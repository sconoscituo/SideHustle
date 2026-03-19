# SideHustle 💼

AI 부업 아이디어 생성 + 수익 시뮬레이터

## 개요

사용자의 스킬/가용 시간/초기 자본을 입력하면 Gemini AI가 맞춤 부업 아이디어를 추천하고,
예상 월수입 계산 + 시작 로드맵을 제공합니다.

## 주요 기능

- 스킬/시간/자본 기반 AI 부업 아이디어 추천
- 카테고리: 프리랜서 / 온라인판매 / 콘텐츠 / 투자 / 오프라인
- 예상 수익 범위 및 시작 비용 계산
- 월수입 성장 곡선 시뮬레이션
- 손익분기점 분석
- 아이디어 저장/관리

## 수익 구조

| 플랜 | 아이디어 수 | 상세 로드맵 | 수익 시뮬레이션 |
|------|------------|-----------|--------------|
| 무료 | 3개        | X         | X            |
| 프리미엄 | 무제한  | O         | O            |

## 빠른 시작

```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일에 실제 값 입력

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload
```

## Docker 실행

```bash
docker-compose up -d
```

## API 문서

서버 실행 후 http://localhost:8000/docs 접속

## 기술 스택

- **Backend**: FastAPI, SQLAlchemy, aiosqlite
- **AI**: Google Gemini API
- **인증**: JWT (python-jose)
