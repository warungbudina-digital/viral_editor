# Viral Editor Input/Output Spec

## 1) POST /plan

### Input
```json
{
  "source_video_path": "/data/input/source.mp4",
  "analysis": {
    "video": "source.mp4",
    "bpm": 123.0,
    "subtitle_style": {"speed": "medium", "word_count_avg": 6.1},
    "subtitle_segments": [
      {"text": "Hook text", "start": 0.4, "end": 2.4}
    ],
    "scene_analysis": [
      {
        "start": 0.0,
        "end": 11.9,
        "duration": 11.9,
        "semantic": "youtube talking head",
        "emotion": "neutral face",
        "meme": "reaction meme",
        "motion": 8.3,
        "camera_movement": "fast_move",
        "transition": "cut",
        "beat_sync": true,
        "framing": {"faces": [], "speaker_position": "unknown"},
        "hook_strength": "medium_hook"
      }
    ]
  },
  "preset": {
    "platform": "tiktok",
    "target_aspect_ratio": "9:16",
    "target_duration_sec": 45,
    "max_scenes": 8,
    "prefer_hook_strength": true,
    "prefer_beat_sync": true,
    "allow_reorder": false,
    "caption_mode": "plan_only",
    "add_cta": true,
    "title_text": "",
    "cta_text": "follow untuk part berikutnya"
  }
}
```

### Output
```json
{
  "plan_id": "plan-uuid",
  "source_video_path": "/data/input/source.mp4",
  "selected_scenes": [
    {
      "index": 0,
      "source_start": 0.0,
      "source_end": 11.9,
      "duration": 11.9,
      "score": 8.2,
      "reason": ["hook_strength:medium_hook", "beat_sync", "motion:high"]
    }
  ],
  "estimated_duration_sec": 45.0,
  "subtitle_plan": {
    "mode": "plan_only",
    "segments_used": 20,
    "style_hint": "medium"
  },
  "render_profile": {
    "aspect_ratio": "9:16",
    "platform": "tiktok"
  },
  "warnings": []
}
```

## 2) POST /render

### Input
Boleh kirim input lengkap yang sama seperti `/plan`, atau kirim `plan` hasil endpoint `/plan`.

```json
{
  "source_video_path": "/data/input/source.mp4",
  "analysis": {"...": "..."},
  "preset": {"...": "..."},
  "plan": null,
  "dry_run": true,
  "output_path": "/data/output/rendered.mp4"
}
```

### Output dry-run
```json
{
  "status": "dry_run",
  "output_path": "/data/output/rendered.mp4",
  "plan": {"...": "..."},
  "manifest": {
    "engine": "ffmpeg",
    "steps": ["cut", "concat"],
    "captions_applied": false
  }
}
```

### Output render nyata
```json
{
  "status": "rendered",
  "output_path": "/data/output/rendered.mp4",
  "plan": {"...": "..."},
  "manifest": {
    "engine": "ffmpeg",
    "segments_rendered": 6,
    "captions_applied": false
  }
}
```
