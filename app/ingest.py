from __future__ import annotations

import io
import os
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd

from app.config import settings
from app.geo import process_geodataframe
from app.storage import store

ALLOWED = {".kml", ".zip"}


def _safe_zip_extract(data: bytes, destination: Path) -> Path:
    if len(data) > settings.max_archive_bytes:
        raise ValueError("Archive exceeds the configured size limit")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        infos = zf.infolist()
        if len(infos) > settings.max_archive_members:
            raise ValueError("Archive contains too many members")
        total_uncompressed = sum(info.file_size for info in infos)
        if total_uncompressed > settings.max_archive_bytes:
            raise ValueError("Archive expands beyond the configured size limit")
        for info in infos:
            member = Path(info.filename)
            if member.is_absolute() or ".." in member.parts:
                raise ValueError("Archive contains an unsafe path")
        zf.extractall(destination)

    shapefiles = list(destination.rglob("*.shp"))
    if not shapefiles:
        raise ValueError("ZIP archive does not contain a Shapefile (.shp)")
    return shapefiles[0]


def process_upload(filename: str, data: bytes):
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED:
        raise ValueError("Unsupported file type. Upload a .kml or .zip Shapefile archive")
    if len(data) > settings.max_upload_bytes:
        raise ValueError("Uploaded file exceeds the configured size limit")

    with tempfile.TemporaryDirectory(prefix="geo-measure-") as tmp:
        root = Path(tmp)
        if suffix == ".zip":
            source = _safe_zip_extract(data, root)
            file_type = "shapefile"
            gdf = gpd.read_file(source)
        else:
            source = root / filename
            source.write_bytes(data)
            file_type = "kml"
            gdf = gpd.read_file(source, driver="KML")

        features, measurement_crs, warnings = process_geodataframe(gdf, settings.max_features)
        return store.create(
            filename=filename,
            file_type=file_type,
            feature_count=len(features),
            crs=features[0]["crs"] if features else (str(gdf.crs) if gdf.crs else None),
            status="COMPLETED",
            measurement_crs=measurement_crs,
            features=features,
            warnings=warnings,
        )
