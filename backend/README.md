# MedVisionAI — Backend

## Running locally (without Docker)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env  # edit values
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for the Swagger UI.
