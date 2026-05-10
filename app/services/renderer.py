from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from pathlib import Path

from app.models import EditPlan, RenderRequest


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(shlex.quote(x) for x in cmd)}\n{result.stderr[-4000:]}")


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
        concat_file.write_text("".join(f"file '{p}'\n" for p in segment_paths))

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
            str(output),
        ]
        _run(cmd)

    return {
        "engine": "ffmpeg",
        "steps": ["cut", "concat"],
        "segments_rendered": len(plan.selected_scenes),
        "captions_applied": False,
    }
