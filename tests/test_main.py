"""
SideHustle API 기본 테스트
회원가입, 로그인, 프로필 업데이트, 아이디어 생성/조회/삭제, 시뮬레이션 검증
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.database import Base, get_db

# 테스트용 인메모리 SQLite DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    """테스트용 DB 세션 오버라이드"""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """각 테스트 전 테이블 생성, 후 삭제"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    """비동기 테스트 클라이언트"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client):
    """테스트용 인증 헤더"""
    await client.post("/api/users/register", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    resp = await client.post("/api/users/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def premium_headers(client):
    """프리미엄 사용자 인증 헤더"""
    await client.post("/api/users/register", json={
        "email": "premium@example.com",
        "password": "premiumpass123"
    })
    resp = await client.post("/api/users/login", data={
        "username": "premium@example.com",
        "password": "premiumpass123"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # 프리미엄 업그레이드
    await client.post("/api/users/upgrade", headers=headers)
    return headers


# 아이디어 생성 공통 페이로드
IDEA_PAYLOAD = {
    "profile": {
        "skills": "Python, 글쓰기",
        "available_hours": 10,
        "initial_capital": 500000
    },
    "count": 2
}


@pytest.mark.asyncio
async def test_health_check(client):
    """헬스체크 엔드포인트 테스트"""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register(client):
    """회원가입 테스트"""
    resp = await client.post("/api/users/register", json={
        "email": "new@example.com",
        "password": "password123"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["is_premium"] is False


@pytest.mark.asyncio
async def test_register_duplicate(client):
    """이메일 중복 회원가입 차단 테스트"""
    payload = {"email": "dup@example.com", "password": "pass123"}
    await client.post("/api/users/register", json=payload)
    resp = await client.post("/api/users/register", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login(client):
    """로그인 테스트"""
    await client.post("/api/users/register", json={
        "email": "login@example.com", "password": "pass123"
    })
    resp = await client.post("/api/users/login", data={
        "username": "login@example.com", "password": "pass123"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_update_profile(client, auth_headers):
    """프로필 업데이트 테스트"""
    resp = await client.patch("/api/users/me", json={
        "skills": "Python, 영상편집",
        "available_hours": 15,
        "initial_capital": 1000000
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["skills"] == "Python, 영상편집"
    assert data["available_hours"] == 15.0


@pytest.mark.asyncio
async def test_generate_ideas(client, auth_headers):
    """아이디어 생성 테스트"""
    resp = await client.post("/api/ideas/generate", json=IDEA_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 201
    ideas = resp.json()
    assert len(ideas) >= 1
    assert "title" in ideas[0]
    assert "estimated_income_min" in ideas[0]


@pytest.mark.asyncio
async def test_list_ideas(client, auth_headers):
    """아이디어 목록 조회 테스트"""
    await client.post("/api/ideas/generate", json=IDEA_PAYLOAD, headers=auth_headers)
    resp = await client.get("/api/ideas/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_free_plan_limit(client, auth_headers):
    """무료 플랜 3개 제한 테스트"""
    # 3개 생성
    await client.post("/api/ideas/generate", json={
        "profile": {"skills": "글쓰기", "available_hours": 5, "initial_capital": 0},
        "count": 3
    }, headers=auth_headers)

    # 추가 생성 차단
    resp = await client.post("/api/ideas/generate", json={
        "profile": {"skills": "글쓰기", "available_hours": 5, "initial_capital": 0},
        "count": 1
    }, headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_toggle_save(client, auth_headers):
    """아이디어 저장 토글 테스트"""
    create_resp = await client.post("/api/ideas/generate", json=IDEA_PAYLOAD, headers=auth_headers)
    idea_id = create_resp.json()[0]["id"]

    # 저장
    save_resp = await client.post(f"/api/ideas/{idea_id}/save", headers=auth_headers)
    assert save_resp.status_code == 200
    assert save_resp.json()["is_saved"] is True

    # 저장 해제
    unsave_resp = await client.post(f"/api/ideas/{idea_id}/save", headers=auth_headers)
    assert unsave_resp.json()["is_saved"] is False


@pytest.mark.asyncio
async def test_simulate_premium(client, premium_headers):
    """수익 시뮬레이션 프리미엄 테스트"""
    create_resp = await client.post("/api/ideas/generate", json=IDEA_PAYLOAD, headers=premium_headers)
    idea_id = create_resp.json()[0]["id"]

    sim_resp = await client.get(f"/api/ideas/{idea_id}/simulate", headers=premium_headers)
    assert sim_resp.status_code == 200
    data = sim_resp.json()
    assert "monthly_growth" in data
    assert len(data["monthly_growth"]) == 12
    assert "roi_pct" in data


@pytest.mark.asyncio
async def test_simulate_free_blocked(client, auth_headers):
    """무료 사용자 시뮬레이션 차단 테스트"""
    create_resp = await client.post("/api/ideas/generate", json=IDEA_PAYLOAD, headers=auth_headers)
    idea_id = create_resp.json()[0]["id"]

    resp = await client.get(f"/api/ideas/{idea_id}/simulate", headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_idea(client, auth_headers):
    """아이디어 삭제 테스트"""
    create_resp = await client.post("/api/ideas/generate", json=IDEA_PAYLOAD, headers=auth_headers)
    idea_id = create_resp.json()[0]["id"]

    del_resp = await client.delete(f"/api/ideas/{idea_id}", headers=auth_headers)
    assert del_resp.status_code == 204
