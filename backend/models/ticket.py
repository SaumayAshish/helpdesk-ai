"""
Ticket ORM model.

Column names mirror database/migrations/006_create_tickets_table.sql exactly.
Any drift between this file and the real schema will cause runtime errors.
"""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin

# =====================================================
# Enums — values must match PostgreSQL enum literals exactly
# =====================================================


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =====================================================
# Ticket Model
# =====================================================


class Ticket(Base, TimestampMixin):
    """Maps to the 'tickets' table defined in 006_create_tickets_table.sql."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Human-friendly ticket number e.g. TKT-2026-00001
    ticket_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Status and priority
    # values_callable ensures SQLAlchemy stores .value ("open") not .name ("OPEN")
    status: Mapped[TicketStatus] = mapped_column(
        Enum(
            TicketStatus,
            name="ticket_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=TicketStatus.OPEN,
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(
            TicketPriority,
            name="ticket_priority",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=TicketPriority.MEDIUM,
    )

    # Foreign keys — names match the real DB columns exactly
    created_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_to_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    sla_policy_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # SLA tracking
    sla_breached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ML predictions — populated by ML service, null until then
    predicted_priority_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    predicted_sla_breach_prob: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    predicted_resolution_hours: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)

    # =====================================================
    # Relationships
    # =====================================================

    reporter = relationship("User", foreign_keys=[created_by_id], back_populates="reported_tickets")
    assignee = relationship(
        "User", foreign_keys=[assigned_to_id], back_populates="assigned_tickets"
    )
    department = relationship("Department", back_populates="tickets")
    comments = relationship(
        "Comment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="Comment.created_at",
    )

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} number={self.ticket_number} status={self.status}>"
