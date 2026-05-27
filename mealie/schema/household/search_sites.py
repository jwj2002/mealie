from pydantic import UUID4, ConfigDict

from mealie.schema._mealie import MealieModel


class HouseholdSearchSiteCreate(MealieModel):
    name: str
    domain: str
    enabled: bool = True
    is_blocked: bool = False
    is_default: bool = False
    position: int = 0


class HouseholdSearchSiteSave(HouseholdSearchSiteCreate):
    group_id: UUID4
    household_id: UUID4


class HouseholdSearchSiteUpdate(MealieModel):
    enabled: bool | None = None
    is_blocked: bool | None = None


class HouseholdSearchSiteOut(HouseholdSearchSiteCreate):
    id: UUID4
    group_id: UUID4
    household_id: UUID4
    model_config = ConfigDict(from_attributes=True)
