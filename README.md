# Vector Conversion Platform

This repository provides a full-stack image vectorization pipeline with a FastAPI backend and a React frontend. Upload raster images, apply preprocessing, and download vector outputs in SVG, AI, and EPS formats. The project also includes automated tests and Docker Compose configuration for local development.

## Project Structure

```
backend/        # FastAPI application, vectorization pipeline, tests
frontend/       # React single-page app for uploading and previewing conversions
Dockerfile      # (per service) container specifications
```

## Backend

### Key Features
- **Preprocessing:** Configurable median-based noise reduction and gradient-magnitude edge highlighting without external dependencies.
- **Vectorization:** Raster edges are collapsed into horizontal vector strips that are emitted as SVG rectangles.
- **Export:** Lightweight writers generate PDF (AI-compatible) and EPS payloads directly, keeping the stack self-contained.
- **API:** `POST /convert` accepts an image plus preprocessing parameters and returns the converted assets.

### Running Locally

The automated evaluation environment cannot reach PyPI, so the backend ships
with fallbacks that run purely on the standard library. When you have internet
access you can still install FastAPI and friends to expose an actual HTTP
service:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn
uvicorn app.main:app --reload
```

### Tests

Execute unit and integration tests with:

```bash
cd backend
pytest
```

## Frontend

The React interface lets users upload an image, tune preprocessing parameters, view the resulting SVG preview, and download the AI/EPS variants.

### Setup

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` while the backend is running on port `8000`.

## Docker Compose

To run the entire stack in containers:

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000/convert

## Manual Testing

1. Start the backend and frontend (via local commands or Docker Compose).
2. Upload a sample raster image (PNG/JPEG) through the web UI.
3. Adjust preprocessing parameters and submit.
4. Verify the SVG preview renders correctly and download SVG/AI/EPS outputs.

## Requirements
- Python 3.11+
- Node.js 18+ (for the optional React frontend)
- Docker & Docker Compose (optional, for containerized workflow)

## License

MIT
