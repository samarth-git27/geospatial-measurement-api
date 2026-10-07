from __future__ import annotations

from typing import Any

import geopandas as gpd
from pyproj import CRS
from shapely.geometry import GeometryCollection

SUPPORTED = {"Point", "LineString", "LinearRing", "Polygon", "MultiLineString", "MultiPolygon"}


def crs_label(crs: Any) -> str | None:
    if crs is None:
        return None
    try:
        return CRS.from_user_input(crs).to_string()
    except Exception:
        return str(crs)


def choose_measurement_crs(gdf: gpd.GeoDataFrame) -> CRS | None:
    """Select a metric projected CRS suitable for the dataset's extent.

    For geographic/projected input, GeoPandas' estimate_utm_crs is a robust default
    for local-to-regional data. For datasets where UTM cannot be estimated, fall back
    to World Mercator (EPSG:3395), which provides metric units and predictable behavior.
    """
    if gdf.crs is None:
        return None
    source = CRS.from_user_input(gdf.crs)
    if source.is_projected:
        return source
    try:
        estimated = gdf.estimate_utm_crs()
        if estimated:
            return CRS.from_user_input(estimated)
    except Exception:
        pass
    return CRS.from_epsg(3395)


def _safe_properties(row: Any) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    for key, value in row.items():
        if key == "geometry":
            continue
        if hasattr(value, "item"):
            try:
                value = value.item()
            except Exception:
                pass
        if value is None or isinstance(value, (str, int, float, bool)):
            properties[str(key)] = value
        else:
            properties[str(key)] = str(value)
    return properties


def _measurement(geometry: Any) -> tuple[float | None, str | None]:
    if geometry is None or geometry.is_empty:
        return None, None
    geom_type = geometry.geom_type
    if geom_type in {"LineString", "LinearRing", "MultiLineString"}:
        return float(geometry.length), "meters"
    if geom_type in {"Polygon", "MultiPolygon"}:
        return float(geometry.area), "square_meters"
    if geom_type == "GeometryCollection":
        # Collections are not assigned a single semantic measurement because their
        # components may mix dimensions.
        return None, None
    return None, None


def process_geodataframe(gdf: gpd.GeoDataFrame, max_features: int) -> tuple[list[dict[str, Any]], str | None, list[str]]:
    if len(gdf) > max_features:
        raise ValueError(f"Feature count {len(gdf)} exceeds configured limit of {max_features}")

    source_crs = crs_label(gdf.crs)
    measurement_crs = choose_measurement_crs(gdf)
    projected = None
    warnings: list[str] = []

    if measurement_crs is not None:
        try:
            projected = gdf.to_crs(measurement_crs)
        except Exception as exc:
            warnings.append(f"Measurement projection failed: {exc}")
    elif len(gdf):
        warnings.append("Input has no CRS; measurements cannot be guaranteed to use metric units.")

    features: list[dict[str, Any]] = []
    for idx, row in gdf.iterrows():
        geometry = row.geometry
        projected_geometry = projected.loc[idx].geometry if projected is not None else None
        measurement, unit = _measurement(projected_geometry)
        geom_type = geometry.geom_type if geometry is not None else None
        feature_warnings: list[str] = []
        if geom_type not in SUPPORTED and geom_type is not None:
            feature_warnings.append(f"Measurement not supported for geometry type '{geom_type}'")
        if geometry is not None and not geometry.is_valid and geom_type in {"Polygon", "MultiPolygon"}:
            feature_warnings.append("Geometry is invalid; area may be unreliable")

        features.append({
            "id": idx.item() if hasattr(idx, "item") else idx,
            "geometry_type": geom_type,
            "geometry": geometry.__geo_interface__ if geometry is not None else None,
            "crs": source_crs,
            "properties": _safe_properties(row),
            "measurement": measurement,
            "measurement_unit": unit,
            "measurement_crs": measurement_crs.to_string() if measurement_crs else None,
            "warnings": feature_warnings,
        })
    return features, measurement_crs.to_string() if measurement_crs else None, warnings
