from functools import cached_property

from fastapi import HTTPException, status

from mealie.routes._base.base_controllers import BaseUserController
from mealie.routes._base.controller import controller
from mealie.routes._base.routers import UserAPIRouter
from mealie.schema.household.recipe_hunt import HuntSearchRequest, HuntSearchResponse
from mealie.services.household_services.recipe_hunt_service import RecipeHuntError, RecipeHuntService

router = UserAPIRouter(prefix="/recipes/hunt", tags=["Recipe: Hunt"])


@controller(router)
class RecipeHuntController(BaseUserController):
    @cached_property
    def service(self) -> RecipeHuntService:
        return RecipeHuntService(self.group_id, self.household_id, self.repos)

    @router.post("/search", response_model=HuntSearchResponse)
    async def hunt_search(self, body: HuntSearchRequest):
        """Search for recipes via Brave Search. Returns 503 when BRAVE_SEARCH_API_KEY is not set."""
        if not self.settings.BRAVE_SEARCH_API_KEY:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Recipe Hunt is not available: BRAVE_SEARCH_API_KEY is not configured",
            )
        try:
            return await self.service.search(body.query, body.count, body.offset)
        except RecipeHuntError as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
