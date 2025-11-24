import traceback
from fastapi import Depends, APIRouter, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict
from pydantic import BaseModel, HttpUrl
from datetime import date, datetime
from auth import get_current_user
from database import get_db
from models import ListEntityAssociation, Person, List as DBList, Signal, Source

router = APIRouter()


class Highlight(BaseModel):
    category: Optional[str] = None
    date_added: Optional[str] = None
    text: Optional[str] = None
    company_urn: Optional[str] = None


class Location(BaseModel):
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class School(BaseModel):
    name: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    entity_urn: Optional[str] = None


class SaveList(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None


class Education(BaseModel):
    school: Optional[School] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    grade: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class SocialMedia(BaseModel):
    url: Optional[HttpUrl] = None
    follower_count: Optional[int] = None
    username: Optional[str] = None
    status: Optional[str] = None


class Experience(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current_position: Optional[bool] = None
    location: Optional[str] = None
    role_type: Optional[str] = None
    company_name: Optional[str] = None


class AllPersonResponse(BaseModel):
    id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    source_name: Optional[str] = None
    linkedin_headline: Optional[str] = None
    profile_picture_url: Optional[HttpUrl] = None
    location: Optional[Location] = None
    highlights: Optional[List[Highlight]] = None
    education: Optional[List[Education]] = None
    socials: Optional[Dict[str, SocialMedia]] = None
    experience: Optional[List[Experience]] = None
    awards: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    added_at: Optional[datetime] = None  # New Field
    comments: Optional[str] = None
    relevence_stage: Optional[str] = None
    lists: Optional[List[SaveList]] = None

    class Config:
        from_attributes = True


def fetch_people(
    db: Session,
    name: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    list_id: Optional[int] = None,
    created_at: Optional[date] = None,
    source_name: Optional[str] = None,
) -> List[Dict]:
    try:
        # Subquery to aggregate lists associated with each person
        list_subquery = (
            select(
                ListEntityAssociation.entity_id.label("person_id"),
                func.json_agg(
                    func.json_build_object("id", DBList.id, "name", DBList.name)
                ).label("lists"),
            )
            .join(DBList, ListEntityAssociation.list_id == DBList.id)
            .where(ListEntityAssociation.entity_type == "person")
            .group_by(ListEntityAssociation.entity_id)
            .subquery()
        )

        people_subquery = (
            db.query(func.max(Person.id).label("id"))
            .filter(
                and_(Person.source_person_id.isnot(None), Person.source_person_id != 0)
            )
            .filter(or_(Person.is_hidden == False, Person.is_hidden.is_(None)))
            .group_by(Person.source_person_id)
            .subquery()
        )

        # Base query to fetch persons and their associated lists
        query = (
            db.query(
                people_subquery.c.id,
                Person,
                list_subquery.c.lists,
                Source.name.label("source_name"),
            )
            .join(Person, Person.id == people_subquery.c.id)
            .outerjoin(Signal, Person.signal_id == Signal.id)
            .outerjoin(Source, Signal.source_id == Source.id)
            .outerjoin(list_subquery, Person.id == list_subquery.c.person_id)
            .order_by(Person.created_at.desc(), Person.first_name.asc())
        )

        # Filter by name if provided
        if name:
            query = query.filter(
                or_(
                    Person.first_name.ilike(f"%{name}%"),
                    Person.last_name.ilike(f"%{name}%"),
                )
            )

        # Filter by source_name if provided
        if source_name:
            query = query.filter(Source.name == source_name)

        # If list_id is provided, join and filter by it
        if list_id is not None:
            query = query.join(
                ListEntityAssociation,
                and_(
                    Person.id == ListEntityAssociation.entity_id,
                    ListEntityAssociation.entity_type == "person",
                ),
            ).filter(ListEntityAssociation.list_id == list_id)

        if created_at:
            query = query.filter(
                func.date(Person.created_at) == created_at  # Filter by date
            )

        # Apply pagination
        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        result = query.all()

        serialized_result = []
        for _, person, lists, source in result:
            # Initialize the person dictionary with necessary fields
            person_dict = {
                "id": person.id,
                "first_name": person.first_name,
                "last_name": person.last_name,
                "source_name": source,
                "linkedin_headline": person.linkedin_headline,
                "profile_picture_url": person.profile_picture_url,
                "location": person.location,
                "highlights": person.highlights,
                "education": person.education,
                "socials": person.socials,
                "experience": person.experience,
                "awards": person.awards,
                "created_at": person.created_at,
                "comments": person.comments,
                "relevence_stage": person.relevence_stage,
                "lists": lists,
                "added_at": None,  # Default to None
            }

            # If list_id is provided, fetch added_at
            if list_id:
                added_at = (
                    db.query(ListEntityAssociation.created_at)
                    .filter(
                        ListEntityAssociation.entity_id == person.id,
                        ListEntityAssociation.list_id == list_id,
                        ListEntityAssociation.entity_type == "person",
                    )
                    .scalar()
                )
                person_dict["added_at"] = added_at

            serialized_result.append(person_dict)

        return serialized_result

    except SQLAlchemyError as e:
        traceback_str = traceback.format_exc()
        print(f"SQLAlchemyError: {str(e)}\n{traceback_str}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
    except Exception as e:
        traceback_str = traceback.format_exc()
        print(f"Exception: {str(e)}\n{traceback_str}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get("/people", response_model=List[AllPersonResponse])
def get_or_search_people(
    name: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    list_id: Optional[int] = None,
    created_at: Optional[date] = Query(
        None, description="Filter people by creation date"
    ),
    source_name: Optional[str] = None,
    _=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return fetch_people(db, name, skip, limit, list_id, created_at, source_name)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )
