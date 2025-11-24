from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from auth import get_current_user
from models import Company
from database import get_db

router = APIRouter()


class HideCompaniesRequest(BaseModel):
    ids: List[int]


@router.post("/companies/hide")
def hide_companies(
    request: HideCompaniesRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        # Fetch the company name from the provided company ID
        company_to_hide = db.query(Company).filter(Company.id == request.ids[0]).first()

        if not company_to_hide:
            raise HTTPException(
                status_code=404,
                detail="No company found with the provided ID",
            )

        # Bulk update all companies with the same name
        result = (
            db.query(Company)
            .filter(Company.name == company_to_hide.name)
            .update({"is_hidden": True}, synchronize_session=False)
        )

        db.commit()

        if result == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No companies found with the name {company_to_hide.name}",
            )

        return {
            "message": f"Companies with name '{company_to_hide.name}' hidden successfully"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )
