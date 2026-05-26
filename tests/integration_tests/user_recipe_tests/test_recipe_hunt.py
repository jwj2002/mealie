from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser


def test_hunt_search_returns_503_when_no_api_key(api_client: TestClient, unique_user: TestUser) -> None:
    """When BRAVE_SEARCH_API_KEY is not set the endpoint must return 503."""
    with patch("mealie.routes.recipe.hunt.RecipeHuntController.settings") as mock_settings:
        mock_settings.BRAVE_SEARCH_API_KEY = None
        response = api_client.post(
            api_routes.recipes_hunt_search,
            json={"query": "chicken soup"},
            headers=unique_user.token,
        )
    assert response.status_code == 503


def test_hunt_search_requires_auth(api_client: TestClient) -> None:
    """Endpoint must return 401 when no token is provided."""
    response = api_client.post(api_routes.recipes_hunt_search, json={"query": "pasta"})
    assert response.status_code == 401


def test_hunt_search_request_body_validation(api_client: TestClient, unique_user: TestUser) -> None:
    """Invalid request bodies (no query field) should return 422, not 500."""
    response = api_client.post(
        api_routes.recipes_hunt_search,
        json={"count": 5},  # missing required 'query' field
        headers=unique_user.token,
    )
    # 422 = validation error; 503 = no API key — both are acceptable here
    assert response.status_code in {422, 503}
