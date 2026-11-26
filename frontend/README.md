# PneumoScan frontend (Angular 18)

Talks to the FastAPI backend in `../backend`:
- `POST /predict` (multipart field `file`) -> label, confidence, probabilities, Grad-CAM image, Claude explanation
- `GET /health` -> shows server / model / Claude status in the header

## Run
```bash
# 1) backend (from pneumoscan/backend)
uvicorn app.main:app --reload            # http://localhost:8000

# 2) frontend (from pneumoscan/frontend)
npm install
npm start                                # http://localhost:4200
```
API URL: `src/environments/environment.development.ts` (dev) / `environment.ts` (prod build).
The backend's `ALLOWED_ORIGIN` must match the page origin (default `http://localhost:4200`).
