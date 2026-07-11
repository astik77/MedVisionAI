# MedVisionAI 🏥

> **Next-generation medical image analysis platform** — Chest X-ray classification powered by CNN and explainable AI (Grad-CAM visualizations).

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, Tailwind CSS, Framer Motion |
| Backend | FastAPI, SQLAlchemy, Alembic |
| ML | TensorFlow (CPU), OpenCV, Grad-CAM |
| Database | PostgreSQL 15 |
| DevOps | Docker, Docker Compose |

## Quick Start

### Prerequisites
- Docker Desktop installed and running

### 1. Clone & configure
```bash
git clone <repo-url>
cd MedVisionAI
cp .env.example .env
# Edit .env and set a strong SECRET_KEY
```

### 2. Build & run
```bash
docker compose up --build
```

| Service | URL |
|---|---|
| React Frontend | http://localhost:5173 |
| FastAPI Backend | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

### 3. Download test images (optional)
```bash
python download_samples.py
```

## Project Structure

```
MedVisionAI/
├── backend/            # FastAPI + ML service
│   ├── app/
│   │   ├── main.py        # Entry point
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routers/       # API route handlers
│   │   ├── ml/            # CNN + Grad-CAM logic
│   │   └── core/          # Auth, config, DB session
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/           # React (Vite) app
│   ├── src/
│   │   ├── pages/         # Login, Register, Dashboard, History
│   │   ├── components/    # Shared UI components
│   │   └── store/         # Auth state management
│   ├── package.json
│   └── Dockerfile
├── test_images/        # Sample chest X-ray images
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## Development Status

| Phase | Status |
|---|---|
| Phase 1: Project Setup & DevOps | ✅ Complete |
| Phase 2: Database & Auth | ⏳ Pending |
| Phase 3: ML & Grad-CAM | ⏳ Pending |
| Phase 4: Core API Endpoints | ⏳ Pending |
| Phase 5: React Frontend | ⏳ Pending |
| Phase 6: Final Integration | ⏳ Pending |
