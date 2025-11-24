from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from auth import get_current_user
from database import get_db
from models import Company

router = APIRouter()


class CompanyRelevanceUpdate(BaseModel):
    id: int
    relevence_stage: str


@router.post("/edit_company_relevence", status_code=status.HTTP_200_OK)
async def edit_company_relevance(
    company_data: CompanyRelevanceUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        company = db.query(Company).filter(Company.id == company_data.id).first()

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        source_company_id = company.source_company_id

        db.query(Company).filter(Company.source_company_id == source_company_id).update(
            {Company.relevence_stage: company_data.relevence_stage},
            synchronize_session=False,
        )
        db.commit()

        return {
            "message": "Relevance stage updated successfully for all related companies"
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while updating the relevance stage.",
        )

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
