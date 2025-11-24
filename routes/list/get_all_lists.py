from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from auth import get_current_user
from models import List as DBList
from pydantic import BaseModel
from database import get_db

router = APIRouter()


class ListDetailResponse(BaseModel):
    id: int
    name: str
    type: str

    class Config:
        from_attributes = True


@router.get("/lists", response_model=Optional[List[ListDetailResponse]])
def get_all_lists(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    lists = db.query(DBList).all()
    return lists
