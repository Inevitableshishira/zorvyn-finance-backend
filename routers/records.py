from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import User, FinancialRecord, Role, RecordType
from schemas import RecordCreate, RecordUpdate, RecordOut
from dependencies import get_current_user, require_analyst_or_above, require_admin

router = APIRouter(prefix="/records", tags=["Financial Records"])


@router.post("", response_model=RecordOut, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: RecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_above),
):
    """Create a financial record. Analyst and Admin only."""
    record = FinancialRecord(**payload.model_dump(), owner_id=current_user.id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=List[RecordOut])
def list_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    record_type: Optional[RecordType] = Query(None, description="Filter by type: income or expense"),
    category: Optional[str] = Query(None, description="Filter by category name"),
    date_from: Optional[datetime] = Query(None, description="Filter records from this date (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Filter records up to this date (ISO 8601)"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    List financial records with optional filters.
    All authenticated users can view records.
    """
    query = db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)

    if record_type:
        query = query.filter(FinancialRecord.type == record_type)
    if category:
        query = query.filter(FinancialRecord.category.ilike(f"%{category}%"))
    if date_from:
        query = query.filter(FinancialRecord.date >= date_from)
    if date_to:
        query = query.filter(FinancialRecord.date <= date_to)

    return query.order_by(FinancialRecord.date.desc()).offset(offset).limit(limit).all()


@router.get("/{record_id}", response_model=RecordOut)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single record by ID. All authenticated users can view."""
    record = db.query(FinancialRecord).filter(
        FinancialRecord.id == record_id,
        FinancialRecord.is_deleted == False,
    ).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record


@router.patch("/{record_id}", response_model=RecordOut)
def update_record(
    record_id: int,
    payload: RecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_above),
):
    """
    Update a financial record. Analyst and Admin only.
    Analysts can only update records they created; Admins can update any.
    """
    record = db.query(FinancialRecord).filter(
        FinancialRecord.id == record_id,
        FinancialRecord.is_deleted == False,
    ).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    if current_user.role == Role.analyst and record.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analysts can only update their own records",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Soft-delete a financial record. Admin only."""
    record = db.query(FinancialRecord).filter(
        FinancialRecord.id == record_id,
        FinancialRecord.is_deleted == False,
    ).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    record.is_deleted = True
    db.commit()
