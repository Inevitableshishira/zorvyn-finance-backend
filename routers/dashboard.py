from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from collections import defaultdict

from database import get_db
from models import User, FinancialRecord, RecordType
from schemas import DashboardSummary, CategoryTotal, MonthlyTrend, RecordOut
from dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Full dashboard summary: totals, category breakdown, recent activity, monthly trends.
    All authenticated users can access.
    """
    active_records = db.query(FinancialRecord).filter(
        FinancialRecord.is_deleted == False
    ).all()

    # ── Core totals ──────────────────────────────────────────────────────────
    total_income = sum(r.amount for r in active_records if r.type == RecordType.income)
    total_expenses = sum(r.amount for r in active_records if r.type == RecordType.expense)
    net_balance = total_income - total_expenses

    # ── Category totals ──────────────────────────────────────────────────────
    category_map: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "count": 0})
    for r in active_records:
        category_map[r.category]["total"] += r.amount
        category_map[r.category]["count"] += 1

    category_totals = [
        CategoryTotal(category=cat, total=round(data["total"], 2), count=data["count"])
        for cat, data in sorted(category_map.items(), key=lambda x: -x[1]["total"])
    ]

    # ── Recent 10 records ────────────────────────────────────────────────────
    recent = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.is_deleted == False)
        .order_by(FinancialRecord.date.desc())
        .limit(10)
        .all()
    )

    # ── Monthly trends (last 6 months) ───────────────────────────────────────
    monthly: dict[str, dict] = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for r in active_records:
        key = r.date.strftime("%Y-%m")
        if r.type == RecordType.income:
            monthly[key]["income"] += r.amount
        else:
            monthly[key]["expenses"] += r.amount

    monthly_trends = [
        MonthlyTrend(
            month=month,
            income=round(data["income"], 2),
            expenses=round(data["expenses"], 2),
            net=round(data["income"] - data["expenses"], 2),
        )
        for month, data in sorted(monthly.items())[-6:]
    ]

    return DashboardSummary(
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        net_balance=round(net_balance, 2),
        total_records=len(active_records),
        category_totals=category_totals,
        recent_records=recent,
        monthly_trends=monthly_trends,
    )


@router.get("/by-category", response_model=list[CategoryTotal])
def get_by_category(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Category-wise totals, sorted by amount descending. All authenticated users."""
    records = db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False).all()
    category_map: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "count": 0})
    for r in records:
        category_map[r.category]["total"] += r.amount
        category_map[r.category]["count"] += 1

    return [
        CategoryTotal(category=cat, total=round(data["total"], 2), count=data["count"])
        for cat, data in sorted(category_map.items(), key=lambda x: -x[1]["total"])
    ]


@router.get("/trends", response_model=list[MonthlyTrend])
def get_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Monthly income vs expense trends for all time. All authenticated users."""
    records = db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False).all()
    monthly: dict[str, dict] = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for r in records:
        key = r.date.strftime("%Y-%m")
        if r.type == RecordType.income:
            monthly[key]["income"] += r.amount
        else:
            monthly[key]["expenses"] += r.amount

    return [
        MonthlyTrend(
            month=month,
            income=round(data["income"], 2),
            expenses=round(data["expenses"], 2),
            net=round(data["income"] - data["expenses"], 2),
        )
        for month, data in sorted(monthly.items())
    ]
