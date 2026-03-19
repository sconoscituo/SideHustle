import os
import json
from typing import Dict, Any, List
import google.generativeai as genai


genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))


class RoadmapGenerator:
    """Gemini AI 기반 부업 수익화 로드맵 생성 서비스."""

    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def generate_roadmap(
        self,
        hustle_title: str,
        hustle_category: str,
        expected_income: float,
        available_hours: float,
        available_capital: float,
        skill_level: str = "beginner",
    ) -> Dict[str, Any]:
        """30일/90일/1년 수익화 로드맵 생성."""

        prompt = f"""
부업 수익화 전문가로서 다음 부업의 단계별 로드맵을 작성해주세요.

## 부업 정보
- 부업명: {hustle_title}
- 카테고리: {hustle_category}
- 목표 월 수익: {expected_income:,.0f}원
- 주당 가용 시간: {available_hours}시간
- 초기 자본: {available_capital:,.0f}원
- 현재 스킬 수준: {skill_level}

다음 JSON 형식으로 로드맵을 작성해주세요:
{{
  "overview": "로드맵 전체 개요 (2-3문장)",
  "phases": {{
    "30d": {{
      "goal": "30일 목표",
      "expected_income": 예상_수익_원,
      "tasks": [
        {{"title": "태스크 제목", "description": "상세 내용", "week": 1}},
        {{"title": "태스크 제목", "description": "상세 내용", "week": 2}},
        {{"title": "태스크 제목", "description": "상세 내용", "week": 3}},
        {{"title": "태스크 제목", "description": "상세 내용", "week": 4}}
      ],
      "milestones": ["달성 지표1", "달성 지표2"]
    }},
    "90d": {{
      "goal": "90일 목표",
      "expected_income": 예상_수익_원,
      "tasks": [
        {{"title": "태스크 제목", "description": "상세 내용", "month": 2}},
        {{"title": "태스크 제목", "description": "상세 내용", "month": 3}}
      ],
      "milestones": ["달성 지표1", "달성 지표2"]
    }},
    "365d": {{
      "goal": "1년 목표",
      "expected_income": 예상_수익_원,
      "tasks": [
        {{"title": "태스크 제목", "description": "상세 내용", "quarter": 2}},
        {{"title": "태스크 제목", "description": "상세 내용", "quarter": 3}},
        {{"title": "태스크 제목", "description": "상세 내용", "quarter": 4}}
      ],
      "milestones": ["달성 지표1", "달성 지표2", "달성 지표3"]
    }}
  }},
  "key_resources": ["필요 리소스/도구1", "필요 리소스/도구2", "필요 리소스/도구3"],
  "success_tips": ["성공 팁1", "성공 팁2", "성공 팁3"],
  "risk_factors": ["리스크1", "리스크2"]
}}
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            roadmap = json.loads(text)
        except Exception as e:
            roadmap = {
                "overview": "AI 로드맵 생성 일시 불가.",
                "phases": {
                    "30d": {"goal": "초기 세팅", "expected_income": 0, "tasks": [], "milestones": []},
                    "90d": {"goal": "첫 수익 달성", "expected_income": expected_income * 0.5, "tasks": [], "milestones": []},
                    "365d": {"goal": "목표 수익 달성", "expected_income": expected_income, "tasks": [], "milestones": []},
                },
                "key_resources": [],
                "success_tips": [],
                "risk_factors": [],
                "error": str(e),
            }

        return {
            "hustle_title": hustle_title,
            "target_monthly_income": expected_income,
            "roadmap": roadmap,
        }

    async def generate_daily_tasks(
        self,
        hustle_title: str,
        phase: str,
        completed_tasks: List[str],
    ) -> List[Dict[str, Any]]:
        """현재 단계에 맞는 다음 실행 태스크 생성."""

        prompt = f"""
부업 "{hustle_title}"의 {phase} 단계에서 다음 실행 태스크 5개를 생성해주세요.
완료된 태스크: {', '.join(completed_tasks) if completed_tasks else '없음'}

JSON 배열 형식:
[
  {{"title": "태스크 제목", "description": "상세 내용", "estimated_hours": 예상_소요_시간, "priority": "high/medium/low"}}
]
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            tasks = json.loads(text)
            return tasks[:5] if isinstance(tasks, list) else []
        except Exception as e:
            return [{"title": "태스크 생성 실패", "description": str(e), "estimated_hours": 1, "priority": "low"}]
