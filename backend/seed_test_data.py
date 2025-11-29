
import asyncio
from app.config import settings
from supabase import create_client

# The Dev Mock User ID we set in middleware.py
USER_ID = "557c3ac3-e6a9-4b2b-95eb-b7f57961024b"

async def seed_data():
    if not settings.supabase_service_role_key:
        print("ERROR: SUPABASE_SERVICE_ROLE_KEY is missing")
        return

    supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
    print(f"Seeding data for user {USER_ID}...")

    # 1. Clear existing data for this user to ensure clean state
    print("Clearing existing chats and folders...")
    supabase.table("chats").delete().eq("user_id", USER_ID).execute()
    supabase.table("folders").delete().eq("user_id", USER_ID).execute()

    # 2. Create Folders
    folders = ["CS 101", "MATH 202"]
    folder_map = {}
    
    for name in folders:
        data = {"user_id": USER_ID, "name": name}
        res = supabase.table("folders").insert(data).execute()
        folder_id = res.data[0]['id']
        folder_map[name] = folder_id
        print(f"Created folder: {name} ({folder_id})")

    # 3. Create Chats
    # Some in folders, some root
    chats = [
        {"title": "Linear Algebra Review", "folder": None}, # Expected to be starred in tests (we can't force star yet)
        {"title": "Spanish Practice", "folder": None},
        {"title": "Essay Brainstorming", "folder": None},
        {"title": "React Components", "folder": None},
        {"title": "Physics Lab Report", "folder": None},
    ]

    for chat in chats:
        data = {
            "user_id": USER_ID, 
            "title": chat["title"],
            "folder_id": folder_map.get(chat["folder"]) if chat["folder"] else None
        }
        res = supabase.table("chats").insert(data).execute()
        print(f"Created chat: {chat['title']} ({res.data[0]['id']})")

    print("Seeding complete!")

if __name__ == "__main__":
    print("Starting seed script...")
    asyncio.run(seed_data())
