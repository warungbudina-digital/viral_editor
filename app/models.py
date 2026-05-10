from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class SubtitleStyle(BaseModel):
    speed: str = "medium"
    word_count_avg: float | None = None


class SubtitleSegment(BaseModel):
    text: str
    start: float
    end: float


class FramingData(BaseModel):
    faces: list[dict[str, Any]] = Field(default_factory=list)
    speaker_position: str = "unknown"


class SceneAnalysis(BaseModel):
    start: float
    end: float
    duration: float
    semantic: str = "unknown"
    emotion: str = "unknown"
    meme: str = "unknown"
    motion: float = 0.0
    camera_movement: str = "static"
    transition: str = "cut"
    beat_sync: bool = False
    framing: FramingData = Field(default_factory=FramingData)
    hook_strength: str = "weak_hook"


class ViralAnalysis(BaseModel):
    video: str
    bpm: float | None = None
    subtitle_style: SubtitleStyle = Field(default_factory=SubtitleStyle)
    subtitle_segments: list[SubtitleSegment] = Field(default_factory=list)
    scene_analysis: list[SceneAnalysis] = Field(default_factory=list)


class EditPreset(BaseModel):
    platform: str = "tiktok"
    target_aspect_ratio: str = "9:16"
    target_duration_sec: float = 45.0
    max_scenes: int = 8
    prefer_hook_strength: bool = True
    prefer_beat_sync: bool = True
    allow_reorder: bool = False
    caption_mode: Literal["plan_only", "burn_in_later", "none"] = "plan_only"
    add_cta: bool = True
    title_text: str = ""
    cta_text: str = ""


class PlanRequest(BaseModel):
    source_video_path: str
    analysis: ViralAnalysis
    preset: EditPreset = Field(default_factory=EditPreset)


class PlannedScene(BaseModel):
    index: int
    source_start: float
    source_end: float
    duration: float
    score: float
    reason: list[str] = Field(default_factory=list)


class EditPlan(BaseModel):
    plan_id: str
    source_video_path: str
    selected_scenes: list[PlannedScene] = Field(default_factory=list)
    estimated_duration_sec: float = 0.0
    subtitle_plan: dict[str, Any] = Field(default_factory=dict)
    render_profile: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class RenderRequest(BaseModel):
    source_video_path: str
    analysis: ViralAnalysis
    preset: EditPreset = Field(default_factory=EditPreset)
    plan: EditPlan | None = None
    dry_run: bool = True
    output_path: str = "/tmp/viral-editor-output.mp4"


class RenderResponse(BaseModel):
    status: str
    output_path: str
    plan: EditPlan
    manifest: dict[str, Any]
