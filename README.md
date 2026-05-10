# viral-editor-v1

FastAPI tool container untuk membangun ulang / re-cut video viral berbasis:
- source video
- output JSON dari `viral_analyzer`
- preset editing

## Status

V1 ini adalah scaffold yang sudah bisa:
- menerima analyzer JSON
- membangun edit plan heuristik
- menjalankan dry-run render
- mencoba render clip dasar via ffmpeg concat
- burn-in subtitle dasar dari analyzer JSON
- crop dasar ke 9:16 / 1:1 via ffmpeg

Belum fokus ke:
- caption burn-in penuh
- face-aware cropping presisi
- overlay engine kompleks
- B-roll auto placement

## Endpoint

- `GET /healthz`
- `POST /plan`
- `POST /render`

## Jalankan lokal

```bash
docker build -t viral-editor:v1 .
docker run --rm -p 9020:9020 \
  -v $(pwd)/examples:/data/examples \
  viral-editor:v1
```

Lalu buka:
- `http://127.0.0.1:9020/docs`

## Catatan runtime

Agar `render` bekerja, `source_video_path` harus mengarah ke file yang benar-benar bisa diakses di dalam container.


## Deploy sebagai service tool untuk n8n

Repo ini sekarang juga punya `docker-compose.example.yml` agar bisa dipasang sebagai service tool terpisah yang hidup di network Docker yang sama dengan `n8n-main` dan `n8n-worker`.

Contoh internal URL dari n8n:
- `http://viral_editor:9020/healthz`
- `http://viral_editor:9020/plan`
- `http://viral_editor:9020/render`
