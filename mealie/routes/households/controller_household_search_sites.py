from functools import cached_property

from fastapi import HTTPException, status

from mealie.routes._base.base_controllers import BaseUserController
from mealie.routes._base.controller import controller
from mealie.routes._base.routers import UserAPIRouter
from mealie.schema.household.search_sites import (
    HouseholdSearchSiteCreate,
    HouseholdSearchSiteOut,
    HouseholdSearchSiteSave,
    HouseholdSearchSiteUpdate,
)
from mealie.schema.response.responses import SuccessResponse
from mealie.services.household_services.recipe_hunt_service import RecipeHuntService

router = UserAPIRouter(prefix="/households/search-sites", tags=["Households: Search Sites"])


@controller(router)
class HouseholdSearchSitesController(BaseUserController):
    @cached_property
    def service(self) -> RecipeHuntService:
        return RecipeHuntService(self.group_id, self.household_id, self.repos)

    @router.get("", response_model=list[HouseholdSearchSiteOut])
    def get_all(self):
        """Returns all search sites for the current household."""
        return self.repos.household_search_sites.get_all()

    @router.post("", response_model=HouseholdSearchSiteOut, status_code=status.HTTP_201_CREATED)
    def create_one(self, data: HouseholdSearchSiteCreate):
        """Create a new search site for the current household."""
        self.checks.can_manage_household()
        return self.repos.household_search_sites.create(
            HouseholdSearchSiteSave(group_id=self.group_id, household_id=self.household_id, **data.model_dump())
        )

    # IMPORTANT: restore-defaults must be registered BEFORE /{item_id} routes to prevent
    # FastAPI from matching the literal string "restore-defaults" as a UUID parameter.
    @router.post("/restore-defaults", response_model=list[HouseholdSearchSiteOut])
    def restore_defaults(self):
        """Delete all search sites and reinsert the 7 canonical defaults."""
        self.checks.can_manage_household()
        return self.service.restore_defaults()

    @router.put("/{item_id}", response_model=HouseholdSearchSiteOut)
    def update_one(self, item_id: str, data: HouseholdSearchSiteUpdate):
        """Partially update enabled/is_blocked on a search site."""
        self.checks.can_manage_household()
        site = self.repos.household_search_sites.get_one(item_id)
        if not site:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Search site not found")
        # Use patch to only update fields that are explicitly set (skip None values)
        return self.repos.household_search_sites.patch(item_id, data.model_dump(exclude_none=True))

    @router.delete("/{item_id}", response_model=SuccessResponse)
    def delete_one(self, item_id: str):
        """Delete a search site."""
        self.checks.can_manage_household()
        site = self.repos.household_search_sites.get_one(item_id)
        if not site:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Search site not found")
        self.repos.household_search_sites.delete(item_id)
        return SuccessResponse.respond()
