import os
import json
from typing import List, Dict, Any
import google.generativeai as genai
from app.models.profile import UserProfile


genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))


class HustleMatcher:
    """Gemini AI 기반 부업 아이디어 매칭 서비스."""

    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def match_hustles(self, profile: UserProfile) -> List[Dict[str, Any]]:
        """사용자 프로필 기반 맞춤형 부업 아이디어 5개 추천."""

        prompt = f"""
당신은 부업 전문 커리어 컨설턴트입니다.
사용자 프로필을 분석하여 가장 적합한 부업 아이디어 5개를 추천해주세요.

## 사용자 프로필
- 보유 스킬: {', '.join(profile.skills) if profile.skills else '없음'}
- 스킬 수준: {profile.skill_level}
- 주당 가용 시간: {profile.available_hours_per_week}시간
- 초기 투자 가능 금액: {profile.available_capital:,.0f}원
- 선호 카테고리: {', '.join(profile.preferred_categories) if profile.preferred_categories else '제한 없음'}
- 최소 기대 월 수익: {profile.min_expected_income:,.0f}원
- 리스크 허용도: {profile.risk_tolerance}
- 선호 업무 방식: {profile.work_style}

다음 JSON 배열 형식으로 정확히 5개의 부업을 추천해주세요:
[
  {{
    "title": "부업 이름",
    "category": "카테고리 (IT/콘텐츠/교육/디자인/커머스/기타 중 하나)",
    "description": "부업 상세 설명 (2-3문장)",
    "expected_income": 예상_월_수익_숫자_원,
    "required_hours": 주당_필요_시간_숫자,
    "required_capital": 초기_필요_자본_숫자_원,
    "difficulty": "easy/medium/hard 중 하나",
    "platform": "주요 활동 플랫폼",
    "match_score": 매칭_점수_0_100,
    "why_match": "이 사용자에게 적합한 이유"
  }}
]
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            ideas = json.loads(text)
            if not isinstance(ideas, list):
                ideas = []
            return ideas[:5]
        except Exception as e:
            return [
                {
                    "title": "프리랜서 개발/디자인",
                    "category": "IT",
                    "description": "보유 스킬을 활용한 프리랜서 프로젝트 수행.",
                    "expected_income": 500000,
                    "required_hours": 10,
                    "required_capital": 0,
                    "difficulty": "medium",
                    "platform": "크몽, 숨고",
                    "match_score": 70,
                    "why_match": "AI 분석 일시 불가. 기본 추천을 제공합니다.",
                    "error": str(e),
                }
            ]

    async def evaluate_hustle_fit(
        self,
        profile: UserProfile,
        hustle_title: str,
        hustle_category: str,
    ) -> Dict[str, Any]:
        """특정 부업 아이디어의 적합도 상세 평가."""

        prompt = f"""
다음 사용자와 부업 아이디어의 적합도를 평가해주세요.

사용자: 스킬={profile.skills}, 가용시간={profile.available_hours_per_week}h/주, 자본={profile.available_capital:,.0f}원
부업: {hustle_title} ({hustle_category})

JSON 형식으로 응답:
{{
  "fit_score": 점수_0_100,
  "pros": ["장점1", "장점2", "장점3"],
  "cons": ["단점1", "단점2"],
  "requirements_gap": ["부족한 점1", "부족한 점2"],
  "recommendation": "최종 추천 여부 및 이유"
}}
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except Exception as e:
            return {
                "fit_score": 50,
                "pros": [],
                "cons": [],
                "requirements_gap": [],
                "recommendation": "평가 불가",
                "error": str(e),
            }
