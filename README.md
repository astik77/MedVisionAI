# MedVisionAI 🩺

> **AI-powered medical image analysis platform** — Chest X-ray classification with CNN + Grad-CAM explainability.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-FF6F00?logo=tensorflow)](https://tensorflow.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docs.docker.com/compose/)

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Browser :5173                     │
│            React + Vite + Framer Motion             │
│   Login → Dashboard (Scanner) → History             │
└────────────────────┬────────────────────────────────┘
                     │  HTTP / REST (JWT Bearer)
                     ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend :8000                   │
│  /api/auth  /api/predict  /api/history  /health     │
│  ┌─────────────┐   ┌───────────────────────────┐   │
│  │   JWT Auth  │   │ MedicalModelScanner (CNN)  │   │
│  └─────────────┘   │  + Grad-CAM explainability │   │
│                    └───────────────────────────┘   │
└────────────────────┬────────────────────────────────┘
                     │  SQLAlchemy ORM
                     ▼
┌─────────────────────────────────────────────────────┐
│           PostgreSQL :5432  (pgdata volume)          │
│   Tables: users, prediction_history                  │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git

### 1 — Clone & configure

```powershell
git clone https://github.com/<your-org>/MedVisionAI.git
cd MedVisionAI

# Copy env template and set your values
cp .env.example .env
# Edit .env — at minimum change SECRET_KEY to a long random string
```

### 2 — Start the stack

```powershell
docker compose up --build
```

> First build downloads base images and installs Python/Node packages — allow 3–5 minutes.

### 3 — Open the app

| Service  | URL                         |
|----------|-----------------------------|
| Frontend | http://localhost:5173       |
| API docs | http://localhost:8000/docs  |
| Health   | http://localhost:8000/health|

### 4 — Stop

```powershell
docker compose down          # stop containers, keep data volumes
docker compose down -v       # stop + delete all data (clean slate)
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `medvision` | PostgreSQL username |
| `POSTGRES_PASSWORD` | _(required)_ | PostgreSQL password |
| `POSTGRES_DB` | `medvisiondb` | Database name |
| `DATABASE_URL` | _(required)_ | Full SQLAlchemy connection URL |
| `SECRET_KEY` | _(change me!)_ | JWT signing secret — use a 32+ char random string |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT lifetime in minutes |
| `BACKEND_CORS_ORIGINS` | `http://localhost:5173,...` | Comma-separated allowed CORS origins |
| `UPLOAD_DIR` | `/app/uploads` | Path inside the backend container for image uploads |
| `VITE_API_URL` | `http://localhost:8000` | API base URL used by the React frontend |
| `ENVIRONMENT` | `development` | `development` or `production` |

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/register` | No | Create a new account |
| `POST` | `/api/auth/login` | No | Login, returns JWT |
| `GET`  | `/api/auth/me` | Bearer | Get current user profile |
| `POST` | `/api/predict` | Bearer | Upload image → CNN prediction + Grad-CAM |
| `GET`  | `/api/predict/{id}` | Bearer | Get one prediction by ID |
| `GET`  | `/api/history` | Bearer | Paginated scan history |
| `DELETE` | `/api/history/{id}` | Bearer | Delete a prediction record |
| `GET`  | `/health` | No | Service liveness + DB ping |
| `GET`  | `/docs` | No | Swagger interactive API docs |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Framer Motion, Lucide React |
| Backend | FastAPI, SQLAlchemy 2, Pydantic v2, Python-Jose JWT |
| ML | TensorFlow 2 (CPU), NumPy, OpenCV, Grad-CAM |
| Database | PostgreSQL 15 |
| DevOps | Docker, Docker Compose |

---

## Development Workflow

```powershell
# Install backend deps locally (optional — for IDE support)
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Install frontend deps locally
cd ..\frontend
npm install

# Hot-reload dev (via Docker — recommended)
docker compose up
```

Files in `./backend` and `./frontend` are bind-mounted into the containers,
so any local edits hot-reload without rebuilding.

---

## Sample Test Images

```powershell
# Download sample chest X-rays for testing
python download_samples.py
```

Images are saved to `./test_images/`.

---

## License

MIT — see [LICENSE](LICENSE) for details.
