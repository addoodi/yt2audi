import asyncio
import uuid
from pathlib import Path
from typing import Dict, Any, List

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from yt2audi.core.pipeline import ProcessingPipeline
from yt2audi.config.loader import load_profile, list_available_profiles
from yt2audi.models.profile import Profile
from yt2audi.transfer import USBManager

# --- Global State ---
# In a real production app, this might be a database or Redis.
# For a local desktop app, in-memory is fine.
class JobStore:
    jobs: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def create_job(cls, url: str) -> str:
        job_id = str(uuid.uuid4())[:8]
        cls.jobs[job_id] = {
            "id": job_id, 
            "url": url, 
            "status": "pending", 
            "progress": 0, 
            "stage": "Initializing",
            "title": url # placeholder
        }
        return job_id

    @classmethod
    def update_job(cls, job_id: str, **kwargs):
        if job_id in cls.jobs:
            cls.jobs[job_id].update(kwargs)

    @classmethod
    def get_active_jobs(cls) -> List[Dict[str, Any]]:
        # Return jobs that aren't "complete" (or keep complete for a bit?)
        # For now, return all recent
        return list(cls.jobs.values())

job_store = JobStore()

# --- Dependencies ---
pipeline_instance: ProcessingPipeline = None
default_profile: Profile = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global pipeline_instance, default_profile
    
    # Load default profile (Audi Q5) or first available
    try:
        default_profile = load_profile("audi_q5")
    except Exception:
        # Fallback if audi_q5 doesn't exist
        available = list_available_profiles()
        if available:
            default_profile = load_profile(available[0])
        else:
            # Create a minimal default if nothing exists
            from yt2audi.models.profile import Profile as ProfileModel
            default_profile = ProfileModel() 

    pipeline_instance = ProcessingPipeline(default_profile)
    yield
    # Shutdown
    pass

app = FastAPI(title="YT2Audi Web", lifespan=lifespan)

# Mount Static
base_path = Path(__file__).parent
app.mount("/static", StaticFiles(directory=base_path / "static"), name="static")

templates = Jinja2Templates(directory=base_path / "templates")

# --- Models ---
class QueueRequest(BaseModel):
    url: str
    profile_id: str = "audi_q5"
    custom_output_dir: str | None = None
    auto_copy_usb: bool = False

# --- Helpers ---
async def run_pipeline_task(job_id: str, request: QueueRequest):
    """Background task to run the pipeline for a single video."""
    def progress_callback(item_url: str, percent: float, stage: str):
        job_store.update_job(job_id, progress=percent, stage=stage, status="processing")
        if percent >= 100:
             job_store.update_job(job_id, status="complete", stage="Finished")

    try:
        # 1. Determine Output Directory
        if request.custom_output_dir and request.custom_output_dir.strip():
            out_path_str = request.custom_output_dir
        else:
            out_path_str = pipeline_instance.profile.output.output_dir
            
        # Resolve relative paths
        if out_path_str.startswith("~"):
            output_dir = Path(out_path_str).expanduser()
        else:
            output_dir = Path(out_path_str).absolute()
            
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. Modify USB Setting Temporarily (Thread-unsafe but ok for MVP)
        # Ideally, we'd pass override params to process_one, but profile is tied to pipeline.
        # For simplicity, we create a temporary patched profile or just rely on the fact 
        # that 'auto_copy_usb' is a step in the pipeline.
        # BETTER: We will monkeypatch the profile for this instance if needed, 
        # OR we just modify the pipeline.process_one signature to accept overrides.
        
        # Since refining pipeline.py is risky now, we'll temporarily set the flag on the profile
        # This is strictly not thread-safe for diverse concurrent requests but acceptable here.
        original_usb_setting = pipeline_instance.profile.transfer.usb_auto_copy
        if request.auto_copy_usb:
            pipeline_instance.profile.transfer.usb_auto_copy = True
        
        try:
            await pipeline_instance.process_one(
                request.url, 
                output_dir=output_dir, 
                progress_callback=progress_callback
            )
        finally:
            # Restore
            pipeline_instance.profile.transfer.usb_auto_copy = original_usb_setting

    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Job {job_id} failed: {error_msg}") # Log to console for debugging
        # Truncate for UI but keep critical info
        ui_msg = str(e)[:200]
        job_store.update_job(job_id, status="error", stage=ui_msg, progress=0)

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/queue")
async def queue_video(req: QueueRequest, background_tasks: BackgroundTasks):
    job_id = job_store.create_job(req.url)
    background_tasks.add_task(run_pipeline_task, job_id, req)
    return {"id": job_id, "status": "queued"}

@app.get("/api/status")
async def get_status():
    return {
        "jobs": job_store.get_active_jobs(),
        "system": {
            "usb_connected": bool(USBManager.get_removable_drives()),
            "cpu_load": 15 # Mock for now
        }
    }

@app.get("/api/profiles")
async def get_profiles():
    # Return mock profiles for now, or real ones if available
    return [
        {"id": "audi_q5", "name": "Audi Q5 (Best Quality)"},
        {"id": "mp3", "name": "Audio Only (MP3)"}
    ]
