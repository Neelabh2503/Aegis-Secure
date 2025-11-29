import hashlib
from bson import ObjectId
from datetime import datetime

def convert_doc(doc):
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    if isinstance(doc, dict):
        return {k: convert_doc(v) for k, v in doc.items()}
    if isinstance(doc, list):
        return [convert_doc(i) for i in doc]
    return doc

def generate_message_hash(address: str, body: str, date_ms: int):
    text = f"{address}-{body}-{date_ms}"
    return hashlib.sha256(text.encode()).hexdigest()
