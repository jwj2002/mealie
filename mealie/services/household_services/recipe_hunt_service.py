from urllib.parse import urlparse

import httpx
from pydantic import UUID4

from mealie.pkgs import safehttp
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.household.recipe_hunt import HuntSearchResponse, SearchSiteResult
from mealie.services._base_service import BaseService

# Canonical default search sites — referenced by migration and restore_defaults.
# domain, display name
DEFAULT_SEARCH_SITES: list[tuple[str, str]] = [
    ("cooking.nytimes.com", "NYT Cooking"),
    ("simplyrecipes.com", "Simply Recipes"),
    ("seriouseats.com", "Serious Eats"),
    ("bonappetit.com", "Bon Appétit"),
    ("budgetbytes.com", "Budget Bytes"),
    ("halfbakedharvest.com", "Half Baked Harvest"),
    ("smittenkitchen.com", "Smitten Kitchen"),
]

_MAX_SEARCH_SITES = 10
_BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


class RecipeHuntError(Exception):
    """Raised when the Brave Search API call fails."""

    ...


class BraveSearchClient:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def search(self, query: str, count: int, offset: int) -> dict:
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self._api_key,
        }
        params = {"q": query, "count": count, "offset": offset, "safesearch": "strict"}
        try:
            async with httpx.AsyncClient(transport=safehttp.AsyncSafeTransport(timeout=10)) as client:
                response = await client.get(_BRAVE_SEARCH_URL, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as exc:
            raise RecipeHuntError("Brave Search API timed out") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500:
                raise RecipeHuntError(f"Brave Search API error: {exc.response.status_code}") from exc
            raise


class RecipeHuntService(BaseService):
    def __init__(self, group_id: UUID4, household_id: UUID4, repos: AllRepositories) -> None:
        self.group_id = group_id
        self.household_id = household_id
        self.repos = repos
        super().__init__()

    async def search(self, query: str, count: int = 10, offset: int = 0) -> HuntSearchResponse:
        all_sites = self.repos.household_search_sites.get_all()
        enabled_sites = [s for s in all_sites if s.enabled and not s.is_blocked]

        truncated = len(enabled_sites) > _MAX_SEARCH_SITES
        top_sites = enabled_sites[:_MAX_SEARCH_SITES]

        site_filters = " OR ".join(f"site:{s.domain}" for s in top_sites)
        brave_query = f"{query} ({site_filters})" if site_filters else query

        if not self.settings.BRAVE_SEARCH_API_KEY:
            raise RecipeHuntError("BRAVE_SEARCH_API_KEY is not configured")

        raw = await BraveSearchClient(self.settings.BRAVE_SEARCH_API_KEY).search(brave_query, count, offset)

        blocked_domains = {s.domain for s in all_sites if s.is_blocked}
        results = []
        for item in raw.get("web", {}).get("results", []):
            url = item.get("url", "")
            domain = urlparse(url).hostname or ""
            # strip www. prefix for matching
            domain = domain.removeprefix("www.")
            results.append(
                SearchSiteResult(
                    title=item.get("title", ""),
                    url=url,
                    description=item.get("description"),
                    is_blocked_site=domain in blocked_domains,
                )
            )

        return HuntSearchResponse(query=query, results=results, truncated_to_max_sites=truncated)

    def restore_defaults(self) -> list:
        """Delete all search sites for this household and reinsert the canonical 7 defaults."""
        all_sites = self.repos.household_search_sites.get_all()
        for site in all_sites:
            self.repos.household_search_sites.delete(site.id)

        from mealie.schema.household.search_sites import HouseholdSearchSiteSave

        created = []
        for position, (domain, name) in enumerate(DEFAULT_SEARCH_SITES):
            site = self.repos.household_search_sites.create(
                HouseholdSearchSiteSave(
                    group_id=self.group_id,
                    household_id=self.household_id,
                    name=name,
                    domain=domain,
                    enabled=True,
                    is_blocked=False,
                    is_default=True,
                    position=position,
                )
            )
            created.append(site)
        return created
