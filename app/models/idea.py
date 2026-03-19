"""
부업 아이디어 모델
AI가 생성한 부업 아이디어와 수익 예측 정보를 저장합니다.
"""
from datetime import datetime
from sqlalchemy import String, Float, Boolean, ForeignKey, DateTime, Text, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class IdeaCategory(str, enum.Enum):
    """부업 카테고리"""
    FREELANCE = "freelance"         # 프리랜서 (번역, 디자인, 개발 등)
    ONLINE_SALES = "online_sales"   # 온라인 판매 (쿠팡, 스마트스토어 등)
    CONTENT = "content"             # 콘텐츠 창작 (유튜브, 블로그, 인스타 등)
    INVESTMENT = "investment"       # 소액 투자 (P2P, 공모주 등)
    OFFLINE = "offline"             # 오프라인 (과외, 배달, 알바 등)


class DifficultyLevel(str, enum.Enum):
    """난이도"""
    EASY = "easy"       # 쉬움 (바로 시작 가능)
    MEDIUM = "medium"   # 보통 (1~3개월 준비)
    HARD = "hard"       # 어려움 (3개월 이상 준비)


class SideHustleIdea(Base):
    __tablename__ = "side_hustle_ideas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # 아이디어 기본 정보
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[IdeaCategory] = mapped_column(Enum(IdeaCategory), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # 수익 예측
    estimated_income_min: Mapped[float] = mapped_column(Float, default=0.0)  # 예상 최소 월수입 (원)
    estimated_income_max: Mapped[float] = mapped_column(Float, default=0.0)  # 예상 최대 월수입 (원)
    startup_cost: Mapped[float] = mapped_column(Float, default=0.0)          # 시작 비용 (원)
    time_required: Mapped[float] = mapped_column(Float, default=0.0)         # 주당 필요 시간

    # 부가 정보
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM
    )
    roadmap: Mapped[str | None] = mapped_column(Text, nullable=True)   # 시작 로드맵 (프리미엄)
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False)     # 북마크 여부

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 관계: 아이디어 → 소유자(User)
    owner: Mapped["User"] = relationship("User", back_populates="ideas")
