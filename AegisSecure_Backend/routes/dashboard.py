import os
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from .auth import get_current_user
from database import messages_col, sms_messages_col
from typing import Dict, Any
from groq import Groq

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# Labels and bucket boundaries
LABELS = ["Secure", "Suspicious", "Threat", "Critical"]
BUCKET_BOUNDS = [0, 26, 51, 76, 101]

# Static Cybersecurity Trends
CYBER_TRENDS = [
    "Beware of SMS phishing links claiming lottery wins",
    "Do not open emails from unknown senders with attachments",
    "Enable Multi-factor Authentication (MFA)",
    "Recent phishing campaigns mimic banking institutions"
]


def _format_response(counts: Dict[int, int], summary: str = "", trends: list = []) -> Dict[str, Any]:
    """Return response in consistent label order, with summary and trends."""
    values = [counts.get(i, 0) for i in range(len(LABELS))]
    return {
        "labels": LABELS,
        "values": values,
        "total": sum(values),
        "summary": summary,
        "trends": trends
    }


async def _aggregate_collection_by_buckets(col, user_id_field, score_field, user_id, days: int = None):
    """Aggregate a single collection into the 4 score buckets for a user."""
    match_stage = {"$match": {user_id_field: user_id}}
    if days is not None:
        since_ms = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
        match_stage["$match"].update({
            "$or": [
                {"timestamp": {"$gte": since_ms}},
                {"created_at": {"$gte": datetime.utcnow() - timedelta(days=days)}}
            ]
        })

    pipeline = [
        match_stage,
        {
            "$project": {
                "score": {
                    "$convert": {
                        "input": f"${score_field}",
                        "to": "double",
                        "onError": 0.0,
                        "onNull": 0.0
                    }
                }
            }
        },
        {"$match": {"score": {"$gte": 0, "$lte": 100}}},
        {
            "$bucket": {
                "groupBy": "$score",
                "boundaries": BUCKET_BOUNDS,
                "default": "other",
                "output": {"count": {"$sum": 1}}
            }
        }
    ]

    cursor = col.aggregate(pipeline)
    counts = {}
    idx_map = {0: 0, 26: 1, 51: 2, 76: 3}

    async for doc in cursor:
        b = doc.get("_id")
        if isinstance(b, (int, float)):
            b_key = None
            for boundary in sorted(idx_map.keys(), reverse=True):
                if b >= boundary:
                    b_key = boundary
                    break
            if b_key is not None:
                counts[idx_map[b_key]] = counts.get(idx_map[b_key], 0) + doc.get("count", 0)

    return counts


async def generate_summary_ai(total_counts: dict) -> str:
    """Generate AI summary via Groq. Falls back if Groq API fails."""
    try:
        prompt = f"""
        The user has the following message risk counts: {total_counts}.
        Write a brief summary (2–3 sentences) in simple language highlighting how many messages are safe vs risky
        and give a short tip about staying safe from scams.
        """

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠ Groq AI summary failed: {e}")
        return "Summary unavailable due to AI service error."


@router.get("")
@router.get("/")
async def get_dashboard(
    mode: str = Query("both", regex="^(sms|mail|both)$"),
    days: int = Query(None, ge=1),
    current_user: dict = Depends(get_current_user),
):
    """Fetch dashboard data with counts, AI summary, and cybersecurity trends related to Scam and phising attempts."""
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    total_counts = {}

    # SMS data
    if mode in ("sms", "both"):
        sms_counts = await _aggregate_collection_by_buckets(
            sms_messages_col, "user_id", "spam_score", user_id, days
        )
        for k, v in sms_counts.items():
            total_counts[k] = total_counts.get(k, 0) + v

    # Mail data
    if mode in ("mail", "both"):
        mail_counts = await _aggregate_collection_by_buckets(
            messages_col, "user_id", "spam_prediction", user_id, days
        )
        for k, v in mail_counts.items():
            total_counts[k] = total_counts.get(k, 0) + v

    # AI-generated summary
    summary = await generate_summary_ai(total_counts)
    print("SUMMARY FROM AI: ");
    print(summary);
    # Return response including trends
    response = _format_response(total_counts, summary=summary, trends=CYBER_TRENDS)
    return response