"""
사용자 모델
스킬/가용 시간/초기 자본 정보를 포함한 확장 프로필
"""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 사용자 프로필 (부업 추천에 활용)
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)          # 보유 스킬 (쉼표 구분)
    available_hours: Mapped[float | None] = mapped_column(Float, nullable=True)  # 주당 가용 시간
    initial_capital: Mapped[float | None] = mapped_column(Float, nullable=True)  # 초기 투자 가능 금액 (원)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 관계: 사용자 → 아이디어 목록
    ideas: Mapped[list["SideHustleIdea"]] = relationship(
        "SideHustleIdea", back_populates="owner", cascade="all, delete-orphan"
    )
