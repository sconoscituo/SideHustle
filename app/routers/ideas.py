"""
부업 아이디어 라우터
아이디어 생성/조회/저장/삭제 + 수익 시뮬레이션
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.idea import SideHustleIdea
from app.models.user import User
from app.schemas.idea import IdeaRequest, IdeaResponse, SimulationResult
from app.services.idea_generator import generate_ideas
from app.services.simulator import simulate_income
from app.utils.auth import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/api/ideas", tags=["부업 아이디어"])
settings = get_settings()


@router.post("/generate", response_model=list[IdeaResponse], status_code=status.HTTP_201_CREATED)
async def generate_and_save_ideas(
    request: IdeaRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    AI 부업 아이디어 생성 및 저장
    - 무료: 최대 3개, 로드맵 미포함
    - 프리미엄: 최대 10개, 상세 로드맵 포함
    """
    # 무료 플랜 제한
    if not current_user.is_premium:
        # 이미 생성한 아이디어 수 확인
        result = await db.execute(
            select(SideHustleIdea).where(SideHustleIdea.user_id == current_user.id)
        )
        existing_count = len(result.scalars().all())
        if existing_count >= settings.free_plan_idea_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"무료 플랜은 최대 {settings.free_plan_idea_limit}개의 아이디어만 생성할 수 있습니다. 프리미엄으로 업그레이드하세요.",
            )
        # 무료 플랜: 요청 개수 제한
        request.count = min(request.count, settings.free_plan_idea_limit - existing_count)

    include_roadmap = current_user.is_premium
    ideas_data = await generate_ideas(request.profile, request.count, include_roadmap)

    saved_ideas = []
    for idea_dict in ideas_data:
        idea = SideHustleIdea(user_id=current_user.id, **idea_dict)
        db.add(idea)
        await db.flush()
        await db.refresh(idea)
        saved_ideas.append(idea)

    return saved_ideas


@router.get("/", response_model=list[IdeaResponse])
async def list_ideas(
    saved_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """내 아이디어 목록 조회 (saved_only=True이면 저장된 것만)"""
    query = select(SideHustleIdea).where(SideHustleIdea.user_id == current_user.id)
    if saved_only:
        query = query.where(SideHustleIdea.is_saved == True)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{idea_id}", response_model=IdeaResponse)
async def get_idea(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """특정 아이디어 조회"""
    result = await db.execute(
        select(SideHustleIdea).where(
            SideHustleIdea.id == idea_id,
            SideHustleIdea.user_id == current_user.id,
        )
    )
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="아이디어를 찾을 수 없습니다.")
    return idea


@router.post("/{idea_id}/save", response_model=IdeaResponse)
async def toggle_save(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """아이디어 저장/저장 해제 토글"""
    result = await db.execute(
        select(SideHustleIdea).where(
            SideHustleIdea.id == idea_id,
            SideHustleIdea.user_id == current_user.id,
        )
    )
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="아이디어를 찾을 수 없습니다.")

    idea.is_saved = not idea.is_saved
    db.add(idea)
    await db.flush()
    await db.refresh(idea)
    return idea


@router.get("/{idea_id}/simulate", response_model=SimulationResult)
async def simulate(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """수익 시뮬레이션 (프리미엄 전용)"""
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="수익 시뮬레이션은 프리미엄 플랜 전용입니다.",
        )

    result = await db.execute(
        select(SideHustleIdea).where(
            SideHustleIdea.id == idea_id,
            SideHustleIdea.user_id == current_user.id,
        )
    )
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="아이디어를 찾을 수 없습니다.")

    simulation = simulate_income(idea)
    return SimulationResult(**simulation)


@router.delete("/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_idea(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """아이디어 삭제"""
    result = await db.execute(
        select(SideHustleIdea).where(
            SideHustleIdea.id == idea_id,
            SideHustleIdea.user_id == current_user.id,
        )
    )
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="아이디어를 찾을 수 없습니다.")

    await db.delete(idea)
