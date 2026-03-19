"""
수익 시뮬레이션 서비스 (프리미엄 전용)
월수입 성장 곡선, 손익분기점, 12개월 ROI 계산
"""
from typing import Optional
from app.models.idea import SideHustleIdea


# 카테고리별 월별 성장률 (초기 3개월 빠른 성장, 이후 안정화)
GROWTH_PROFILES = {
    "freelance":     [0.3, 0.6, 0.8, 0.9, 1.0, 1.0, 1.1, 1.1, 1.2, 1.2, 1.3, 1.3],
    "online_sales":  [0.1, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 1.0, 1.0, 1.1, 1.1, 1.2],
    "content":       [0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    "investment":    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
    "offline":       [0.5, 0.7, 0.9, 1.0, 1.0, 1.0, 1.1, 1.1, 1.1, 1.2, 1.2, 1.2],
}

# 카테고리별 월 운영 비용 비율 (수입 대비)
OPERATING_COST_RATIO = {
    "freelance":    0.05,   # 플랫폼 수수료
    "online_sales": 0.30,   # 물류/광고비
    "content":      0.10,   # 장비/소프트웨어
    "investment":   0.02,   # 거래 수수료
    "offline":      0.05,   # 교통/재료비
}


def simulate_income(idea: SideHustleIdea) -> dict:
    """
    12개월 수익 시뮬레이션
    - 월별 예상 수입 성장 곡선
    - 손익분기점 (startup_cost 회수 월)
    - 12개월 누적 수입/비용/순이익
    """
    category = idea.category.value
    target_income = (idea.estimated_income_min + idea.estimated_income_max) / 2
    startup_cost = idea.startup_cost
    op_cost_ratio = OPERATING_COST_RATIO.get(category, 0.1)
    growth_profile = GROWTH_PROFILES.get(category, [1.0] * 12)

    monthly_income: list[float] = []
    monthly_cost: list[float] = []
    cumulative_profit = -startup_cost  # 초기 투자 비용에서 시작
    breakeven_month: Optional[int] = None

    for month_idx, growth_factor in enumerate(growth_profile):
        income = round(target_income * growth_factor, 0)
        op_cost = round(income * op_cost_ratio, 0)

        monthly_income.append(income)
        monthly_cost.append(op_cost)

        cumulative_profit += income - op_cost

        # 손익분기점 탐색 (아직 미달성 상태에서 흑자 전환 시)
        if breakeven_month is None and cumulative_profit >= 0:
            breakeven_month = month_idx + 1  # 1-based 월

    total_income = sum(monthly_income)
    total_cost = startup_cost + sum(monthly_cost)
    net_profit = total_income - total_cost
    roi_pct = (net_profit / total_cost * 100) if total_cost > 0 else 0.0

    return {
        "idea_title": idea.title,
        "monthly_growth": monthly_income,
        "breakeven_month": breakeven_month,
        "total_12month_income": round(total_income, 0),
        "total_12month_cost": round(total_cost, 0),
        "net_profit_12month": round(net_profit, 0),
        "roi_pct": round(roi_pct, 1),
    }
