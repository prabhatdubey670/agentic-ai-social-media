from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
import sys
import os
from typing import List, Optional
from pydantic import BaseModel

# Adjust path to find root modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.database import Database
from orchestrator.main import Supervisor
from workers.content_creator import ContentCreator
from workers.market_analyst import MarketAnalyst
from platforms.x_platform import XPlatform
from platforms.linkedin_platform import LinkedInPlatform
from llm_router import LLMRouter
from config import TARGET_TOPICS, AGENT_IDENTITY

app = FastAPI(title="Quanteve AI Social Media Manager API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
llm = LLMRouter()
creator = ContentCreator(llm, db)
analyst = MarketAnalyst(llm, db)

# Pydantic models for response data
class PostDraft(BaseModel):
    id: str
    platform: str
    content_type: str
    topic: str
    content_text: str
    status: str
    created_at: str

@app.get("/")
async def root():
    return {"status": "online", "message": "Quanteve AI Agent API is running"}

@app.get("/api/dashboard")
async def get_dashboard():
    """Fetch all analytics data for the dashboard"""
    return {
        "daily_stats": db.get_daily_stats(7),
        "topic_performance": db.get_topic_performance(),
        "success_rates": db.get_action_success_rate(),
        "recent_strategies": db.get_strategy_log(5),
        "top_content": db.get_best_content(limit=5),
        "identity": AGENT_IDENTITY,
        "db_status": "Absolute Path Verified"
    }

@app.get("/api/profile")
async def get_profile():
    """Fetch live social media profile metrics"""
    x_platform = XPlatform(None, db, dry_run=True)
    metrics = await x_platform.get_profile_metrics()
    
    return {
        "x": metrics,
        "linkedin": {"followers": "N/A", "connections": "N/A"} 
    }

@app.get("/api/queue", response_model=List[PostDraft])
async def get_queue(status: str = "draft"):
    """Get content queue items"""
    rows = db.get_queued_content(status=status)
    return [
        PostDraft(
            id=r[0], platform=r[1], content_type=r[2], topic=r[3],
            content_text=r[4], status=r[5], created_at=r[8]
        ) for r in rows
    ]

@app.post("/api/queue/{item_id}/approve")
async def approve_item(item_id: str):
    """Approve a queued item for posting"""
    db.approve_content(item_id)
    return {"status": "success", "message": f"Item {item_id} approved"}

@app.get("/api/published")
async def get_published():
    """Get recently published posts"""
    return db.get_published_posts(limit=20)

class GenerateRequest(BaseModel):
    topic: str
    platform: str

@app.post("/api/generate")
async def generate_instant(req: GenerateRequest):
    """Generate content on-demand for a topic"""
    if req.platform.lower() == "x.com":
        draft = await run_in_threadpool(creator.generate_x_post, req.topic)
    else:
        draft = await run_in_threadpool(creator.generate_linkedin_post, req.topic)
    return {"draft": draft.get("post_text", ""), "topic": req.topic, "platform": req.platform}

class PublishRequest(BaseModel):
    text: str
    platform: str

@app.post("/api/publish")
async def publish_instant(req: PublishRequest):
    """Publish content immediately to a platform"""
    if req.platform.lower() == "x.com":
        platform = XPlatform(None, db, dry_run=False)
    else:
        platform = LinkedInPlatform(None, db, dry_run=False)
    
    success = await platform.post_content(req.text)
    if success:
        db.save_published_post(req.platform, req.text, "instant-manual", "post", "manual-ui")
        db.update_daily_stats(req.platform, "posts_published")
    
    return {"status": "success" if success else "failed"}

@app.get("/api/world-update")
async def get_world_update():
    """Fetch 5-point summary of world technical trends"""
    summary = await run_in_threadpool(analyst.get_world_summary)
    return {"summary": summary}

@app.get("/api/peers/suggest")
async def get_suggested_peers():
    """AI suggests 10 peers to follow/monitor"""
    peers = await run_in_threadpool(analyst.suggest_peers)
    return {"peers": peers}

class PeerRequest(BaseModel):
    handle: str
    platform: str
    url: Optional[str] = ""
    niche: Optional[str] = "research"

@app.post("/api/peers")
async def add_peer(req: PeerRequest):
    """Manually add a peer to track"""
    db.save_top_performer(
        platform=req.platform, author=req.handle, handle=req.handle,
        url=req.url, niche=req.niche, followers=0, avg_engagement=0,
        why_valuable="Manually added via UI"
    )
    return {"status": "success"}

@app.post("/api/agent/run")
async def run_agent(mode: str, background_tasks: BackgroundTasks):
    """Trigger an agent run in the background"""
    if mode not in ["post", "engage", "full"]:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    # Run supervisor in background
    supervisor = Supervisor(mode=mode, dry_run=False)
    background_tasks.add_task(supervisor.run)
    
    return {"status": "started", "mode": mode}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
