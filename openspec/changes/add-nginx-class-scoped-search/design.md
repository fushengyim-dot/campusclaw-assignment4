# Design

- Compose exposes only NGINX on `WEB_PORT`; the Flask API has no host port mapping.
- NGINX proxies `/`, `/health`, and `/api/` to the internal `api:8080` service.
- `GET /api/knowledge/search?q=...` returns HTTP 401 without a login session.
- The API obtains `class_id` from the server-side session and filters both `knowledge_entries` and `materials` by that value.
- Results include `material_id`, title, source filename, and stored content. The current implementation uses bounded SQLite `LIKE` matching.
- Seed passwords are supplied through environment variables and are never hardcoded in application source.
