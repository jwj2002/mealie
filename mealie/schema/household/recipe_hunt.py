from mealie.schema._mealie import MealieModel


class HuntSearchRequest(MealieModel):
    query: str
    count: int = 10
    offset: int = 0


class SearchSiteResult(MealieModel):
    title: str
    url: str
    description: str | None = None
    is_blocked_site: bool = False


class HuntSearchResponse(MealieModel):
    query: str
    results: list[SearchSiteResult]
    truncated_to_max_sites: bool = False
