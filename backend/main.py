"""
Luminate AI Course Marshal - FastAPI Backend
Main entry point for the agentic tutoring platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


from app.config import settings
from app.api.middleware import require_auth
from app.api.routes import chat, admin, execute, mastery, history, models

app = FastAPI(
    title="Luminate AI Course Tutor",
    description="Agentic AI tutoring platform for COMP 237",
    version="0.0.1"
)

# Include routers
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(execute.router)
app.include_router(mastery.router)
app.include_router(history.router)
app.include_router(models.router)

# CORS middleware for Chrome Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://localhost:*"],  # Will be updated with actual extension ID
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "Luminate AI Course Marshal API",
            "environment": settings.environment
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(
        content={
            "message": "Luminate AI Course Marshal API",
            "version": "0.0.1"
        }
    )


@app.get("/api/auth/me")
async def get_current_user(user_info: dict = require_auth):
    """Get current authenticated user info"""
    return JSONResponse(
        content={
            "user_id": user_info["user_id"],
            "email": user_info["email"],
            "role": user_info["role"],
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
