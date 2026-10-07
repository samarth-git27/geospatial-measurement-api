# 🌍 GeoMeasure API

### Geospatial files in. Accurate measurements out.

**GeoMeasure API** is a production-oriented geospatial processing service built with **FastAPI, GeoPandas, Shapely, and PyProj**.

It accepts geospatial datasets such as **KML files** and **ZIP archives containing Shapefiles**, extracts their features, safely handles coordinate reference systems, and calculates physically meaningful measurements such as **polygon area** and **LineString length**.

The core idea is simple:

> **Never measure geographic coordinates as if degrees were meters.**

GeoMeasure automatically transforms geographic data into an appropriate projected coordinate system before calculating measurements.

---

<p align="center">

**UPLOAD → VALIDATE → PARSE → PROJECT → MEASURE → RESPOND**

</p>

---

## ✨ Why GeoMeasure?

Geospatial data looks deceptively simple.

A polygon can be represented by a few coordinate pairs:

```text
(77.5946, 12.9716)
(77.6046, 12.9716)
(77.6046, 12.9816)
(77.5946, 12.9816)
```

But those numbers may represent **longitude and latitude**, not meters.

Calculating area directly from geographic coordinates can therefore produce meaningless results.

GeoMeasure treats **CRS handling as a first-class part of measurement**, rather than an implementation detail.

### Core principles

| Principle | Implementation |
|---|---|
| 🛡️ Safe ingestion | Validates uploads and archive contents |
| 🗺️ CRS-aware | Detects geographic CRS and projects before measurement |
| 📐 Accurate measurements | Area in `m²`, length in `m` |
| 🧩 Feature-centric | Every feature is processed independently |
| 🚫 Graceful degradation | Unsupported geometries don't crash the pipeline |
| 🔍 Observable | Structured status, metadata and warnings |
| 🧪 Testable | Core processing and measurement logic covered by tests |
| 🐳 Portable | Docker-ready development environment |

---

# 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │      API Client      │
                         │ curl / Postman / UI  │
                         └──────────┬───────────┘
                                    │
                                    │ multipart/form-data
                                    ▼
                         ┌──────────────────────┐
                         │      FastAPI         │
                         │   API / Validation   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Upload Validator   │
                         │                      │
                         │ • extension          │
                         │ • size limits        │
                         │ • archive safety     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │      Geospatial Reader       │
                    │                              │
                    │     KML       ZIP/Shapefile  │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │     GeoDataFrame     │
                         │                      │
                         │ geometry + properties│
                         │ CRS + feature index  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     CRS Engine       │
                         │                      │
                         │ Geographic CRS?      │
                         │        │             │
                         │        ▼             │
                         │ Select projected CRS │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │     Measurement Engine     │
                    │                             │
                    │ Polygon    → Area           │
                    │ LineString → Length         │
                    │ Point      → None           │
                    │ Unsupported → Warning       │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │   Measurement API    │
                         │                      │
                         │ metadata + results   │
                         │ warnings + status    │
                         └──────────────────────┘
```

---

# 🔄 Processing Pipeline

GeoMeasure processes every upload through a deterministic pipeline.

```text
              FILE
               │
               ▼
        ┌─────────────┐
        │   Validate  │
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │    Parse    │
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │ Extract CRS │
        └──────┬──────┘
               │
               ▼
       ┌─────────────────┐
       │ Geographic CRS? │
       └───────┬─────────┘
               │
        ┌──────┴──────┐
        │             │
       YES            NO
        │             │
        ▼             │
 ┌──────────────┐     │
 │ Project to   │     │
 │ metric CRS   │     │
 └──────┬───────┘     │
        │             │
        └──────┬──────┘
               ▼
       ┌──────────────┐
       │   Measure    │
       └──────┬───────┘
              │
              ▼
       ┌──────────────┐
       │  Normalize   │
       │    Output    │
       └──────┬───────┘
              │
              ▼
            JSON
```

---

# 📦 Supported Input

GeoMeasure currently accepts:

### KML

```text
survey.kml
```

### Shapefile archive

```text
survey.zip
│
├── survey.shp
├── survey.shx
├── survey.dbf
└── survey.prj
```

The Shapefile components are expected to be supplied together inside the ZIP archive.

---

# 📐 Measurement Model

GeoMeasure currently supports measurement for three major geometry categories.

### Polygon

```text
Polygon
   │
   ▼
Projected geometry
   │
   ▼
Area
   │
   ▼
square meters (m²)
```

### LineString

```text
LineString
     │
     ▼
Projected geometry
     │
     ▼
Length
     │
     ▼
meters (m)
```

### Point

Points are extracted normally, but no measurement is required.

```text
Point
  │
  ▼
No measurement
```

Unsupported geometry types are handled gracefully rather than terminating the complete processing operation.

---

# 🧭 CRS Intelligence

This is one of the most important parts of the project.

Suppose the uploaded dataset uses:

```text
EPSG:4326
```

That CRS represents coordinates as:

```text
longitude / latitude
```

Those values are measured in **degrees**.

GeoMeasure therefore does **not** perform:

```python
geometry.area
```

or:

```python
geometry.length
```

directly on the geographic geometry.

Instead:

```text
EPSG:4326
     │
     │ geographic coordinates
     ▼
CRS selection
     │
     ▼
Projected CRS
     │
     │ metric coordinates
     ▼
Measurement
     │
     ├── Area   → m²
     └── Length → m
```

For geographic datasets, the service selects an appropriate projected coordinate system for measurement.

This prevents the classic geospatial mistake of treating latitude/longitude degrees as physical distance.

---

# 🔌 API

## `POST /api/files/`

Uploads and processes a geospatial file.

### Request

```bash
curl -X POST \
  http://localhost:8000/api/files/ \
  -F "file=@survey.kml"
```

Or:

```bash
curl -X POST \
  http://localhost:8000/api/files/ \
  -F "file=@survey.zip"
```

### Response

```json
{
  "id": "abc123",
  "filename": "survey.kml",
  "feature_count": 120,
  "crs": "EPSG:4326",
  "status": "COMPLETED"
}
```

---

# 🔎 File Information

## `GET /api/files/{id}/`

Returns metadata about a processed file.

Example:

```bash
curl \
  http://localhost:8000/api/files/abc123/
```

Possible information includes:

```text
File ID
Filename
Feature count
Original CRS
Processing status
Warnings
```

---

# 📊 Measurements

## `GET /api/files/{id}/measurements/`

Returns measurement information for the features contained in the uploaded dataset.

Example conceptual response:

```json
{
  "file_id": "abc123",
  "measurement_crs": "EPSG:32643",
  "features": [
    {
      "feature_id": 0,
      "geometry_type": "Polygon",
      "measurement": {
        "type": "area",
        "value": 12051.54,
        "unit": "m²"
      }
    },
    {
      "feature_id": 1,
      "geometry_type": "LineString",
      "measurement": {
        "type": "length",
        "value": 310.52,
        "unit": "m"
      }
    },
    {
      "feature_id": 2,
      "geometry_type": "Point",
      "measurement": null
    }
  ]
}
```

---

# ❤️ Health Check

## `GET /health`

Used to verify that the service is running.

```bash
curl http://localhost:8000/health
```

---

# 🗂️ Project Structure

```text
geospatial-measurement-api/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── ...
│   │
│   ├── services/
│   │   ├── archive.py
│   │   ├── geospatial.py
│   │   ├── measurement.py
│   │   └── ...
│   │
│   ├── models/
│   ├── schemas/
│   └── main.py
│
├── tests/
│   ├── ...
│   └── ...
│
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

The codebase separates:

```text
HTTP Layer
    ↓
Validation
    ↓
Geospatial Processing
    ↓
CRS Transformation
    ↓
Measurement
    ↓
Response Serialization
```

This keeps the API layer thin and makes the processing logic independently testable.

---

# 🛡️ Security & Defensive Processing

Geospatial uploads are untrusted input.

GeoMeasure therefore treats uploaded files as potentially hostile.

### ZIP extraction protections

The archive-processing layer is designed to defend against:

- Path traversal
- Malicious archive members
- Excessive archive expansion
- Oversized uploads
- Unexpected archive contents
- Excessive file counts

Instead of blindly extracting:

```text
../../somewhere/file
```

the service validates the destination before extraction.

### Why this matters

A geospatial API is still an **upload-processing service**.

That means security needs to be considered before geospatial correctness.

---

# 🧪 Testing

The project includes automated tests covering the core behavior.

Run:

```bash
pytest
```

The test suite validates important processing paths including geospatial measurements and CRS-aware behavior.

For development:

```bash
pytest -v
```

---

# 🐳 Run with Docker

Build and start the service:

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

Alternative OpenAPI documentation:

```text
http://localhost:8000/redoc
```

Stop the service:

```bash
docker compose down
```

---

# 💻 Run Locally

## 1. Clone

```bash
git clone https://github.com/samarth-git27/geospatial-measurement-api.git
cd geospatial-measurement-api
```

## 2. Create a virtual environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Start the API

```bash
uvicorn app.main:app --reload
```

---

# 📖 Interactive Documentation

Once the API is running:

### Swagger UI

```text
http://localhost:8000/docs
```

### ReDoc

```text
http://localhost:8000/redoc
```

Swagger makes it possible to upload and test geospatial files directly from the browser.

---

# 🧠 Design Decisions

## Why FastAPI?

FastAPI provides:

- Strong request validation
- Automatic OpenAPI generation
- Excellent developer ergonomics
- Async-ready architecture
- Clear separation between API and processing layers

For a service centered around file processing and API endpoints, it provides a lightweight foundation without unnecessary framework complexity.

---

## Why GeoPandas?

GeoPandas provides a natural abstraction around:

```text
Geometry
+
Attributes
+
CRS
```

This makes it particularly suitable for feature-oriented geospatial processing.

---

## Why Shapely?

Shapely provides the geometry operations required for:

```text
Polygon → area
LineString → length
```

while allowing the application to remain independent of the API transport layer.

---

## Why PyProj?

CRS transformation is delegated to **PyProj**, providing the coordinate-system machinery required to transform geographic data into projected coordinate systems before measurement.

---

# ⚙️ Error Handling Philosophy

A single bad feature should not unnecessarily destroy an entire dataset.

The processing pipeline therefore distinguishes between:

```text
Fatal file-level error
        │
        └── Cannot process dataset

Feature-level issue
        │
        └── Record warning and continue
```

For example:

```text
Feature 0 → Polygon → measured
Feature 1 → LineString → measured
Feature 2 → Point → no measurement
Feature 3 → Unsupported geometry → warning
Feature 4 → Polygon → measured
```

This makes the API much more useful for real-world datasets containing mixed or imperfect geometry.

---

# 🚀 Performance Considerations

The architecture is intentionally designed so processing can evolve independently from the HTTP layer.

Potential future improvements include:

```text
Current
   │
   ├── Synchronous processing
   │
   ▼
Future
   │
   ├── Background jobs
   ├── Task queue
   ├── Streaming uploads
   ├── Persistent metadata store
   ├── Object storage
   ├── Distributed workers
   └── Result caching
```

This allows the API to scale from a small engineering service into a larger geospatial processing platform.

---

# 🔮 Future Scope

GeoMeasure is intentionally designed as a foundation rather than a dead-end assignment implementation.

Potential extensions include:

### More geometry measurements

```text
Polygon
├── Area
├── Perimeter
└── Centroid

LineString
├── Length
└── Segment statistics

Point
├── Coordinate extraction
└── Spatial metadata
```

### More formats

```text
GeoJSON
GeoPackage
GeoTIFF metadata
GPX
CSV + coordinates
```

### Advanced geospatial operations

```text
Spatial indexing
Bounding boxes
Buffering
Intersection
Union
Nearest-neighbor queries
Spatial joins
Topology validation
```

### Platform capabilities

```text
Async processing
Job IDs
Progress tracking
Object storage
Persistent database
Authentication
Rate limiting
Observability
Metrics
Distributed workers
```

---

# 🧩 Current vs Future Architecture

```text
                    ┌──────────────────┐
                    │      Client      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │     FastAPI      │
                    └────────┬─────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Geospatial Processor │
                  └──────────┬───────────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
             Reader        CRS        Measurement
                │            │            │
                └────────────┼────────────┘
                             ▼
                         Response


             ───────────── FUTURE ─────────────

                    ┌──────────────────┐
                    │      Client      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    API Gateway   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    Job Service   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    Task Queue    │
                    └────────┬─────────┘
                             │
                  ┌──────────┼──────────┐
                  ▼          ▼          ▼
               Worker     Worker     Worker
                  │          │          │
                  └──────────┼──────────┘
                             ▼
                     Object Storage
                             │
                             ▼
                        Result API
```

---

# 📋 API Contract

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Service health |
| `POST` | `/api/files/` | Upload and process file |
| `GET` | `/api/files/{id}/` | Retrieve file information |
| `GET` | `/api/files/{id}/measurements/` | Retrieve measurements |

---

# 🧭 Engineering Philosophy

GeoMeasure follows a few principles:

### 1. Correctness before convenience

A measurement that looks plausible but is calculated in the wrong CRS is worse than an explicit error.

### 2. Treat uploaded data as untrusted

Every file enters through validation and defensive processing.

### 3. Keep responsibilities isolated

The API shouldn't know how polygon area is calculated.

The measurement engine shouldn't know anything about HTTP.

### 4. Fail gracefully

A problematic feature should not automatically invalidate every valid feature around it.

### 5. Design for evolution

The initial implementation remains intentionally small, while the architecture leaves room for asynchronous processing, persistence, distributed workers, and additional geospatial operations.

---

# 📚 Learning & Takeaways

This project explores the intersection of:

- Backend API engineering
- Geospatial data processing
- Coordinate reference systems
- Computational geometry
- Secure file handling
- Python service architecture
- Automated testing
- Containerized deployment

The most important lesson is that **geospatial correctness is not simply a geometry problem — it is also a coordinate-system problem.**

---

# 🤝 Contributing

Contributions are welcome.

A typical development workflow:

```bash
git checkout -b feature/my-feature

# make changes

pytest

git add .
git commit -m "Add my feature"

git push origin feature/my-feature
```

Then open a pull request.

---

# 📄 License

Add the project's chosen open-source license here before publishing broadly.

---

# 👨‍💻 Author

**Samarth**

Graduate Engineer · Backend / AI / Systems Engineering

GitHub:

[github.com/samarth-git27](https://github.com/samarth-git27?utm_source=chatgpt.com)

---

<p align="center">

### 🌍 GeoMeasure API

**Turning raw geospatial files into trustworthy measurements.**

</p>
