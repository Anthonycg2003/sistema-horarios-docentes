"""System accounts and their link to the domain people."""

import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import UserRole, db_enum


class User(Base):
    """Login account of a system actor (RNF-03).

    An account is either an administrator, who has no domain profile, or the
    account of exactly one coordinator, department head or student. The role
    and the profile column that is set must agree, and each profile has at
    most one account. The display name comes from the profile.
    """

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "(role = 'administrador' AND coordinator_id IS NULL"
            " AND department_head_id IS NULL AND student_id IS NULL)"
            " OR (role = 'coordinador' AND coordinator_id IS NOT NULL"
            " AND department_head_id IS NULL AND student_id IS NULL)"
            " OR (role = 'jefe' AND department_head_id IS NOT NULL"
            " AND coordinator_id IS NULL AND student_id IS NULL)"
            " OR (role = 'estudiante' AND student_id IS NOT NULL"
            " AND coordinator_id IS NULL AND department_head_id IS NULL)",
            name="role_matches_profile",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(db_enum(UserRole, "user_role"))
    is_active: Mapped[bool] = mapped_column(server_default="true")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    coordinator_id: Mapped[int | None] = mapped_column(
        ForeignKey("coordinators.id"), unique=True
    )
    department_head_id: Mapped[int | None] = mapped_column(
        ForeignKey("department_heads.id"), unique=True
    )
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"), unique=True)
