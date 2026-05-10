# Render Worker Host Deploy

Dokumen ini untuk memasang `viral_editor` pada host render terpisah.

## Asumsi
- repo ini sudah di-clone di host render
- host render dipakai khusus untuk pekerjaan ffmpeg/render
- `n8n-main` dan `n8n-worker` berada di host lain

## File yang dipakai
- `docker-compose.render-worker.yml`
- `.env.render-worker.example`

## Step 1 — siapkan env
```bash
cp .env.render-worker.example .env.render-worker
mkdir -p data/input data/output
```

## Step 2 — build dan jalankan lokal-only
```bash
docker compose --env-file .env.render-worker -f docker-compose.render-worker.yml up -d --build
```

## Step 3 — verifikasi
```bash
docker compose --env-file .env.render-worker -f docker-compose.render-worker.yml ps
curl -sS http://127.0.0.1:9020/healthz
```

## Step 4 — kalau perlu public endpoint via Cloudflared
Isi `TUNNEL_TOKEN` pada `.env.render-worker`, lalu jalankan dengan profile public:

```bash
docker compose --env-file .env.render-worker -f docker-compose.render-worker.yml --profile public up -d
```

## Integrasi dari n8n
Kalau host `n8n-worker` bisa menjangkau host render secara privat, gunakan endpoint privat seperti:
- `http://<render-host-private-ip>:9020/healthz`
- `http://<render-host-private-ip>:9020/plan`
- `http://<render-host-private-ip>:9020/render`

Kalau tidak ada jalur privat, gunakan hostname yang ditunnelkan Cloudflare.

## Catatan operasional
- mulai dengan concurrency render = 1 job
- jangan simpan file media besar terlalu lama; cleanup rutin
- `n8n-main` jangan memanggil render langsung; biarkan `n8n-worker` yang dispatch
