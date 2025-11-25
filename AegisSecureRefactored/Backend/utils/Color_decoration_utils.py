import os,random
from dotenv import load_dotenv
from database import avatars_col
load_dotenv()

COLOR_PALETTE = os.getenv("COLOR_PALETTE", "").split(",")

async def get_sender_avatar_color(sender: str):
    existing = await avatars_col.find_one({"email": sender})
    if existing and "char_color" in existing:
        return existing["char_color"]

    random_color = random.choice(COLOR_PALETTE)
    await avatars_col.update_one(
        {"email": sender},
        {"$set": {"char_color": random_color}},
        upsert=True
    )
    return random_color