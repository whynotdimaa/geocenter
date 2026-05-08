from pydantic import BaseModel, Field


class ClusterRequest(BaseModel):
    n_clusters: int = Field(default=5, ge=2, le=20, description="Кількість кластерів (2-20)")


class ClusterPoint(BaseModel):
    id: int
    title: str
    lat: float
    lng: float


class ClusterItem(BaseModel):
    cluster_id: int
    center_lat: float
    center_lng: float
    size: int
    points: list[ClusterPoint]


class ClusterResponse(BaseModel):
    n_clusters: int
    total_points: int
    clusters: list[ClusterItem]


class HeatmapPoint(BaseModel):
    lat: float
    lng: float
    weight: float


class HeatmapResponse(BaseModel):
    count: int
    points: list[HeatmapPoint]


class DistanceResponse(BaseModel):
    point_a: dict
    point_b: dict
    distance_km: float
    distance_m: float


class StatsResponse(BaseModel):
    total_locations: int
    public_locations: int
    private_locations: int
    total_collections: int
    total_views_received: int
    most_viewed_location: dict | None
    locations_by_category: list[dict]
    locations_last_30_days: int
