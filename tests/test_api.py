"""Tests pour les endpoints de l'API FastAPI."""
import pytest
from httpx import AsyncClient, ASGITransport
from dataviz_backend.main import app


@pytest.fixture
def sample_csv():
    return (
        "produit,ventes,prix\n"
        "A,100,10.5\n"
        "B,200,20.0\n"
        "C,150,15.5\n"
        "D,300,25.0\n"
        "E,50,8.0\n"
    )


@pytest.mark.asyncio
async def test_health_check():
    """Test que /health retourne un status healthy."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_root_returns_html():
    """Test que / retourne du HTML."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "DataViz LLM" in response.text


@pytest.mark.asyncio
async def test_root_has_no_cache_headers():
    """Test que les headers no-cache sont presents."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
    assert "no-cache" in response.headers.get("cache-control", "")


@pytest.mark.asyncio
async def test_analyze_missing_file():
    """Test que /api/analyze retourne 422 sans fichier."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/analyze",
            data={"problem": "test question"}
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_missing_problem():
    """Test que /api/analyze retourne 422 sans problematique."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/analyze",
            files={"file": ("test.csv", b"a,b\n1,2", "text/csv")}
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_missing_body():
    """Test que /api/generate retourne 422 sans body."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/generate")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_invalid_body():
    """Test que /api/generate retourne 422 avec un body invalide."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/generate",
            json={"wrong_field": "test"}
        )
    assert response.status_code == 422
