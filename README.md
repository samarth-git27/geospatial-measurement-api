# GeoMeasure API

A production-oriented FastAPI service that ingests KML files or ZIP archives containing ESRI Shapefiles, extracts feature metadata, and calculates metric measurements without performing area/length calculations directly on latitude/longitude degrees.

## Why this implementation is different

The brief permits architectural decisions beyond the minimum. GeoMeasure uses that freedom to make the API safer and more explicit:

- **Automatic measurement CRS**: geographic input is transformed into an estimated UTM CRS when possible, with a metric fallback.
- **Measurement provenance**: every measured feature records the CRS used for the calculation.
- **Graceful unsupported geometry handling**: points and unsupported collections are returned with `measurement: null` and warnings instead of crashing the request.
- **Secure ZIP ingestion**: member-count, expansion-size, and path-traversal protections are applied before extractions.
- **Resource limits**: upload size and feature count are configurable.
- **API-first design**: OpenAPI documentation is generated automatically by FastAPI.
- **Stateless processing boundary**: the current storage adapter is intentionally isolated so it can be replaced by Postgres/S3/Redis without changing the API contract.

## Requirements

Python 3.11+ or Docker.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for Swagger UI.

## Docker

```bash
docker compose up --build
```

## API

### Health

`GET /health`

```json
{"status":"ok"}
```

### Upload

`POST /api/files/`

Multipart field: `file`.

Supported inputs:
- `.kml`
- `.zip` containing an ESRI Shapefile (`.shp`, with its companion files)

Example:

```bash
curl -X POST http://localhost:8000/api/files/ \\
  -F "file=@survey.kml"
```

Response:

```json
{
  "id": "...",
  "filename": "survey.kml",
  "file_type": "kml",
  "feature_count": 120,
  "crs": "EPSG:4326",
  "measurement_crs": "EPSG:32643",
  "status": "COMPLETED",
  "warnings": []
}
```

### File information

`GET /api/files/{id}/`

Returns the processing metadata and status.

### Measurements

`GET /api/files/{id}/measurements/`

Each feature includes its ID, geometry type, geometry, source CRS, properties, measurement, measurement unit, calculation CRS, and warnings.

Example feature shape:

```json
{
  "id": 0,
  "geometry_type": "Polygon",
  "geometry": {"type": "Polygon", "coordinates": []},
  "crs": "EPSG:4326",
  "properties": {"name": "Parcel A"},
  "measurement": 1842.31,
  "measurement_unit": "square_meters",
  "measurement_crs": "EPSG:32643",
  "warnings": []
}
```

## Architecture

```text
Client
  |
  v
FastAPI route
  |
  +--> validation + resource limits
  |
  +--> secure ZIP extraction (if needed)
  |
  +--> GeoPandas / GDAL ingestion
  |
  +--> CRS analysis
  |      |
  |      +--> projected input: use source CRS
  |      +--> geographic input: estimate UTM
  |      +--> fallback: EPSG:3395
  |
  +--> feature normalization + measurements
  |
  +--> storage adapter
  |
  v
JSON API
```

## CRS strategy

The brief explicitly requires that geographic coordinates not be measured directly in degrees. GeoMeasure therefore selects a projected metric CRS before calculating area or length. For geographic datasets, `estimate_utm_crs()` is preferred because UTM is generally appropriate for local/regional survey data. If that estimate cannot be produced, EPSG:3395 is used as a metric fallback. The selected CRS is exposed in the API so measurement provenance is visible.

For very large, cross-zone, polar, or geodesic workloads, a future version should support an explicit CRS strategy supplied by the caller.

## Measurement rules

- Polygon / MultiPolygon -> area in square meters.
- LineString / LinearRing / MultiLineString -> length in meters.
- Point -> no measurement required; returns `null`.
- Unsupported/mixed geometry -> request remains successful; the feature contains a warning and `null` measurement.

## Design decisions

### FastAPI over Django
The service is API-first, has a compact domain, and benefits from FastAPI's type-driven validation and generated OpenAPI contract.

### GeoPandas + GDAL
This combination provides mature support for KML and Shapefile formats and interoperates directly with pyproj and Shapely.

### In-memory repository
The assignment focuses on ingestion and measurement rather than persistence. The repository is isolated behind `app/storage.py` so persistent storage can be introduced without rewriting the processing layer.

### Security-first ZIP handling
Zip archives are an untrusted input boundary. The implementation checks archive size, expanded size, member count, and path traversal before extraction.

## Testing

```bash
pytest
```

The baseline suite covers health behavior, not-found semantics, and file-type validation. A production deployment should extend this with fixture-based KML/Shapefile tests, CRS accuracy tests, malformed archives, oversized inputs, invalid geometries, and property serialization edge cases.

## Learning

This project demonstrates practical geospatial backend engineering: OGC-style geometry handling, GDAL-backed ingestion, CRS transformations, metric computation, API design, and secure file processing.

## Future scope

- PostgreSQL/PostGIS persistence.
- Object storage for original uploads.
- Background jobs for large datasets.
- Pagination/streaming for very large feature collections.
- Explicit measurement CRS selection by request.
- Geodesic measurement mode for global-scale geometries.
- GeoJSON download/export.
- Authentication, rate limiting, audit logs, and observability.
- Kubernetes deployment and horizontal workers.
