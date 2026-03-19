"""
부업 수입 추적 라우터
"""
from datetime import datetime, timedelta
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/income", tags=["수입 추적"])

try:
    from app.models.hustle import SideHustle, IncomeRecord
    HAS_MODELS = True
except ImportError:
    HAS_MODELS = False

try:
    from app.config import config
    GEMINI_KEY = config.GEMINI_API_KEY
except Exception:
    GEMINI_KEY = ""


class IncomeRecordCreate(BaseModel):
    hustle_id: int
    amount: float
    description: Optional[str] = None
    date: Optional[str] = None


@router.post("/record")
async def record_income(
    income: IncomeRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """수입 기록 추가"""
    if not HAS_MODELS:
        return {"message": "모델이 없습니다", "amount": income.amount}

    record = IncomeRecord(
        hustle_id=income.hustle_id,
        user_id=current_user.id,
        amount=income.amount,
        description=income.description,
        recorded_at=datetime.utcnow(),
    )
    db.add(record)
    await db.commit()
    return {"message": "수입이 기록되었습니다", "amount": income.amount}


@router.get("/summary")
async def get_income_summary(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """수입 요약 통계"""
    if not HAS_MODELS:
        return {"total": 0, "period_days": days}

    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            func.sum(IncomeRecord.amount).label("total"),
            func.count(IncomeRecord.id).label("count"),
        ).where(
            IncomeRecord.user_id == current_user.id,
            IncomeRecord.recorded_at >= since,
        )
    )
    row = result.one()
    total = float(row.total or 0)
    return {
        "period_days": days,
        "total_income": total,
        "transaction_count": row.count or 0,
        "daily_average": round(total / days, 0),
        "monthly_projection": round(total / days * 30, 0),
    }


@router.get("/ai-growth-tips")
async def get_growth_tips(
    current_user: User = Depends(get_current_user),
):
    """AI 부업 성장 조언"""
    if not GEMINI_KEY:
        return {"tips": ["꾸준함이 핵심입니다", "수입원을 다양화하세요"]}

    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        "부업으로 수입을 늘리기 위한 실용적인 팁 5가지를 한국어로 알려줘. "
        "각 팁은 구체적이고 실행 가능하게 작성해줘."
    )
    return {"tips": response.text}
