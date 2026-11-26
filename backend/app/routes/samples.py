"""Browse and serve the local dataset (backend/data/chest_xray) to the frontend.
GET /samples?split=test&label=NORMAL&offset=0&limit=24  -> paged list of images
GET /samples/image?path=test/NORMAL/IM-0001.jpeg        -> the image file
GET /samples/image?path=...&thumb=true                  -> small JPEG thumbnail
"""
import io
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response
from PIL import Image, UnidentifiedImageError

from app.config import CLASS_NAMES, DATA_DIR

router = APIRouter(prefix="/samples", tags=["samples"])

SPLITS = ("train", "val", "test")
EXTENSIONS = {".jpg", ".jpeg", ".png"}
THUMB_SIZE = 220


def _files(split: str, label: str) -> list[Path]:
    folder = Path(DATA_DIR) / split / label
    if not folder.is_dir():
        return []
    return sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in EXTENSIONS and not p.name.startswith(".")
    )


def _resolve(rel_path: str) -> Path:
    """Map 'split/LABEL/file' to a real file, refusing anything outside DATA_DIR."""
    base = Path(DATA_DIR).resolve()
    target = (base / rel_path).resolve()
    if base not in target.parents or target.suffix.lower() not in EXTENSIONS or not target.is_file():
        raise HTTPException(404, "Image not found.")
    return target


@router.get("")
def list_samples(
    split: str = Query("test"),
    label: str = Query("NORMAL"),
    offset: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=100),
):
    if split not in SPLITS:
        raise HTTPException(400, f"split must be one of {list(SPLITS)}")
    if label not in CLASS_NAMES:
        raise HTTPException(400, f"label must be one of {CLASS_NAMES}")
    files = _files(split, label)
    page = files[offset: offset + limit]
    return {
        "split": split,
        "label": label,
        "total": len(files),
        "offset": offset,
        "items": [{"path": f"{split}/{label}/{p.name}", "name": p.name} for p in page],
    }


@router.get("/image")
def sample_image(path: str = Query(...), thumb: bool = Query(False)):
    target = _resolve(path)
    if not thumb:
        return FileResponse(target)
    try:
        with Image.open(target) as im:
            im = im.convert("RGB")
            im.thumbnail((THUMB_SIZE, THUMB_SIZE))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=80)
    except (UnidentifiedImageError, OSError):
        raise HTTPException(415, "Could not read that image.")
    return Response(buf.getvalue(), media_type="image/jpeg",
                    headers={"Cache-Control": "public, max-age=3600"})
