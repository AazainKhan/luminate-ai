"""
Chat History and Folder Management API routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime

from app.api.middleware import require_auth
from supabase import create_client, Client
from app.config import settings

router = APIRouter(prefix="/api/history", tags=["history"])
logger = logging.getLogger(__name__)

# Supabase client
supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """Get Supabase client for database operations"""
    global supabase_client
    if supabase_client is None:
        if not settings.supabase_service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY not configured")
        supabase_client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return supabase_client

# Models
class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None

class ChatCreate(BaseModel):
    title: str
    folder_id: Optional[str] = None

class ChatUpdate(BaseModel):
    title: Optional[str] = None
    folder_id: Optional[str] = None

# Routes

@router.get("/folders")
async def get_folders(user_info: dict = Depends(require_auth)):
    """Get all folders for the user"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("folders").select("*").eq("user_id", user_info["user_id"]).is_("deleted_at", "null").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching folders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/folders")
async def create_folder(folder: FolderCreate, user_info: dict = Depends(require_auth)):
    """Create a new folder"""
    try:
        supabase = get_supabase_client()
        data = {
            "user_id": user_info["user_id"],
            "name": folder.name,
            "parent_id": folder.parent_id
        }
        response = supabase.table("folders").insert(data).execute()
        return response.data[0]
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: str, user_info: dict = Depends(require_auth)):
    """Soft delete a folder"""
    try:
        supabase = get_supabase_client()
        # Verify ownership
        check = supabase.table("folders").select("id").eq("id", folder_id).eq("user_id", user_info["user_id"]).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Folder not found")
            
        # Soft delete
        response = supabase.table("folders").update({"deleted_at": datetime.utcnow().isoformat()}).eq("id", folder_id).execute()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chats")
async def get_chats(folder_id: Optional[str] = None, user_info: dict = Depends(require_auth)):
    """Get chats, optionally filtered by folder"""
    try:
        supabase = get_supabase_client()
        query = supabase.table("chats").select("*").eq("user_id", user_info["user_id"]).is_("deleted_at", "null")
        if folder_id:
            query = query.eq("folder_id", folder_id)
        
        response = query.order("updated_at", desc=True).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chats")
async def create_chat(chat: ChatCreate, user_info: dict = Depends(require_auth)):
    """Create a new chat"""
    try:
        supabase = get_supabase_client()
        data = {
            "user_id": user_info["user_id"],
            "title": chat.title,
            "folder_id": chat.folder_id
        }
        response = supabase.table("chats").insert(data).execute()
        return response.data[0]
    except Exception as e:
        logger.error(f"Error creating chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str, user_info: dict = Depends(require_auth)):
    """Soft delete a chat"""
    try:
        supabase = get_supabase_client()
        # Verify ownership
        check = supabase.table("chats").select("id").eq("id", chat_id).eq("user_id", user_info["user_id"]).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Chat not found")
            
        # Soft delete
        response = supabase.table("chats").update({"deleted_at": datetime.utcnow().isoformat()}).eq("id", chat_id).execute()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/{chat_id}")
async def get_messages(chat_id: str, user_info: dict = Depends(require_auth)):
    """Get messages for a chat"""
    try:
        supabase = get_supabase_client()
        # Verify ownership via chat
        chat_check = supabase.table("chats").select("id").eq("id", chat_id).eq("user_id", user_info["user_id"]).execute()
        if not chat_check.data:
            raise HTTPException(status_code=404, detail="Chat not found")
            
        response = supabase.table("messages").select("*").eq("chat_id", chat_id).order("created_at", desc=False).execute()
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/folders/{folder_id}")
async def update_folder(folder_id: str, folder: FolderUpdate, user_info: dict = Depends(require_auth)):
    """Update a folder (rename or move)"""
    try:
        supabase = get_supabase_client()
        # Verify ownership
        check = supabase.table("folders").select("id").eq("id", folder_id).eq("user_id", user_info["user_id"]).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Folder not found")
            
        data = {}
        if folder.name is not None:
            data["name"] = folder.name
        if folder.parent_id is not None:
            data["parent_id"] = folder.parent_id
            
        if not data:
            return check.data[0] # No changes
            
        response = supabase.table("folders").update(data).eq("id", folder_id).execute()
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/chats/{chat_id}")
async def update_chat(chat_id: str, chat: ChatUpdate, user_info: dict = Depends(require_auth)):
    """Update a chat (rename or move)"""
    try:
        supabase = get_supabase_client()
        # Verify ownership
        check = supabase.table("chats").select("id").eq("id", chat_id).eq("user_id", user_info["user_id"]).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Chat not found")
            
        data = {}
        if chat.title is not None:
            data["title"] = chat.title
        if chat.folder_id is not None:
            data["folder_id"] = chat.folder_id
            
        if not data:
            return check.data[0] # No changes
            
        response = supabase.table("chats").update(data).eq("id", chat_id).execute()
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trash")
async def get_trash(user_info: dict = Depends(require_auth)):
    """Get all deleted items (folders and chats)"""
    try:
        supabase = get_supabase_client()
        
        # Fetch deleted folders
        folders = supabase.table("folders").select("*").eq("user_id", user_info["user_id"]).not_.is_("deleted_at", "null").order("deleted_at", desc=True).execute()
        
        # Fetch deleted chats
        chats = supabase.table("chats").select("*").eq("user_id", user_info["user_id"]).not_.is_("deleted_at", "null").order("deleted_at", desc=True).execute()
        
        return {
            "folders": folders.data,
            "chats": chats.data
        }
    except Exception as e:
        logger.error(f"Error fetching trash: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trash/restore/{type}/{id}")
async def restore_item(type: str, id: str, user_info: dict = Depends(require_auth)):
    """Restore a deleted item"""
    try:
        if type not in ["folder", "chat"]:
            raise HTTPException(status_code=400, detail="Invalid type")
            
        table = "folders" if type == "folder" else "chats"
        supabase = get_supabase_client()
        
        # Verify ownership
        check = supabase.table(table).select("id").eq("id", id).eq("user_id", user_info["user_id"]).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Item not found")
            
        # Restore
        response = supabase.table(table).update({"deleted_at": None}).eq("id", id).execute()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/trash/{type}/{id}")
async def permanent_delete_item(type: str, id: str, user_info: dict = Depends(require_auth)):
    """Permanently delete an item"""
    try:
        if type not in ["folder", "chat"]:
            raise HTTPException(status_code=400, detail="Invalid type")
            
        table = "folders" if type == "folder" else "chats"
        supabase = get_supabase_client()
        
        # Verify ownership
        check = supabase.table(table).select("id").eq("id", id).eq("user_id", user_info["user_id"]).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Item not found")
            
        # Hard delete
        response = supabase.table(table).delete().eq("id", id).execute()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error permanently deleting item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

