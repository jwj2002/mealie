from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Mapped, mapped_column

from .._model_base import BaseMixins, FilterableColumn, SqlAlchemyBase
from .._model_utils.auto_init import auto_init
from .._model_utils.guid import GUID

if TYPE_CHECKING:
    from .household import Household


class HouseholdSearchSiteModel(SqlAlchemyBase, BaseMixins):
    __tablename__ = "household_search_sites"
    __table_args__ = (
        sa.UniqueConstraint("household_id", "domain", name="household_search_sites_household_id_domain_key"),
    )

    id: FilterableColumn[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    group_id: FilterableColumn[GUID] = mapped_column(GUID, sa.ForeignKey("groups.id"), nullable=False, index=True)
    household_id: FilterableColumn[GUID] = mapped_column(
        GUID, sa.ForeignKey("households.id"), nullable=False, index=True
    )
    household: Mapped[Optional["Household"]] = orm.relationship("Household", back_populates="search_sites")
    name: FilterableColumn[str] = mapped_column(sa.String, nullable=False)
    domain: FilterableColumn[str] = mapped_column(sa.String, nullable=False)
    enabled: FilterableColumn[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    is_blocked: FilterableColumn[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    is_default: FilterableColumn[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    position: FilterableColumn[int] = mapped_column(sa.Integer, default=0, nullable=False)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
