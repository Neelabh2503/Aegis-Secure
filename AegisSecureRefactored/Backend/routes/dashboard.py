import os,re,json
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query


from datetime import datetime, timedelta
from routes.auth import get_current_user
from database import messages_col, sms_messages_col
from utils.dashboard_utils import grouped_data_fromDB,generate_Cyber_insights


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

LABELS = ["Secure", "Suspicious", "Threat", "Critical"]


@router.get("")
@router.get("/")
async def get_dashboard(
    mode: str = Query("both", regex="^(sms|mail|both)$"),
    days: int = Query(None, ge=1),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    sms_counts, mail_counts = {}, {}
    if mode in ("sms", "both"):
        sms_counts = await grouped_data_fromDB(
            sms_messages_col, "user_id", "spam_score", user_id, days
        )
    if mode in ("mail", "both"):
        mail_counts = await grouped_data_fromDB(
            messages_col, "user_id", "spam_prediction", user_id, days
        )

    if mode == "both":
        combined_counts = {i: sms_counts.get(i, 0) + mail_counts.get(i, 0) for i in range(len(LABELS))}
        counts_to_send = combined_counts
    elif mode == "sms":
        counts_to_send = sms_counts
    elif mode == "mail":
        counts_to_send = mail_counts

    for i in range(len(LABELS)):
        counts_to_send.setdefault(i, 0)

    insights = await generate_Cyber_insights()
    return {
        "labels": LABELS,
        "values": [counts_to_send[i] for i in range(len(LABELS))],
        "total": sum(counts_to_send.values()),
        "insights": insights
    }