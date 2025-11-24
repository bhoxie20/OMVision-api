from fastapi import Depends, APIRouter, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Company, Person, Signal
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import date, datetime
from pydantic.fields import Field
from typing import Any

router = APIRouter()


class SourceData(BaseModel):
    sender: Optional[str] = None
    date: Optional[str] = None
    body: Optional[str] = None


class NerTags(BaseModel):
    person: Optional[Dict[str, str]] = Field(default_factory=dict)
    org: Optional[Dict[str, str]] = Field(default_factory=dict)
    gpe: Optional[Dict[str, str]] = Field(default_factory=dict)


class Document(BaseModel):
    name: Optional[str] = None
    id: Optional[int] = None
    source_company_ids: Optional[List[str]] = Field(default_factory=list)
    source_people_ids: Optional[List[str]] = None
    updated_at: Optional[datetime] = None
    source_id: Optional[int] = None
    source_data: Optional[SourceData] = None
    ner_tags: Optional[NerTags] = None
    created_at: Optional[datetime] = None


@router.get("/signals")
def get_signals(
    skip: int = 0,
    limit: int = 50,
    name: Optional[str] = None,
    created_at: Optional[date] = Query(
        None, description="Filter people by creation date"
    ),
    _=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(Signal).order_by(Signal.created_at.desc())

        if name:
            query = query.filter(
                or_(
                    Signal.name.ilike(f"%{name}%"),
                )
            )

        if created_at:
            query = query.filter(
                func.date(Signal.created_at) == created_at  # Filter by date
            )

        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        result = query.all()

        return result

    except SQLAlchemyError as e:
        print(f"SQLAlchemyError: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
