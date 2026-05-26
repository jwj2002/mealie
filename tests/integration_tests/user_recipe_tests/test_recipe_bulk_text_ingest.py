import json

import pytest
from fastapi.testclient import TestClient

import mealie.services.scraper.recipe_scraper as recipe_scraper_module
from mealie.schema.group.ai_providers import AIProviderCreate, AIProviderSettingsUpdate
from mealie.schema.openai.general import OpenAIText
from mealie.services.openai import OpenAIService
from mealie.services.recipe.recipe_data_service import RecipeDataService
from mealie.services.scraper.scraper_strategies import RecipeScraperOpenAI
from tests.utils import api_routes
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser
from tests.utils.helpers import parse_sse_events


def _make_ld_json(name: str) -> str:
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Recipe",
            "name": name,
            "recipeIngredient": ["1 cup flour"],
            "recipeInstructions": [{"@type": "HowToStep", "text": "Mix and bake."}],
        }
    )


TWO_RECIPE_MARKDOWN = """\
# Chocolate Cake

Ingredients:
- 2 cups flour

Steps:
1. Mix.

# Banana Bread

Ingredients:
- 3 bananas

Steps:
1. Mash.
"""


@pytest.fixture(autouse=True)
def bulk_text_test_setup(monkeypatch: pytest.MonkeyPatch, unique_user: TestUser):
    """Configure AI provider and patch out network/image calls."""
    monkeypatch.setattr(recipe_scraper_module, "DEFAULT_SCRAPER_STRATEGIES", [RecipeScraperOpenAI])

    provider = unique_user.repos.group_ai_providers.create(
        AIProviderCreate(name=random_string(), model="gpt-4o", api_key="test-key")
    )
    unique_user.repos.group_ai_provider_settings.update(
        unique_user.repos.group_id,
        AIProviderSettingsUpdate(default_provider_id=provider.id, audio_provider_id=None, image_provider_id=None),
    )

    monkeypatch.setattr(RecipeDataService, "scrape_image", lambda *_: "TEST_IMAGE")


def test_bulk_text_stream_splits_and_creates(
    api_client: TestClient,
    unique_user: TestUser,
    monkeypatch: pytest.MonkeyPatch,
):
    """Two markdown-heading recipes produce two recipe_done events and one done summary."""
    call_count = [0]

    async def mock_get_response(self, prompt, message, *args, **kwargs) -> OpenAIText | None:
        call_count[0] += 1
        # Return different recipe names depending on call order
        name = "Chocolate Cake" if call_count[0] == 1 else "Banana Bread"
        return OpenAIText(text=_make_ld_json(name))

    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    response = api_client.post(
        api_routes.recipes_create_bulk_text_stream,
        json={"text": TWO_RECIPE_MARKDOWN},
        headers=unique_user.token,
    )

    assert response.status_code == 200
    events = parse_sse_events(response.text)

    recipe_done_events = [e for e in events if e["event"] == "recipe_done"]
    done_events = [e for e in events if e["event"] == "done"]

    assert len(recipe_done_events) == 2
    assert len(done_events) == 1

    summary = done_events[0]["data"]
    assert summary["total"] == 2
    assert summary["succeeded"] == 2
    assert summary["failed"] == 0
    assert summary["truncated"] is False

    for evt in recipe_done_events:
        assert evt["data"]["status"] == "created"
        assert evt["data"]["recipe_slug"] != ""


def test_bulk_text_stream_single_recipe(
    api_client: TestClient,
    unique_user: TestUser,
    monkeypatch: pytest.MonkeyPatch,
):
    """Single-heading text produces one recipe_done and one done."""

    async def mock_get_response(self, prompt, message, *args, **kwargs) -> OpenAIText | None:
        return OpenAIText(text=_make_ld_json("Pancakes"))

    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    single_recipe = "# Pancakes\n\nIngredients:\n- 1 cup flour\n\nSteps:\n1. Mix and cook."
    response = api_client.post(
        api_routes.recipes_create_bulk_text_stream,
        json={"text": single_recipe},
        headers=unique_user.token,
    )

    assert response.status_code == 200
    events = parse_sse_events(response.text)

    recipe_done_events = [e for e in events if e["event"] == "recipe_done"]
    done_events = [e for e in events if e["event"] == "done"]

    assert len(recipe_done_events) == 1
    assert len(done_events) == 1
    assert done_events[0]["data"]["succeeded"] == 1
    assert done_events[0]["data"]["failed"] == 0


def test_bulk_text_stream_partial_failure(
    api_client: TestClient,
    unique_user: TestUser,
    monkeypatch: pytest.MonkeyPatch,
):
    """When the second recipe's OpenAI call fails, first is created and second is failed."""
    call_count = [0]

    async def mock_get_response(self, prompt, message, *args, **kwargs) -> OpenAIText | None:
        call_count[0] += 1
        if call_count[0] == 1:
            return OpenAIText(text=_make_ld_json("Good Recipe"))
        raise RuntimeError("Simulated OpenAI failure")

    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    response = api_client.post(
        api_routes.recipes_create_bulk_text_stream,
        json={"text": TWO_RECIPE_MARKDOWN},
        headers=unique_user.token,
    )

    assert response.status_code == 200
    events = parse_sse_events(response.text)

    recipe_done_events = [e for e in events if e["event"] == "recipe_done"]
    done_events = [e for e in events if e["event"] == "done"]

    assert len(recipe_done_events) == 2
    assert recipe_done_events[0]["data"]["status"] == "created"
    assert recipe_done_events[1]["data"]["status"] == "failed"
    assert recipe_done_events[1]["data"]["recipe_slug"] == ""

    summary = done_events[0]["data"]
    assert summary["succeeded"] == 1
    assert summary["failed"] == 1


def test_bulk_text_stream_requires_auth(api_client: TestClient):
    """Unauthenticated request returns 401."""
    response = api_client.post(
        api_routes.recipes_create_bulk_text_stream,
        json={"text": "# Test Recipe\n\nIngredients: flour"},
    )
    assert response.status_code == 401


def test_bulk_text_stream_no_text(api_client: TestClient, unique_user: TestUser):
    """Empty text field fails Pydantic validation with 422."""
    response = api_client.post(
        api_routes.recipes_create_bulk_text_stream,
        json={"text": ""},
        headers=unique_user.token,
    )
    assert response.status_code == 422


def test_bulk_text_stream_extras_populated(
    api_client: TestClient,
    unique_user: TestUser,
    monkeypatch: pytest.MonkeyPatch,
):
    """Created recipe has ingest_source, ingest_at, and ingest_chunk_index in extras."""

    async def mock_get_response(self, prompt, message, *args, **kwargs) -> OpenAIText | None:
        return OpenAIText(text=_make_ld_json("Extras Test Recipe"))

    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    single_recipe = "# Extras Test Recipe\n\nIngredients:\n- 1 egg\n\nSteps:\n1. Boil."
    response = api_client.post(
        api_routes.recipes_create_bulk_text_stream,
        json={"text": single_recipe},
        headers=unique_user.token,
    )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    recipe_done_events = [e for e in events if e["event"] == "recipe_done"]

    assert len(recipe_done_events) == 1
    slug = recipe_done_events[0]["data"]["recipe_slug"]

    recipe = api_client.get(api_routes.recipes_slug(slug), headers=unique_user.token).json()
    extras = recipe.get("extras", {})
    assert extras.get("ingest_source") == "paste"
    assert "ingest_at" in extras
    assert extras.get("ingest_chunk_index") == "0"
