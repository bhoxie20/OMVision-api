from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Search
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from pydantic import BaseModel
from typing import Any
from datetime import datetime


router = APIRouter()


class SearchResponse(BaseModel):
    source_id: int
    name: Any
    updated_at: datetime
    source_company_ids: Optional[List[str]] = []
    source_people_ids: Optional[List[str]] = []
    id: int
    created_at: datetime


@router.get("/searches", response_model=List[SearchResponse])
def get_searches(
    skip: int = 0,
    limit: int = 50,
    _=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        searches_query = (
            db.query(Search)
            .order_by(Search.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        searches = []
        for search in searches_query:
            searches.append(search)

        return searches

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
