"""SQLAlchemy models.

Imported here so Alembic can detect them when autogenerating migrations.
"""

from app.models.academic_program import (
    AcademicProgram,
    Coordinator,
    CoordinatorProgram,
    DepartmentHead,
    ProgramSubject,
    Student,
    StudentProgram,
    Subject,
)
from app.models.analytics import (
    ANALYTICS_SCHEMA,
    DimBlock,
    DimClassroom,
    DimGroup,
    DimTime,
    DimTimeSlot,
    FactBlockAttendance,
    FactChangeRequest,
    FactClassroomOccupancy,
)
from app.models.calendar import Classroom, Semester, TimeSlot
from app.models.change_request import ChangeRequest
from app.models.content_block import ContentBlock
from app.models.enums import (
    ActivityType,
    AttendanceStatus,
    ChangeRequestStatus,
    ComplexityLevel,
    ReviewDecision,
    UserRole,
    Weekday,
)
from app.models.schedule import Attendance, Schedule, ScheduleSession, StudentScheduleAssignment
from app.models.user import User

__all__ = [
    "ANALYTICS_SCHEMA",
    "AcademicProgram",
    "ActivityType",
    "Attendance",
    "AttendanceStatus",
    "ChangeRequest",
    "ChangeRequestStatus",
    "Classroom",
    "ComplexityLevel",
    "ContentBlock",
    "Coordinator",
    "CoordinatorProgram",
    "DepartmentHead",
    "DimBlock",
    "DimClassroom",
    "DimGroup",
    "DimTime",
    "DimTimeSlot",
    "FactBlockAttendance",
    "FactChangeRequest",
    "FactClassroomOccupancy",
    "ProgramSubject",
    "ReviewDecision",
    "Schedule",
    "ScheduleSession",
    "Semester",
    "Student",
    "StudentProgram",
    "StudentScheduleAssignment",
    "Subject",
    "TimeSlot",
    "User",
    "UserRole",
    "Weekday",
]
