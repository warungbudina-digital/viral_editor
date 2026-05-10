from __future__ import annotations

import shlex
import subprocess
import tempfile
from pathlib import Path

from app.models import EditPlan, RenderRequest, SubtitleSegment


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(shlex.quote(x) for x in cmd)}\n{result.stderr[-4000:]}"
        )


def _format_srt_time(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours = millis // 3_600_000
    millis %= 3_600_000
    minutes = millis // 60_000
    millis %= 60_000
    secs = millis // 1000
    millis %= 1000
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def _remap_subtitles(req: RenderRequest, plan: EditPlan) -> list[SubtitleSegment]:
    mapped: list[SubtitleSegment] = []
    offset = 0.0

    for scene in plan.selected_scenes:
        for seg in req.analysis.subtitle_segments:
            if seg.end <= scene.source_start or seg.start >= scene.source_end:
                continue

            clipped_start = max(seg.start, scene.source_start)
            clipped_end = min(seg.end, scene.source_end)
            rel_start = offset + (clipped_start - scene.source_start)
            rel_end = offset + (clipped_end - scene.source_start)

            if rel_end <= rel_start:
                continue

            mapped.append(
                SubtitleSegment(
                    text=seg.text,
                    start=round(rel_start, 3),
                    end=round(rel_end, 3),
                )
            )

        offset += scene.duration

    return mapped


def _write_srt(subs: list[SubtitleSegment], path: Path) -> None:
    lines: list[str] = []
    for idx, seg in enumerate(subs, start=1):
        lines.extend(
            [
                str(idx),
                f"{_format_srt_time(seg.start)} --> {_format_srt_time(seg.end)}",
                seg.text,
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def _video_filter(aspect_ratio: str, subtitle_path: Path | None) -> str:
    filters: list[str] = []

    if aspect_ratio == "9:16":
        filters.append("scale=1080:1920:force_original_aspect_ratio=increase")
        filters.append("crop=1080:1920")
    elif aspect_ratio == "1:1":
        filters.append("scale=1080:1080:force_original_aspect_ratio=increase")
        filters.append("crop=1080:1080")

    if subtitle_path is not None:
        sub_path = str(subtitle_path).replace("\\", "/").replace(":", "\\:").replace("'", r"\'")
        filters.append(
            "subtitles='{}':force_style='FontName=Arial,FontSize=18,Outline=1,Shadow=0,Alignment=2,MarginV=40'".format(
                sub_path
            )
        )

    return ",".join(filters)


def render_basic_concat(req: RenderRequest, plan: EditPlan) -> dict:
    source = Path(req.source_video_path)
    if not source.exists():
        raise FileNotFoundError(f"source_video_not_found: {source}")

    output = Path(req.output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="viral-editor-") as tmpdir:
        tmp = Path(tmpdir)
        segment_paths: list[Path] = []

        for i, scene in enumerate(plan.selected_scenes):
            seg = tmp / f"segment_{i:03d}.mp4"
            cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                str(scene.source_start),
                "-to",
                str(scene.source_end),
                "-i",
                str(source),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-c:a",
                "aac",
                str(seg),
            ]
            _run(cmd)
            segment_paths.append(seg)

        concat_file = tmp / "concat.txt"
        concat_file.write_text("".join(f"file '{p}'\n" for p in segment_paths), encoding="utf-8")

        intermediate = tmp / "concat.mp4"
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(intermediate),
        ]
        _run(cmd)

        mapped_subs = _remap_subtitles(req, plan)
        subtitle_path: Path | None = None
        if req.preset.caption_mode != "none" and mapped_subs:
            subtitle_path = tmp / "captions.srt"
            _write_srt(mapped_subs, subtitle_path)

        filter_chain = _video_filter(req.preset.target_aspect_ratio, subtitle_path)
        if filter_chain:
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(intermediate),
                "-vf",
                filter_chain,
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-c:a",
                "aac",
                str(output),
            ]
            _run(cmd)
        else:
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(intermediate),
                "-c",
                "copy",
                str(output),
            ]
            _run(cmd)

    return {
        "engine": "ffmpeg",
        "steps": ["cut", "concat", "crop", "burn_subtitles"],
        "segments_rendered": len(plan.selected_scenes),
        "captions_applied": req.preset.caption_mode != "none",
        "aspect_ratio": req.preset.target_aspect_ratio,
    }
