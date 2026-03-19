"""
부업 아이디어 관련 Pydantic 스키마
요청/응답 데이터 검증 및 직렬화
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from app.models.idea import IdeaCategory, DifficultyLevel


class UserProfile(BaseModel):
    """부업 추천 요청 시 전달하는 사용자 프로필"""
    skills: str = Field(..., description="보유 스킬 (예: Python, 영상편집, 글쓰기)")
    available_hours: float = Field(..., gt=0, le=168, description="주당 가용 시간")
    initial_capital: float = Field(..., ge=0, description="초기 투자 가능 금액 (원)")
    preferred_category: Optional[IdeaCategory] = Field(
        None, description="선호 카테고리 (없으면 전체 탐색)"
    )


class IdeaRequest(BaseModel):
    """아이디어 생성 요청"""
    profile: UserProfile
    count: int = Field(default=3, ge=1, le=10, description="생성할 아이디어 수")


class IdeaResponse(BaseModel):
    """아이디어 응답 스키마"""
    id: int
    user_id: int
    title: str
    category: IdeaCategory
    description: str
    estimated_income_min: float
    estimated_income_max: float
    startup_cost: float
    time_required: float
    difficulty: DifficultyLevel
    roadmap: Optional[str]       # 프리미엄 전용
    is_saved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SimulationResult(BaseModel):
    """수익 시뮬레이션 결과 (프리미엄 전용)"""
    idea_title: str
    monthly_growth: list[float] = Field(description="월별 예상 수입 성장 곡선 (12개월)")
    breakeven_month: Optional[int] = Field(None, description="손익분기점 도달 월 (None이면 12개월 내 미달성)")
    total_12month_income: float = Field(description="12개월 누적 예상 수입")
    total_12month_cost: float = Field(description="12개월 누적 비용")
    net_profit_12month: float = Field(description="12개월 순이익")
    roi_pct: float = Field(description="12개월 ROI (%)")
