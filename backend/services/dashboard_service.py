"""
Dashboard business logic — aggregation queries.

All queries use SQLAlchemy Core (select + func) rather than ORM
for performance. Aggregation queries don't need ORM object hydration.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from backend.models.department import Department
from backend.models.ticket import Ticket, TicketStatus
from backend.models.user import User


class DashboardService:

    def __init__(self, db: Session) -> None:
        self.db = db

    # =====================================================
    # Summary counts
    # =====================================================

    def get_summary(self) -> dict:
        """
        Returns total counts per status and average resolution time.
        """
        # Count tickets grouped by status
        status_counts = self.db.execute(
            select(Ticket.status, func.count(Ticket.id).label("count")).group_by(Ticket.status)
        ).all()

        counts = {row.status.value: row.count for row in status_counts}

        # Average resolution time in hours (only resolved/closed tickets)
        avg_result = self.db.execute(
            select(
                func.avg(
                    func.extract("epoch", Ticket.resolved_at - Ticket.created_at) / 3600
                ).label("avg_hours")
            ).where(Ticket.resolved_at.isnot(None))
        ).scalar()

        return {
            "open": counts.get("open", 0),
            "in_progress": counts.get("in_progress", 0),
            "resolved": counts.get("resolved", 0),
            "closed": counts.get("closed", 0),
            "reopened": counts.get("reopened", 0),
            "total": sum(counts.values()),
            "avg_resolution_hours": round(float(avg_result), 2) if avg_result else None,
        }

    # =====================================================
    # Monthly trends
    # =====================================================

    def get_monthly_trends(self) -> list[dict]:
        """
        Ticket counts grouped by month for the last 6 months.
        """
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)

        rows = self.db.execute(
            select(
                func.date_trunc("month", Ticket.created_at).label("month"),
                func.count(Ticket.id).label("count"),
            )
            .where(Ticket.created_at >= six_months_ago)
            .group_by("month")
            .order_by("month")
        ).all()

        return [
            {
                "month": row.month.strftime("%Y-%m"),
                "count": row.count,
            }
            for row in rows
        ]

    # =====================================================
    # SLA stats by department
    # =====================================================

    def get_sla_stats(self) -> list[dict]:
        """
        SLA breach rate per department.
        """
        rows = self.db.execute(
            select(
                Department.name.label("department"),
                func.count(Ticket.id).label("total"),
                func.sum(case((Ticket.sla_breached == True, 1), else_=0)).label("breached"),
            )
            .join(Department, Ticket.department_id == Department.id)
            .group_by(Department.name)
            .order_by(Department.name)
        ).all()

        return [
            {
                "department": row.department,
                "total_tickets": row.total,
                "breached": int(row.breached),
                "breach_rate": round(row.breached / row.total * 100, 1) if row.total else 0,
            }
            for row in rows
        ]

    # =====================================================
    # Engineer performance
    # =====================================================

    def get_engineer_stats(self) -> list[dict]:
        """
        Tickets assigned and resolved per engineer.
        """
        rows = self.db.execute(
            select(
                User.full_name.label("engineer"),
                func.count(Ticket.id).label("assigned"),
                func.sum(
                    case((Ticket.status == TicketStatus.RESOLVED, 1), else_=0)
                    + case((Ticket.status == TicketStatus.CLOSED, 1), else_=0)
                ).label("resolved"),
            )
            .join(User, Ticket.assigned_to_id == User.id)
            .group_by(User.full_name)
            .order_by(func.count(Ticket.id).desc())
        ).all()

        return [
            {
                "engineer": row.engineer,
                "tickets_assigned": row.assigned,
                "tickets_resolved": int(row.resolved),
                "resolution_rate": (
                    round(row.resolved / row.assigned * 100, 1) if row.assigned else 0
                ),
            }
            for row in rows
        ]
