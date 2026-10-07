from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.ingest import process_upload
from app.storage import store

app = FastAPI(
    title="GeoMeasure API",
    version="1.0.0",
    description="Secure geospatial ingestion and metric measurement service for Shapefile ZIPs and KML.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/files/", status_code=201, tags=["files"])
async def upload_file(file: UploadFile = File(...)):
    try:
        data = await file.read()
        item = process_upload(file.filename or "upload", data)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Unable to process geospatial file: {exc}") from exc

    return {
        "id": item.id,
        "filename": item.filename,
        "file_type": item.file_type,
        "feature_count": item.feature_count,
        "crs": item.crs,
        "measurement_crs": item.measurement_crs,
        "status": item.status,
        "warnings": item.warnings,
    }


@app.get("/api/files/{file_id}/", tags=["files"])
def file_info(file_id: str):
    item = store.get(file_id)
    if item is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {
        "id": item.id,
        "filename": item.filename,
        "file_type": item.file_type,
        "feature_count": item.feature_count,
        "crs": item.crs,
        "measurement_crs": item.measurement_crs,
        "status": item.status,
        "warnings": item.warnings,
    }


@app.get("/api/files/{file_id}/measurements/", tags=["measurements"])
def measurements(file_id: str):
    item = store.get(file_id)
    if item is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {
        "file_id": item.id,
        "measurement_crs": item.measurement_crs,
        "count": len(item.features),
        "features": item.features,
    }


@app.exception_handler(Exception)
async def unhandled_exception_handler(_, exc: Exception):
    # Avoid leaking internal tracebacks while preserving a useful error contract.
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
