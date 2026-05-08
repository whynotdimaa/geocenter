from sqlalchemy import String, Boolean, Integer, Float, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base


class ClusterResult(Base):
    __tablename__ = "cluster_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    n_clusters: Mapped[int] = mapped_column(Integer)
    total_points: Mapped[int] = mapped_column(Integer)
    result_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ClusterResult user={self.user_id} k={self.n_clusters}>"


class LocationViewLog(Base):
    """Лог переглядів — analytics_service веде свій журнал."""
    __tablename__ = "location_view_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    viewed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
