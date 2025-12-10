"""
Media Routes - Serve course images and media files

Provides API endpoints to serve images from the raw course data.
Images are referenced by their path in the images.json file.
"""

import logging
import mimetypes
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response
import base64

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/media", tags=["media"])

# Base path for raw course data
RAW_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "course-data" / "ExportFile_COMP237"


def resolve_image_path(image_path: str) -> Optional[Path]:
    """
    Resolve an image path from images.json to an actual file path.
    
    Args:
        image_path: Path like "csfiles/home_dir/__xid-1693031_1.png"
        
    Returns:
        Resolved Path object or None if not found
    """
    # Try direct path first
    full_path = RAW_DATA_DIR / image_path
    if full_path.exists() and full_path.is_file():
        return full_path
    
    # Try without extension (some files don't have extension in folder name)
    path_without_ext = full_path.with_suffix("")
    if path_without_ext.exists() and path_without_ext.is_dir():
        # Look for PNG file inside the folder
        for ext in [".png", ".jpg", ".jpeg", ".gif"]:
            img_file = path_without_ext / f"{path_without_ext.name}{ext}"
            if img_file.exists():
                return img_file
    
    # Try looking for the file directly in home_dir with just the xid
    if "__xid-" in image_path:
        xid = image_path.split("/")[-1]  # Get just the filename
        home_dir = RAW_DATA_DIR / "csfiles" / "home_dir"
        
        # Check direct file
        direct_file = home_dir / xid
        if direct_file.exists() and direct_file.is_file():
            return direct_file
        
        # Check folder with same name containing PNG
        if direct_file.exists() and direct_file.is_dir():
            for f in direct_file.iterdir():
                if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif"]:
                    return f
        
        # Check without .png extension (folder name)
        xid_base = xid.replace(".png", "").replace(".jpg", "").replace(".jpeg", "").replace(".gif", "")
        folder_path = home_dir / xid_base
        if folder_path.exists() and folder_path.is_dir():
            for f in folder_path.iterdir():
                if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif"]:
                    return f
    
    return None


@router.get("/image/{image_path:path}")
async def get_image(image_path: str):
    """
    Serve a course image by its path.
    
    Args:
        image_path: Image path from images.json (e.g., "csfiles/home_dir/__xid-1693031_1.png")
        
    Returns:
        Image file or 404 if not found
    """
    resolved_path = resolve_image_path(image_path)
    
    if not resolved_path:
        logger.warning(f"Image not found: {image_path}")
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(str(resolved_path))
    if not content_type:
        content_type = "image/png"  # Default to PNG
    
    logger.debug(f"Serving image: {resolved_path}")
    
    return FileResponse(
        path=resolved_path,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=86400",  # Cache for 1 day
        }
    )


@router.get("/image-base64/{image_path:path}")
async def get_image_base64(image_path: str):
    """
    Get a course image as base64 data URL.
    Useful for embedding in markdown or when direct file serving isn't available.
    
    Args:
        image_path: Image path from images.json
        
    Returns:
        JSON with base64 data URL
    """
    resolved_path = resolve_image_path(image_path)
    
    if not resolved_path:
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
    
    # Read and encode
    with open(resolved_path, "rb") as f:
        image_data = f.read()
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(str(resolved_path))
    if not content_type:
        content_type = "image/png"
    
    base64_data = base64.b64encode(image_data).decode("utf-8")
    data_url = f"data:{content_type};base64,{base64_data}"
    
    return {
        "path": image_path,
        "data_url": data_url,
        "content_type": content_type,
        "size_bytes": len(image_data),
    }
