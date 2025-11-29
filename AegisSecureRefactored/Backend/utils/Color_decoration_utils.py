import os,random
from dotenv import load_dotenv
from database import avatars_col
load_dotenv()

DEFAULT_COLORS = "#F44336,#E91E63,#9C27B0,#673AB7,#3F51B5,#2196F3,#00BCD4,#009688,#4CAF50,#FF9800"
color_env = os.getenv("COLOR_PALETTE", DEFAULT_COLORS)
COLOR_PALETTE = [c.strip() for c in color_env.split(",") if c.strip()]

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
