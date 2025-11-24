from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Literal
from auth import get_current_user
from models import List as DBList
from database import get_db
from sqlalchemy.exc import IntegrityError
from datetime import datetime

router = APIRouter()


class ListCreateRequest(BaseModel):
    name: str = Field(..., description="Name of the list")
    type: Literal["company", "person"] = Field(
        ..., description="Type of the list, must be 'company' or 'person'"
    )


class ListResponse(BaseModel):
    id: int
    name: str
    type: str

    class Config:
        from_attributes = True


@router.post("/lists", response_model=ListResponse)
def create_list(
    list_data: ListCreateRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):

    if list_data.type not in ["company", "person"]:
        raise HTTPException(
            status_code=400, detail="Invalid list type. Must be 'company' or 'person'."
        )

    existing_list = (
        db.query(DBList).filter_by(name=list_data.name, type=list_data.type).first()
    )
    if existing_list:
        raise HTTPException(
            status_code=400,
            detail=f"A {list_data.type} list with the name '{list_data.name}' already exists.",
        )

    new_list = DBList(
        name=list_data.name, type=list_data.type, created_at=datetime.now()
    )

    try:
        db.add(new_list)
        db.commit()
        db.refresh(new_list)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error occurred while creating the list."
        )

    return new_list
