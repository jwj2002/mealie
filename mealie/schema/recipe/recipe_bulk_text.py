from pydantic import Field

from mealie.schema._mealie import MealieModel

MAX_TEXT_LENGTH = 500_000  # ~500 KB; bounds LLM cost per request


class BulkIngestText(MealieModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
