import math
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ClusterResult
from app.schemas import (
    ClusterRequest, ClusterResponse,
    HeatmapResponse, DistanceResponse, StatsResponse,
)
from app.dependencies import get_current_user_id
from app.config import settings

router = APIRouter()


async def fetch_locations(public_only: bool = True) -> list[dict]:
    """Отримує локації з Locations Service через внутрішню мережу."""
    url = f"{settings.LOCATIONS_SERVICE_URL}/api/locations/geojson/"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Locations Service недоступний")

    geojson = response.json()
    locations = []
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [])
        if len(coords) >= 2:
            locations.append({
                "id": props.get("id"),
                "title": props.get("title", ""),
                "lat": coords[1],
                "lng": coords[0],
                "category": props.get("category"),
            })
    return locations


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /api/analytics/stats
    Статистика по поточному юзеру — запитує дані у Locations Service.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.LOCATIONS_SERVICE_URL}/api/locations/",
                params={"owner": user_id, "page_size": 1000},
                timeout=10.0,
            )
            resp.raise_for_status()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Locations Service недоступний")

    data = resp.json()
    locations = data.get("results", data) if isinstance(data, dict) else data

    total = len(locations)
    public = sum(1 for l in locations if l.get("is_public"))
    private = total - public

    by_category: dict[str, int] = {}
    for loc in locations:
        cat = loc.get("category", {})
        name = cat.get("name") if isinstance(cat, dict) else "Без категорії"
        by_category[name or "Без категорії"] = by_category.get(name or "Без категорії", 0) + 1

    return StatsResponse(
        total_locations=total,
        public_locations=public,
        private_locations=private,
        total_collections=0,
        total_views_received=0,
        most_viewed_location=None,
        locations_by_category=[{"category__name": k, "count": v} for k, v in by_category.items()],
        locations_last_30_days=0,
    )


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    bbox: str | None = Query(None, description="min_lat,min_lng,max_lat,max_lng"),
    category: int | None = Query(None),
):
    """
    GET /api/analytics/heatmap
    Повертає точки для теплової карти Leaflet.heat.
    Публічний ендпоінт — авторизація не потрібна.
    """
    locations = await fetch_locations()

    if bbox:
        try:
            min_lat, min_lng, max_lat, max_lng = map(float, bbox.split(","))
            locations = [
                l for l in locations
                if min_lat <= l["lat"] <= max_lat and min_lng <= l["lng"] <= max_lng
            ]
        except ValueError:
            raise HTTPException(status_code=400, detail="bbox: min_lat,min_lng,max_lat,max_lng")

    if category:
        locations = [
            l for l in locations
            if isinstance(l.get("category"), dict) and l["category"].get("id") == category
        ]

    points = [{"lat": l["lat"], "lng": l["lng"], "weight": 1.0} for l in locations]
    return HeatmapResponse(count=len(points), points=points)


@router.post("/cluster", response_model=ClusterResponse)
async def cluster_locations(
    body: ClusterRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    POST /api/analytics/cluster
    K-Means кластеризація публічних локацій.
    Body: { "n_clusters": 5 }
    """
    try:
        import numpy as np
        from sklearn.cluster import KMeans
    except ImportError:
        raise HTTPException(status_code=500, detail="scikit-learn не встановлений")

    locations = await fetch_locations()
    n = body.n_clusters

    if len(locations) < n:
        raise HTTPException(
            status_code=400,
            detail=f"Недостатньо точок для {n} кластерів. Є лише {len(locations)}.",
        )

    coords = np.array([[l["lng"], l["lat"]] for l in locations])
    kmeans = KMeans(n_clusters=n, random_state=42, n_init=10)
    labels = kmeans.fit_predict(coords)

    clusters = []
    for i in range(n):
        indices = [j for j, lbl in enumerate(labels) if lbl == i]
        center = kmeans.cluster_centers_[i]
        clusters.append({
            "cluster_id": i,
            "center_lat": round(float(center[1]), 6),
            "center_lng": round(float(center[0]), 6),
            "size": len(indices),
            "points": [
                {"id": locations[j]["id"], "title": locations[j]["title"],
                 "lat": locations[j]["lat"], "lng": locations[j]["lng"]}
                for j in indices
            ],
        })

    db.add(ClusterResult(
        user_id=user_id,
        n_clusters=n,
        total_points=len(locations),
        result_json=clusters,
    ))
    await db.commit()

    return ClusterResponse(n_clusters=n, total_points=len(locations), clusters=clusters)


@router.get("/distance", response_model=DistanceResponse)
async def get_distance(
    lat1: float = Query(...),
    lng1: float = Query(...),
    lat2: float = Query(...),
    lng2: float = Query(...),
):
    """
    GET /api/analytics/distance?lat1=...&lng1=...&lat2=...&lng2=...
    Відстань між двома точками по формулі Гаверсинуса (без PostGIS).
    """
    R = 6371000.0  # радіус Землі в метрах

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    distance_m = 2 * R * math.asin(math.sqrt(a))

    return DistanceResponse(
        point_a={"lat": lat1, "lng": lng1},
        point_b={"lat": lat2, "lng": lng2},
        distance_km=round(distance_m / 1000, 4),
        distance_m=round(distance_m, 2),
    )
