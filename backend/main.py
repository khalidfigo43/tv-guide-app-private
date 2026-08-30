from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, Path as FPath, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.database_service import tv_service

app = FastAPI(
    title="TV Guide Online API",
    description="Production API for Arabic & International TV Channels Schedule and Movie Library",
    version="1.0.0"
)

# CORS middleware for Web & Android App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Web Frontend
web_dir = Path("web")
if web_dir.exists():
    app.mount("/static", StaticFiles(directory="web"), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        from fastapi.responses import FileResponse
        return FileResponse("web/index.html")



# =============================================================================
# API SCHEMAS
# =============================================================================
class FavoriteToggleRequest(BaseModel):
    content_id: Optional[int] = None
    channel_id: Optional[int] = None


# =============================================================================
# CHANNELS ENDPOINTS
# =============================================================================
@app.get("/api/channels", summary="List all TV channels with frequencies")
def list_channels():
    channels = tv_service.get_channels()
    return {"channels": channels, "count": len(channels)}


@app.get("/api/channels/{channel_id}", summary="Get channel details and frequencies")
def get_channel(channel_id: int = FPath(..., description="Channel ID")):
    channel = tv_service.get_channel_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@app.get("/api/channels/{channel_id}/schedule", summary="Get channel broadcast schedule")
def get_channel_schedule(
    channel_id: int = FPath(..., description="Channel ID"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    channel = tv_service.get_channel_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    schedule = tv_service.get_channel_schedule(channel_id, date)
    return {
        "channel": channel,
        "date": date,
        "schedule": schedule,
        "count": len(schedule)
    }


# =============================================================================
# NOW & NEXT AIRING ENDPOINTS
# =============================================================================
@app.get("/api/now", summary="Get currently airing programs across all channels")
def get_now_airing(
    time: Optional[str] = Query(None, description="ISO timestamp override, e.g. 2026-08-28T20:30:00")
):
    ref_time = datetime.fromisoformat(time) if time else None
    airing = tv_service.get_now_airing(ref_time)
    return {
        "now_airing": airing,
        "count": len(airing)
    }


@app.get("/api/next", summary="Get next upcoming programs across all channels")
def get_next_airing(
    time: Optional[str] = Query(None, description="ISO timestamp override, e.g. 2026-08-28T20:30:00")
):
    ref_time = datetime.fromisoformat(time) if time else None
    next_airing = tv_service.get_next_airing(ref_time)
    return {
        "next_airing": next_airing,
        "count": len(next_airing)
    }


# =============================================================================
# MOVIES & CONTENT LIBRARY
# =============================================================================
@app.get("/api/movies", summary="Browse dynamic visual content library from live channel schedules")
def list_movies(
    page: int = Query(1, ge=1),
    limit: int = Query(36, ge=1, le=100),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    type: Optional[str] = Query(None, description="Filter by content type: 'all', 'movies', 'series', 'documentary'")
):
    return tv_service.get_movies(page=page, limit=limit, genre=genre, content_type=type)


@app.get("/api/content/{content_id}", summary="Get movie/content details with grouped broadcasts")
def get_content_details(content_id: int = FPath(..., description="Canonical Content ID")):
    details = tv_service.get_content_details(content_id)
    if not details:
        raise HTTPException(status_code=404, detail="Content not found")
    return details


# =============================================================================
# SEARCH ENDPOINT
# =============================================================================
@app.get("/api/search", summary="Search movies, series, and programs in Arabic and English")
def search_content(
    q: str = Query(..., min_length=1, description="Search query in Arabic or English"),
    type: Optional[str] = Query(None, description="Filter by 'movie', 'series', 'program'")
):
    results = tv_service.search(query=q, content_type=type)
    return {
        "query": q,
        "results": results,
        "count": len(results)
    }


# =============================================================================
# REMINDERS & NOTIFICATIONS ENDPOINTS
# =============================================================================
class ReminderCreateRequest(BaseModel):
    user_id: Optional[str] = "anonymous"
    broadcast_id: Optional[str] = None
    content_id: Optional[int] = None
    title: str
    channel_name: str
    channel_logo: Optional[str] = None
    start_datetime: str
    remind_1hour: bool = True
    remind_10min: bool = True


@app.post("/api/reminders", summary="Create a broadcast reminder for a movie or show")
def create_reminder(req: ReminderCreateRequest):
    data = req.dict()
    saved = tv_service.add_reminder(data)
    return {"status": "success", "reminder": saved}


@app.get("/api/reminders", summary="List active broadcast reminders")
def list_reminders(user_id: Optional[str] = Query(None)):
    reminders = tv_service.get_reminders(user_id=user_id)
    return {"reminders": reminders, "count": len(reminders)}


@app.delete("/api/reminders/{reminder_id}", summary="Delete a broadcast reminder")
def remove_reminder(reminder_id: str = FPath(...)):
    deleted = tv_service.delete_reminder(reminder_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "success", "message": "Reminder deleted"}


# =============================================================================
# HEALTH & CONFIG
# =============================================================================
@app.get("/api/health", summary="Health check endpoint")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "channels_count": len(tv_service.get_channels())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
