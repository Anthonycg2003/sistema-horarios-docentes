"""Academic program, subject and the people related to programs."""

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AcademicProgram(Base):
    """Academic program with its study plan."""

    __tablename__ = "academic_programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    study_plan: Mapped[str] = mapped_column(String(120))


class Subject(Base):
    """Subject addressed by content blocks."""

    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))


class Coordinator(Base):
    """Academic coordinator."""

    __tablename__ = "coordinators"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    specialty: Mapped[str] = mapped_column(String(120))


class CoordinatorProgram(Base):
    """Authorization of a coordinator to generate or validate schedules of a program."""

    __tablename__ = "coordinator_program"
    __table_args__ = (
        CheckConstraint("can_generate OR can_validate", name="grants_capability"),
    )

    coordinator_id: Mapped[int] = mapped_column(
        ForeignKey("coordinators.id"), primary_key=True
    )
    program_id: Mapped[int] = mapped_column(
        ForeignKey("academic_programs.id"), primary_key=True, index=True
    )
    can_generate: Mapped[bool]
    can_validate: Mapped[bool]


class Student(Base):
    """Student, with the group they belong to."""

    __tablename__ = "students"
    __table_args__ = (CheckConstraint("age > 0", name="age_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    age: Mapped[int]
    group_name: Mapped[str] = mapped_column(String(40), index=True)


class StudentProgram(Base):
    """Enrollment of a student in an academic program."""

    __tablename__ = "student_program"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), primary_key=True)
    program_id: Mapped[int] = mapped_column(
        ForeignKey("academic_programs.id"), primary_key=True, index=True
    )


class DepartmentHead(Base):
    """Department head who reviews generated schedules."""

    __tablename__ = "department_heads"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
