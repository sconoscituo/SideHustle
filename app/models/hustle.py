from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Hustle(Base):
    __tablename__ = "hustles"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # 부업 기본 정보
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # IT / 콘텐츠 / 교육 / 디자인 / 기타
    description = Column(Text, nullable=True)
    expected_income = Column(Float, default=0.0)    # 예상 월 수익 (원)
    required_hours = Column(Float, default=0.0)     # 주당 필요 시간
    required_capital = Column(Float, default=0.0)   # 초기 필요 자본 (원)
    difficulty = Column(String(20), default="medium")  # easy / medium / hard
    platform = Column(String(255), nullable=True)   # 주요 플랫폼

    # AI 생성 로드맵
    roadmap = Column(JSON, nullable=True)           # 30/90/365일 계획

    # 진행 상태
    status = Column(String(30), default="idea")     # idea / in_progress / completed / paused
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # AI 매칭 점수
    match_score = Column(Float, default=0.0)        # 0~100
    ai_generated = Column(Boolean, default=False)   # AI 추천 여부

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("UserProfile", back_populates="hustles")
    tasks = relationship("HustleTask", back_populates="hustle", cascade="all, delete-orphan")


class HustleTask(Base):
    __tablename__ = "hustle_tasks"

    id = Column(Integer, primary_key=True, index=True)
    hustle_id = Column(Integer, ForeignKey("hustles.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    phase = Column(String(20), default="30d")       # 30d / 90d / 365d
    is_done = Column(Boolean, default=False)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    hustle = relationship("Hustle", back_populates="tasks")
