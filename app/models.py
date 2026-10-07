from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProcessedFile:
    id: str
    filename: str
    file_type: str
    feature_count: int
    crs: str | None
    status: str
    measurement_crs: str | None = None
    features: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
