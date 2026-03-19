"""
Gemini AI 부업 아이디어 생성 서비스
사용자 프로필 기반 맞춤 부업 아이디어를 생성합니다.
카테고리: 프리랜서 / 온라인판매 / 콘텐츠 / 투자 / 오프라인
"""
import json
import re
import google.generativeai as genai
from app.config import get_settings
from app.schemas.idea import UserProfile
from app.models.idea import IdeaCategory, DifficultyLevel

settings = get_settings()


def _build_prompt(profile: UserProfile, count: int, include_roadmap: bool) -> str:
    """Gemini에 전달할 프롬프트 구성"""
    category_hint = f"카테고리 제한: {profile.preferred_category.value}" if profile.preferred_category else "모든 카테고리 고려"
    roadmap_instruction = "각 아이디어에 'roadmap' 필드(3~5단계 시작 로드맵, 한국어)를 포함하세요." if include_roadmap else "'roadmap' 필드는 null로 설정하세요."

    return f"""당신은 대한민국 최고의 부업 전문 컨설턴트입니다.
아래 사용자 정보를 바탕으로 현실적이고 실행 가능한 부업 아이디어를 {count}개 추천해주세요.

## 사용자 정보
- 보유 스킬: {profile.skills}
- 주당 가용 시간: {profile.available_hours}시간
- 초기 투자 가능 금액: {profile.initial_capital:,.0f}원
- {category_hint}

## 응답 형식
다음 JSON 배열 형식으로만 응답해주세요 (다른 텍스트 없이):
[
  {{
    "title": "부업 제목 (한국어, 30자 이내)",
    "category": "freelance|online_sales|content|investment|offline 중 하나",
    "description": "부업 설명 (한국어, 150자 이내)",
    "estimated_income_min": 최소 월수입(원, 숫자),
    "estimated_income_max": 최대 월수입(원, 숫자),
    "startup_cost": 시작 비용(원, 숫자),
    "time_required": 주당 필요 시간(숫자),
    "difficulty": "easy|medium|hard 중 하나",
    "roadmap": null
  }}
]

{roadmap_instruction}
사용자의 스킬과 가용 시간, 자본에 맞는 현실적인 수치를 제시하세요.
"""


async def generate_ideas(
    profile: UserProfile,
    count: int = 3,
    include_roadmap: bool = False,
) -> list[dict]:
    """
    Gemini AI로 부업 아이디어 생성
    API 키 없거나 오류 시 규칙 기반 기본 아이디어 반환
    """
    if not settings.gemini_api_key:
        return _default_ideas(profile, count, include_roadmap)

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = _build_prompt(profile, count, include_roadmap)
        response = model.generate_content(prompt)
        text = response.text.strip()

        # 마크다운 코드 블록 제거
        text = re.sub(r"```json\s*|\s*```", "", text).strip()
        ideas = json.loads(text)

        # 유효성 검증 및 기본값 보완
        validated = []
        for idea in ideas[:count]:
            validated.append({
                "title": idea.get("title", "부업 아이디어"),
                "category": _validate_category(idea.get("category", "freelance")),
                "description": idea.get("description", ""),
                "estimated_income_min": float(idea.get("estimated_income_min", 0)),
                "estimated_income_max": float(idea.get("estimated_income_max", 0)),
                "startup_cost": float(idea.get("startup_cost", 0)),
                "time_required": float(idea.get("time_required", 0)),
                "difficulty": _validate_difficulty(idea.get("difficulty", "medium")),
                "roadmap": idea.get("roadmap"),
            })
        return validated

    except (json.JSONDecodeError, Exception):
        return _default_ideas(profile, count, include_roadmap)


def _validate_category(value: str) -> str:
    """카테고리 값 유효성 검증"""
    valid = {c.value for c in IdeaCategory}
    return value if value in valid else IdeaCategory.FREELANCE.value


def _validate_difficulty(value: str) -> str:
    """난이도 값 유효성 검증"""
    valid = {d.value for d in DifficultyLevel}
    return value if value in valid else DifficultyLevel.MEDIUM.value


def _default_ideas(profile: UserProfile, count: int, include_roadmap: bool) -> list[dict]:
    """API 미설정 시 규칙 기반 기본 아이디어"""
    # 초기 자본과 시간 기반으로 기본 아이디어 선택
    pool = [
        {
            "title": "재능마켓 프리랜서",
            "category": "freelance",
            "description": "크몽, 숨고 등 재능마켓에서 보유 스킬로 프리랜서 서비스를 제공합니다.",
            "estimated_income_min": 300_000,
            "estimated_income_max": 1_500_000,
            "startup_cost": 0,
            "time_required": min(profile.available_hours, 10),
            "difficulty": "easy",
            "roadmap": "1단계: 재능마켓 프로필 생성\n2단계: 포트폴리오 3개 준비\n3단계: 첫 의뢰 수주\n4단계: 리뷰 쌓기\n5단계: 단가 인상" if include_roadmap else None,
        },
        {
            "title": "스마트스토어 위탁판매",
            "category": "online_sales",
            "description": "네이버 스마트스토어에서 위탁판매로 초기 재고 없이 온라인 쇼핑몰을 운영합니다.",
            "estimated_income_min": 200_000,
            "estimated_income_max": 2_000_000,
            "startup_cost": min(profile.initial_capital, 100_000),
            "time_required": min(profile.available_hours, 8),
            "difficulty": "medium",
            "roadmap": "1단계: 스마트스토어 개설\n2단계: 위탁 공급사 발굴\n3단계: 상품 등록 (50개)\n4단계: 광고 집행\n5단계: 베스트셀러 집중 육성" if include_roadmap else None,
        },
        {
            "title": "블로그/유튜브 수익화",
            "category": "content",
            "description": "관심 분야 콘텐츠를 꾸준히 제작하여 애드센스, 협찬, 제휴 마케팅으로 수익을 창출합니다.",
            "estimated_income_min": 100_000,
            "estimated_income_max": 3_000_000,
            "startup_cost": 0,
            "time_required": min(profile.available_hours, 15),
            "difficulty": "hard",
            "roadmap": "1단계: 니치 주제 선정\n2단계: 주 3회 이상 꾸준한 발행\n3단계: SEO 최적화\n4단계: 애드센스 신청 (방문자 기준 충족)\n5단계: 제휴 마케팅 추가" if include_roadmap else None,
        },
        {
            "title": "과외/학습 코칭",
            "category": "offline",
            "description": "보유 지식과 스킬로 오프라인 또는 온라인 과외를 진행합니다.",
            "estimated_income_min": 400_000,
            "estimated_income_max": 1_200_000,
            "startup_cost": 0,
            "time_required": min(profile.available_hours, 8),
            "difficulty": "easy",
            "roadmap": "1단계: 과외 플랫폼 등록 (과외천국, 아이엠티처)\n2단계: 첫 학생 모집\n3단계: 커리큘럼 개발\n4단계: 후기 관리\n5단계: 그룹 과외로 확장" if include_roadmap else None,
        },
        {
            "title": "P2P 투자 / 공모주 청약",
            "category": "investment",
            "description": "소액 자본으로 P2P 투자 또는 공모주 청약에 참여하여 이자 및 시세 차익을 얻습니다.",
            "estimated_income_min": 50_000,
            "estimated_income_max": 500_000,
            "startup_cost": min(profile.initial_capital, 1_000_000),
            "time_required": 2,
            "difficulty": "easy",
            "roadmap": "1단계: 증권 계정 개설\n2단계: 공모주 캘린더 확인\n3단계: 청약 참여\n4단계: 수익 재투자\n5단계: 포트폴리오 다각화" if include_roadmap else None,
        },
    ]

    return pool[:count]
