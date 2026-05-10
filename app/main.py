from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.models import PlanRequest, RenderRequest, RenderResponse
from app.services.planner import build_plan
from app.services.renderer import render_basic_concat

app = FastAPI(title="viral-editor", version="0.1.0")


@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "viral-editor", "version": "0.1.0"}


@app.post("/plan")
def plan(req: PlanRequest):
    return build_plan(req)


@app.post("/render", response_model=RenderResponse)
def render(req: RenderRequest):
    plan = req.plan or build_plan(PlanRequest(source_video_path=req.source_video_path, analysis=req.analysis, preset=req.preset))

    manifest = {
        "engine": "ffmpeg",
        "steps": ["cut", "concat"],
        "captions_applied": False,
    }

    if req.dry_run:
        return RenderResponse(status="dry_run", output_path=req.output_path, plan=plan, manifest=manifest)

    try:
        manifest = render_basic_concat(req, plan)
        return RenderResponse(status="rendered", output_path=req.output_path, plan=plan, manifest=manifest)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "render_failed", "message": str(exc)})
