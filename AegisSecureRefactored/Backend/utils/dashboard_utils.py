import os,re,json
from datetime import datetime, timedelta
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

BOUNDARIES = [0, 26, 51, 76, 101]

async def grouped_data_fromDB(col, user_id_field, score_field, user_id, days: int = None):
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
                "boundaries": BOUNDARIES,
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

async def generate_Cyber_insights() -> dict:
    try:
        prompt = """
        You are a cybersecurity assistant. Output a single JSON object with keys fact1 and fact2.
        Each fact must be a short cybersecurity insight or tip.
        Only output JSON, no explanations, no Markdown.
        Example:
        {"fact1": "Enable MFA to prevent account theft.", "fact2": "Do not click suspicious email links."}
        """
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
        )

        content = ""
        if hasattr(response, "choices") and response.choices:
            msg = getattr(response.choices[0], "message", None)
            if msg:
                content = getattr(msg, "content", "") or getattr(msg, "reasoning", "")

        content = content.strip()
        match = re.search(r"{.*}", content, re.DOTALL)
        if match:
            content = match.group(0)

        try:
            parsed = json.loads(content)
            if "fact1" in parsed and "fact2" in parsed:
                return parsed
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}, content: {content}")

        return {
            "fact1": "*** Unable to fetch cybersecurity insights right now.",
            "fact2": "Please try again later."
        }
    except Exception as e:
        return {"fact1": "","fact2": ""}
