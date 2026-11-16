"""Create the users table.

Accounts of the system actors (RNF-03), linked to at most one coordinator,
department head or student profile according to their role.

Revision ID: d4cb330e67e9
Revises: c577513e20a7
Create Date: 2026-11-06 13:27:54.882474

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4cb330e67e9"
down_revision: str | Sequence[str] | None = "c577513e20a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the users table and its role ENUM type."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("administrador", "coordinador", "jefe", "estudiante", name="user_role"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("coordinator_id", sa.Integer(), nullable=True),
        sa.Column("department_head_id", sa.Integer(), nullable=True),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "(role = 'administrador' AND coordinator_id IS NULL"
            " AND department_head_id IS NULL AND student_id IS NULL)"
            " OR (role = 'coordinador' AND coordinator_id IS NOT NULL"
            " AND department_head_id IS NULL AND student_id IS NULL)"
            " OR (role = 'jefe' AND department_head_id IS NOT NULL"
            " AND coordinator_id IS NULL AND student_id IS NULL)"
            " OR (role = 'estudiante' AND student_id IS NOT NULL"
            " AND coordinator_id IS NULL AND department_head_id IS NULL)",
            name=op.f("ck_users_role_matches_profile"),
        ),
        sa.ForeignKeyConstraint(
            ["coordinator_id"],
            ["coordinators.id"],
            name=op.f("fk_users_coordinator_id_coordinators"),
        ),
        sa.ForeignKeyConstraint(
            ["department_head_id"],
            ["department_heads.id"],
            name=op.f("fk_users_department_head_id_department_heads"),
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"], name=op.f("fk_users_student_id_students")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("coordinator_id", name=op.f("uq_users_coordinator_id")),
        sa.UniqueConstraint("department_head_id", name=op.f("uq_users_department_head_id")),
        sa.UniqueConstraint("student_id", name=op.f("uq_users_student_id")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )


def downgrade() -> None:
    """Drop the users table and its role ENUM type."""
    op.drop_table("users")
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=False)
