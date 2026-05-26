"""add household search sites

Revision ID: 0d274f56fb69
Revises: 2187537c52b8
Create Date: 2026-05-26 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types
from mealie.db.models._model_utils.guid import GUID

# revision identifiers, used by Alembic.
revision = "0d274f56fb69"
down_revision: str | None = "2187537c52b8"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

# Canonical default search sites — single source of truth shared with the service layer.
# The service imports this constant directly; the migration uses it inline to avoid circular imports.
DEFAULT_SEARCH_SITES: list[tuple[str, str]] = [
    ("cooking.nytimes.com", "NYT Cooking"),
    ("simplyrecipes.com", "Simply Recipes"),
    ("seriouseats.com", "Serious Eats"),
    ("bonappetit.com", "Bon Appétit"),
    ("budgetbytes.com", "Budget Bytes"),
    ("halfbakedharvest.com", "Half Baked Harvest"),
    ("smittenkitchen.com", "Smitten Kitchen"),
]


def generate_id() -> str:
    val = GUID.generate()
    dialect = op.get_bind().dialect
    return GUID.convert_value_to_guid(val, dialect)  # type: ignore


def upgrade():
    op.create_table(
        "household_search_sites",
        sa.Column("id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("group_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("household_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.Column("update_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("household_id", "domain", name="household_search_sites_household_id_domain_key"),
    )
    with op.batch_alter_table("household_search_sites", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_household_search_sites_group_id"), ["group_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_household_search_sites_household_id"), ["household_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_household_search_sites_created_at"), ["created_at"], unique=False)

    # Seed 7 default sites for every existing household
    conn = op.get_bind()
    households = conn.execute(sa.text("SELECT id, group_id FROM households")).fetchall()
    for household_id, group_id in households:
        for position, (domain, name) in enumerate(DEFAULT_SEARCH_SITES):
            conn.execute(
                sa.text(
                    "INSERT INTO household_search_sites "
                    "(id, group_id, household_id, name, domain, enabled, is_blocked, is_default, position) "
                    "VALUES (:id, :group_id, :household_id, :name, :domain, :enabled, :is_blocked, :is_default, :position)"
                ),
                {
                    "id": generate_id(),
                    "group_id": group_id,
                    "household_id": household_id,
                    "name": name,
                    "domain": domain,
                    "enabled": True,
                    "is_blocked": False,
                    "is_default": True,
                    "position": position,
                },
            )


def downgrade():
    with op.batch_alter_table("household_search_sites", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_household_search_sites_created_at"))
        batch_op.drop_index(batch_op.f("ix_household_search_sites_group_id"))
        batch_op.drop_index(batch_op.f("ix_household_search_sites_household_id"))

    op.drop_table("household_search_sites")
