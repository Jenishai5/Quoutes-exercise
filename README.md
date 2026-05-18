# Quotes Exercise

A tiny full-stack quote generator: a Python backend exposes a JSON API, and a static HTML/JS frontend fetches and renders quotes from it. Packaged with Docker Compose so the whole thing comes up with one command, and deployable to Coolify.

## What's inside

```
.
├── backend/
│   ├── server.py        Python stdlib HTTP server (no dependencies)
│   └── Dockerfile
├── frontend/
│   ├── index.html       HTML page + fetch() JS — no hard-coded quotes
│   ├── nginx.conf       Serves the HTML and proxies /api/* to the backend
│   └── Dockerfile
├── docker-compose.yml   Runs both containers together
└── .gitignore
```

## How the pieces connect

The browser only ever talks to **nginx** (the frontend container). When the page calls `fetch("/api/quote")`, nginx forwards that request over Docker's internal network to the **backend** container at `http://backend:8000`. The backend picks a random quote from its in-memory list and returns it as JSON. The backend itself is never exposed to the internet.

```
Browser ──HTTP──> nginx (frontend:80) ──/api/* proxy──> python (backend:8000)
                       └── serves index.html for everything else
```

New quotes added via `POST /api/quote` are written to `quotes.json` inside a Docker volume (`quotes-data`) so they survive container restarts and redeploys.

## Running it locally

You need Docker Desktop. Then:

```bash
docker compose up --build
```

Open http://localhost:8080 in your browser. Click "New quote" to fetch another one.

Useful commands:

```bash
docker compose up -d      # run in the background
docker compose ps         # see what's running
docker compose logs -f    # tail logs from both services
docker compose down       # stop everything
```

## API

| Method | Path           | Description                                  |
|--------|----------------|----------------------------------------------|
| GET    | `/api/quote`   | Returns a random quote as JSON               |
| GET    | `/api/quotes`  | Returns the full list of quotes              |
| POST   | `/api/quote`   | Adds a new quote (body: `{"quote","author"}`) |

Examples:

```bash
# Get a random quote
curl http://localhost:8080/api/quote

# Add a new quote (author is optional)
curl -X POST http://localhost:8080/api/quote \
  -H "Content-Type: application/json" \
  -d '{"quote":"Hello world","author":"Me"}'

# See everything the backend knows about
curl http://localhost:8080/api/quotes
```

## Running the backend without Docker

Useful for quick edits. The backend has no Python dependencies — just stdlib.

```bash
cd backend
python3 server.py
# http://localhost:8000/api/quote
```

Set `QUOTES_FILE` to control where `quotes.json` lives:

```bash
QUOTES_FILE=/tmp/quotes.json python3 server.py
```

## Deploying to Coolify

1. Push this repo to GitHub (or any Git host Coolify can reach).
2. In Coolify, create a new resource → **Docker Compose**.
3. Connect the Git repository and pick the branch. Coolify auto-detects `docker-compose.yml` at the repo root.
4. In the `frontend` service settings, tell Coolify to expose container port `80`. Leave `backend` with no public port — it stays internal.
5. Coolify gives you a `*.your-coolify-domain.com` URL automatically, or you can attach your own domain. HTTPS is handled via Let's Encrypt.
6. Click **Deploy**.

The `quotes-data` volume in `docker-compose.yml` is picked up by Coolify automatically, so curl-added quotes persist across redeploys.

Optional: for cleaner Coolify deploys, you can drop the `ports: - "8080:80"` block on the `frontend` service — Coolify routes traffic through its own reverse proxy and doesn't need a host port mapping. Leaving it in won't break anything.

## Troubleshooting

**`localhost refused to connect`** — the containers aren't running. Check with `docker compose ps`; if empty, run `docker compose up -d`. Make sure you're hitting `http://localhost:8080` (with the port).

**Port 8080 already in use** — something else on your machine is using it. Run `lsof -i :8080` to find the culprit, or change the host port in `docker-compose.yml` (e.g. `"9090:80"`) and use http://localhost:9090.

**Frontend loads but button does nothing** — open the browser dev tools console. 404s on `/api/quote` mean nginx can't reach the backend; check the service name is exactly `backend` in `docker-compose.yml` (nginx looks up `http://backend:8000`).

**Quotes disappear after redeploy** — the `quotes-data` volume isn't mounted properly. Check the volume settings in Coolify for the backend service.
