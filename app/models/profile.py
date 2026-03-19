from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)

    # 스킬 정보
    skills = Column(JSON, nullable=False, default=list)  # ["Python", "디자인", "글쓰기"]
    skill_level = Column(String(50), default="beginner")  # beginner / intermediate / expert

    # 가용 시간
    available_hours_per_week = Column(Float, default=10.0)  # 주당 가용 시간

    # 자본
    available_capital = Column(Float, default=0.0)  # 초기 투자 가능 금액 (원)

    # 선호 조건
    preferred_categories = Column(JSON, nullable=False, default=list)  # ["IT", "콘텐츠", "교육"]
    min_expected_income = Column(Float, default=0.0)   # 최소 기대 월 수익 (원)
    risk_tolerance = Column(String(20), default="medium")  # low / medium / high
    work_style = Column(String(50), default="flexible")    # fixed / flexible / project

    # 추가 정보
    bio = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hustles = relationship("Hustle", back_populates="profile", cascade="all, delete-orphan")
