from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.hustle import Hustle, HustleTask
from app.models.profile import UserProfile
from app.services.matcher import HustleMatcher
from app.services.roadmap import RoadmapGenerator
from app.utils.auth import get_current_user
from pydantic import BaseModel, Field


router = APIRouter(prefix="/hustles", tags=["hustles"])
matcher = HustleMatcher()
roadmap_gen = RoadmapGenerator()


# --- Schemas ---

class ProfileCreate(BaseModel):
    skills: List[str] = Field(default_factory=list)
    skill_level: str = "beginner"
    available_hours_per_week: float = Field(default=10.0, gt=0)
    available_capital: float = Field(default=0.0, ge=0)
    preferred_categories: List[str] = Field(default_factory=list)
    min_expected_income: float = Field(default=0.0, ge=0)
    risk_tolerance: str = "medium"
    work_style: str = "flexible"
    bio: Optional[str] = None
    location: Optional[str] = None


class HustleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    category: str
    description: Optional[str] = None
    expected_income: float = Field(default=0.0, ge=0)
    required_hours: float = Field(default=0.0, ge=0)
    required_capital: float = Field(default=0.0, ge=0)
    difficulty: str = "medium"
    platform: Optional[str] = None


class TaskUpdate(BaseModel):
    is_done: bool


class HustleStatusUpdate(BaseModel):
    status: str  # idea / in_progress / completed / paused


# --- Profile Endpoints ---

@router.post("/profile", status_code=status.HTTP_201_CREATED)
async def create_or_update_profile(
    data: ProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """사용자 프로필 생성 또는 업데이트."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if profile:
        for field, value in data.model_dump().items():
            setattr(profile, field, value)
        profile.updated_at = datetime.utcnow()
    else:
        profile = UserProfile(user_id=current_user.id, **data.model_dump())
        db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return {"id": profile.id, "message": "프로필이 저장되었습니다."}


@router.get("/profile")
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """사용자 프로필 조회."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="프로필이 없습니다. 먼저 프로필을 생성하세요.")
    return profile


# --- Hustle Match & List ---

@router.post("/match", status_code=status.HTTP_201_CREATED)
async def match_and_save_hustles(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """AI로 맞춤 부업 아이디어 5개 추천 및 저장."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=400, detail="프로필을 먼저 생성하세요.")

    ideas = await matcher.match_hustles(profile)
    saved = []
    for idea in ideas:
        hustle = Hustle(
            profile_id=profile.id,
            user_id=current_user.id,
            title=idea.get("title", ""),
            category=idea.get("category", "기타"),
            description=idea.get("description"),
            expected_income=idea.get("expected_income", 0),
            required_hours=idea.get("required_hours", 0),
            required_capital=idea.get("required_capital", 0),
            difficulty=idea.get("difficulty", "medium"),
            platform=idea.get("platform"),
            match_score=idea.get("match_score", 0),
            ai_generated=True,
        )
        db.add(hustle)
        saved.append(idea)
    await db.commit()
    return {"count": len(saved), "hustles": saved}


@router.get("/", )
async def list_hustles(
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """부업 아이디어 목록 조회."""
    query = select(Hustle).where(Hustle.user_id == current_user.id)
    if status_filter:
        query = query.where(Hustle.status == status_filter)
    result = await db.execute(query.order_by(Hustle.match_score.desc()))
    return result.scalars().all()


@router.get("/{hustle_id}")
async def get_hustle(
    hustle_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """특정 부업 상세 조회."""
    result = await db.execute(
        select(Hustle).where(Hustle.id == hustle_id, Hustle.user_id == current_user.id)
    )
    hustle = result.scalar_one_or_none()
    if not hustle:
        raise HTTPException(status_code=404, detail="부업을 찾을 수 없습니다.")
    return hustle


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_hustle(
    data: HustleCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """수동으로 부업 아이디어 추가."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=400, detail="프로필을 먼저 생성하세요.")

    hustle = Hustle(
        profile_id=profile.id,
        user_id=current_user.id,
        ai_generated=False,
        **data.model_dump(),
    )
    db.add(hustle)
    await db.commit()
    await db.refresh(hustle)
    return hustle


@router.patch("/{hustle_id}/status")
async def update_hustle_status(
    hustle_id: int,
    data: HustleStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """부업 진행 상태 업데이트."""
    result = await db.execute(
        select(Hustle).where(Hustle.id == hustle_id, Hustle.user_id == current_user.id)
    )
    hustle = result.scalar_one_or_none()
    if not hustle:
        raise HTTPException(status_code=404, detail="부업을 찾을 수 없습니다.")
    hustle.status = data.status
    if data.status == "in_progress" and not hustle.started_at:
        hustle.started_at = datetime.utcnow()
    elif data.status == "completed":
        hustle.completed_at = datetime.utcnow()
    hustle.updated_at = datetime.utcnow()
    await db.commit()
    return {"id": hustle_id, "status": data.status}


# --- Roadmap ---

@router.post("/{hustle_id}/roadmap")
async def generate_roadmap(
    hustle_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """AI로 부업 수익화 로드맵 생성 및 저장."""
    result = await db.execute(
        select(Hustle).where(Hustle.id == hustle_id, Hustle.user_id == current_user.id)
    )
    hustle = result.scalar_one_or_none()
    if not hustle:
        raise HTTPException(status_code=404, detail="부업을 찾을 수 없습니다.")

    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    result_data = await roadmap_gen.generate_roadmap(
        hustle_title=hustle.title,
        hustle_category=hustle.category,
        expected_income=hustle.expected_income,
        available_hours=profile.available_hours_per_week if profile else 10,
        available_capital=profile.available_capital if profile else 0,
        skill_level=profile.skill_level if profile else "beginner",
    )

    hustle.roadmap = result_data["roadmap"]
    hustle.updated_at = datetime.utcnow()

    # 태스크 자동 생성 (30일 단계)
    phases = result_data["roadmap"].get("phases", {})
    for phase_key, phase_data in phases.items():
        for task_data in phase_data.get("tasks", []):
            task = HustleTask(
                hustle_id=hustle_id,
                title=task_data.get("title", ""),
                description=task_data.get("description"),
                phase=phase_key,
            )
            db.add(task)

    await db.commit()
    return result_data


@router.get("/{hustle_id}/tasks")
async def list_tasks(
    hustle_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """부업 태스크 목록 조회."""
    result = await db.execute(
        select(Hustle).where(Hustle.id == hustle_id, Hustle.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="부업을 찾을 수 없습니다.")
    tasks = await db.execute(
        select(HustleTask).where(HustleTask.hustle_id == hustle_id)
    )
    return tasks.scalars().all()


@router.patch("/{hustle_id}/tasks/{task_id}")
async def update_task(
    hustle_id: int,
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """태스크 완료 처리."""
    result = await db.execute(
        select(HustleTask).where(
            HustleTask.id == task_id,
            HustleTask.hustle_id == hustle_id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="태스크를 찾을 수 없습니다.")
    task.is_done = data.is_done
    if data.is_done:
        task.completed_at = datetime.utcnow()
    await db.commit()
    return {"id": task_id, "is_done": data.is_done}
