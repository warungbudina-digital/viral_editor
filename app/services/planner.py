from __future__ import annotations

import uuid
from app.models import EditPlan, PlanRequest, PlannedScene


HOOK_SCORE = {
    "strong_hook": 5.0,
    "medium_hook": 3.0,
    "weak_hook": 1.0,
}


def scene_score(scene, prefer_hook_strength: bool, prefer_beat_sync: bool) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    hook = HOOK_SCORE.get(scene.hook_strength, 0.0)
    if prefer_hook_strength:
        score += hook
        if hook:
            reasons.append(f"hook_strength:{scene.hook_strength}")

    if prefer_beat_sync and scene.beat_sync:
        score += 1.5
        reasons.append("beat_sync")

    motion_bonus = min(scene.motion / 4.0, 2.0)
    if motion_bonus > 0:
        score += motion_bonus
        reasons.append("motion:high" if motion_bonus >= 1.0 else "motion:low")

    if scene.semantic in {"youtube talking head", "person talking", "reaction face"}:
        score += 1.0
        reasons.append(f"semantic:{scene.semantic}")

    if scene.duration <= 2.5:
        score += 0.8
        reasons.append("short_scene_bonus")
    elif scene.duration >= 15:
        score -= 1.5
        reasons.append("long_scene_penalty")

    return score, reasons


def build_plan(req: PlanRequest) -> EditPlan:
    ranked: list[tuple[int, float, list[str]]] = []

    for idx, scene in enumerate(req.analysis.scene_analysis):
        score, reasons = scene_score(scene, req.preset.prefer_hook_strength, req.preset.prefer_beat_sync)
        ranked.append((idx, score, reasons))

    ranked.sort(key=lambda x: x[1], reverse=True)
    selected_ranked = ranked[: req.preset.max_scenes]

    if not req.preset.allow_reorder:
        selected_ranked.sort(key=lambda x: req.analysis.scene_analysis[x[0]].start)

    selected: list[PlannedScene] = []
    total = 0.0
    for idx, score, reasons in selected_ranked:
        scene = req.analysis.scene_analysis[idx]
        selected.append(
            PlannedScene(
                index=idx,
                source_start=scene.start,
                source_end=scene.end,
                duration=scene.duration,
                score=round(score, 3),
                reason=reasons,
            )
        )
        total += scene.duration

    warnings: list[str] = []
    if not selected:
        warnings.append("no_scene_selected")
    if total > req.preset.target_duration_sec * 1.5:
        warnings.append("estimated_duration_above_target")

    return EditPlan(
        plan_id=f"plan-{uuid.uuid4().hex[:12]}",
        source_video_path=req.source_video_path,
        selected_scenes=selected,
        estimated_duration_sec=round(total, 3),
        subtitle_plan={
            "mode": req.preset.caption_mode,
            "segments_used": len(req.analysis.subtitle_segments),
            "style_hint": req.analysis.subtitle_style.speed,
        },
        render_profile={
            "aspect_ratio": req.preset.target_aspect_ratio,
            "platform": req.preset.platform,
            "target_duration_sec": req.preset.target_duration_sec,
        },
        warnings=warnings,
    )
