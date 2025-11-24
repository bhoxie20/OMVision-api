from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from auth import get_current_user
from models import List as DBList, ListEntityAssociation
from database import get_db
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()


class DeleteListResponse(BaseModel):
    message: str


@router.post("/delete_lists/{list_id}", response_model=DeleteListResponse)
def delete_list(
    list_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        db_list = db.query(DBList).filter(DBList.id == list_id).first()

        if not db_list:
            raise HTTPException(status_code=404, detail="List not found.")

        db.query(ListEntityAssociation).filter(
            ListEntityAssociation.list_id == list_id
        ).delete(synchronize_session=False)

        db.delete(db_list)
        db.commit()

        return DeleteListResponse(message=f"List with id {list_id} has been deleted.")

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error occurred while deleting the list."
        )
