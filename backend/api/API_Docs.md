# Flask API Documentation

Base URL: `http://<host>:<port>` (default port `5000`)

- Requests: `application/json` unless noted; file upload uses `multipart/form-data`
- Responses: `application/json`

---

## GET `/health`

**What it does**

- Returns service health status.

**Request**

- No body.

**Response (200)**

```json
{
  "status": "ok",
  "service": "flask-api"
}
```

**Error responses**

- None

---

## POST `/publish`

**What it does**

- Accepts two images for a session, creates a processing job, and enforces one active job per session via a session lock.

**Request** (`multipart/form-data`)

- `sessionId`: string (required)
- `image1`: file (required)
- `image2`: file (required)

**Response (200)**

```json
{
  "status": "processing",
  "jobId": "c1f7d2b8-...-..."
}
```

**Error responses**

- 400
  - `{"error": "Missing sessionId"}`
  - `{"error": "Missing image1 or image2"}`
  - `{"error": "Failed to create job dir: <reason>"}`
  - `{"error": "Failed to save files: <reason>"}`
  - `{"error": "DB error: <reason>"}`
- 429
  - `{"error": "Previous job still processing"}`
- 500
  - `{"error": "Failed to publish job: <reason>"}`

**Notes**

- Uploaded files are stored temporarily at `/tmp/<jobId>/`.
- A session-level lock prevents concurrent jobs per session.

---

## GET `/status/{jobId}`

**What it does**

- Returns the processing status of a job and, when completed, the result image URL.

**Path params**

- `jobId`: string (required)

**Request**

- No body.

**Response (200 - processing)**

```json
{ "status": "processing" }
```

**Response (200 - completed)**

```json
{ "status": "completed", "image_url": "https://..." }
```

**Error responses**

- 404
  - `{"status": "not_found"}`

---

## POST `/update_status`

**What it does**

- INTERNAL: Called by the worker to mark a job as completed, update the result URL, and release the session lock.

**Request** (`application/json`)

```json
{
  "jobId": "c1f7d2b8-...-...",
  "resultUrl": "https://..."
}
```

**Response (200)**

```json
{ "status": "updated" }
```

**Error responses**

- 400
  - `{"error": "Missing jobId or resultUrl"}`
- 404
  - `{"error": "Job not found"}`
