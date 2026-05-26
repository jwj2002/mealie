from enum import StrEnum
from typing import Literal

from pydantic import BaseModel

from mealie.schema._mealie import MealieModel


class ErrorResponse(BaseModel):
    message: str
    error: bool = True
    exception: str | None = None

    @classmethod
    def respond(cls, message: str, exception: str | None = None) -> dict:
        """
        This method is an helper to create an object and convert to a dictionary
        in the same call, for use while providing details to a HTTPException
        """
        return cls(message=message, exception=exception).model_dump()


class SuccessResponse(BaseModel):
    message: str
    error: bool = False

    @classmethod
    def respond(cls, message: str = "") -> dict:
        """
        This method is an helper to create an object and convert to a dictionary
        in the same call, for use while providing details to a HTTPException
        """
        return cls(message=message).model_dump()


class FileTokenResponse(MealieModel):
    file_token: str

    @classmethod
    def respond(cls, token: str) -> dict:
        """
        This method is an helper to create an object and convert to a dictionary
        in the same call, for use while providing details to a HTTPException
        """
        return cls(file_token=token).model_dump()


class SSEDataEventStatus(StrEnum):
    PROGRESS = "progress"
    DONE = "done"
    ERROR = "error"
    RECIPE_DONE = "recipe_done"


class SSEDataEventBase(BaseModel): ...


class SSEDataEventMessage(SSEDataEventBase):
    message: str


class SSEDataEventDone(SSEDataEventBase):
    slug: str


class SSEBulkRecipeDone(SSEDataEventBase):
    chunk_index: int
    total_chunks: int
    recipe_slug: str  # empty string "" when status == "failed"
    status: Literal["created", "failed"]


class SSEBulkIngestSummary(SSEDataEventBase):
    total: int
    succeeded: int
    failed: int
    truncated: bool  # True if input had >50 chunks; first 50 were processed
