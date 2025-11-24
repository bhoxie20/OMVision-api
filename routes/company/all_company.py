from fastapi import Depends, APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
import traceback
from datetime import date, datetime
import requests
from sqlalchemy import func, or_, select, and_
from config import settings
from database import get_db
from auth import get_current_user
from models import (
    Company,
    CompanyMetric,
    Signal,
    Source,
    List as DBList,
    ListEntityAssociation,
)

router = APIRouter()

FOUNDING_TITLES = {
    "founder",
    "co-founder",
    "ceo",
    "coo",
    "cto",
    "chief executive officer",
    "chief operations officer",
    "chief technology officer",
}


class KeyEmployee(BaseModel):
    person: Optional[str] = None
    title: Optional[str] = None
    entityUrn: Optional[str] = None


class Investor(BaseModel):
    name: Optional[str] = None
    entity_urn: Optional[str] = None


class SaveList(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None


class AllCompanyResponse(BaseModel):
    id: int
    name: Optional[str] = None
    website_urls: Optional[HttpUrl] = None
    description: Optional[str] = None
    location: Optional[str] = None
    source_name: Optional[str] = None
    source_text: Optional[str] = None
    created_at: Optional[datetime] = None
    investors: Optional[List[Investor]] = None
    most_recent_round: Optional[str] = None
    most_recent_round_size: Optional[int] = None
    key_employees: Optional[List[KeyEmployee]] = None
    comments: Optional[str] = None
    relevence_stage: Optional[str] = None
    is_hidden: Optional[bool] = None
    lists: Optional[List[SaveList]] = None
    added_at: Optional[datetime] = None
    rank: Optional[int] = None

    class Config:
        from_attributes = True


def make_harmonic_request(query, variables=None):
    url = "https://api.harmonic.ai/graphql"
    headers = {"Content-Type": "application/json", "apikey": settings.harmonic_api_key}
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Harmonic API request failed with status code {response.status_code}: {response.text}",
        )

    return response.json()


def get_all_employees(employee_ids):
    query = """
        query Query($getPersonByIdsIds: [Int!]!) {
            getPersonsByIds(ids: $getPersonByIdsIds) {
                fullName
                profilePictureUrl
                entityUrn
                socials {
                    linkedin {
                        url
                    }
                }
            }
        }
    """
    variables = {"getPersonByIdsIds": employee_ids}
    return make_harmonic_request(query, variables)


def parse_company_data(rows, harmonic_data, list_id=None):
    companies_data = []

    for i, row in enumerate(rows):
        try:
            data = {column: getattr(row, column) for column in row._fields}
            employees = data.get("employees", [])

            unique_employees = set()
            key_employees = []
            if employees and isinstance(employees, list):
                for employee in employees:
                    if employee and isinstance(employee, dict):
                        if (employee.get("role_type", "") == "FOUNDER") or any(
                            key_title in (employee.get("title", "") or "").lower()
                            for key_title in FOUNDING_TITLES
                        ):
                            entityUrn = employee.get("person")
                            if harmonic_data and isinstance(harmonic_data, list):
                                h_employee = next(
                                    (
                                        h
                                        for h in harmonic_data
                                        if h.get("entityUrn") == entityUrn
                                    ),
                                    None,
                                )
                                if h_employee:
                                    employee_name = h_employee.get("fullName", "-")
                                    if (
                                        employee_name
                                        and employee_name not in unique_employees
                                        and employee_name != "-"
                                    ):
                                        unique_employees.add(employee_name)
                                        key_employees.append(
                                            {
                                                "person": employee_name,
                                                "title": employee.get("title", "-"),
                                                "entityUrn": entityUrn,
                                            }
                                        )
            data["key_employees"] = key_employees

            if harmonic_data is None:
                harmonic_data = []

            for employee in key_employees:
                entityUrn = employee["person"]
                h_employee = next(
                    (h for h in harmonic_data if h["entityUrn"] == entityUrn), None
                )
                if h_employee:
                    employee["entityUrn"] = entityUrn
                    employee["person"] = h_employee["fullName"]

            location = data.get("location", {})
            data["location"] = (
                ", ".join(str(value) for value in location.values() if value)
                if isinstance(location, dict)
                else ""
            )

            website_urls = data.get("website_urls", {})
            data["website_urls"] = website_urls.get("url", "")

            investors = [
                {"name": investor["name"], "entity_urn": investor["entity_urn"]}
                for investor in data.get("funding", {}).get("investors", [])
            ]
            data["investors"] = investors

            funding_data = data.get("funding", {}) or {}
            investors = [
                {
                    "name": investor.get("name", "-"),
                    "entity_urn": investor.get("entity_urn", "-"),
                }
                for investor in funding_data.get("investors", [])
                if investor and isinstance(investor, dict)
            ]
            data["investors"] = investors

            data["most_recent_round"] = funding_data.get("last_funding_at", "-")
            if data["most_recent_round"] and data["most_recent_round"] != "-":
                try:
                    data["most_recent_round"] = str(data["most_recent_round"])
                except (ValueError, TypeError):
                    data["most_recent_round"] = "-"

            data["most_recent_round_size"] = funding_data.get("last_funding_total", 0.0)
            try:
                data["most_recent_round_size"] = float(
                    data["most_recent_round_size"] or 0.0
                )
            except (ValueError, TypeError):
                data["most_recent_round_size"] = 0.0

            if list_id is not None:
                data["added_at"] = row.added_at
            data["rank"] = data.get("rank")
            companies_data.append(data)

        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing expected data field: {e}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error parsing company data: {str(e)}",
            )

    return companies_data


def search_companies_by_name(
    db: Session,
    name: Optional[str],
    skip: int = 0,
    limit: int = 10,
    list_id: Optional[int] = None,
    created_at: Optional[date] = None,
    source_name: Optional[str] = None,
):
    try:
        # Subquery to aggregate lists associated with each company, including added_at
        list_subquery = (
            select(
                ListEntityAssociation.entity_id.label("company_id"),
                func.json_agg(
                    func.json_build_object("id", DBList.id, "name", DBList.name)
                ).label("lists"),
                func.min(ListEntityAssociation.created_at).label("added_at"),
            )
            .join(DBList, ListEntityAssociation.list_id == DBList.id)
            .where(
                and_(
                    ListEntityAssociation.entity_type == "company",
                    or_(
                        list_id is None,
                        ListEntityAssociation.list_id
                        == list_id,  # Filter for specific list_id if provided
                    ),
                )
            )
            .group_by(ListEntityAssociation.entity_id)
            .subquery()
        )

        # Subquery to filter unique companies based on source_company_id
        company_subquery = (
            db.query(
                func.max(Company.id).label("id"),
                func.max(Company.created_at).label("created_at"),
                func.max(Company.name).label("name"),
            )
            .filter(
                and_(
                    Company.source_company_id.isnot(None),
                    Company.source_company_id != 0,
                    Company.name.isnot(None),
                )
            )
            .filter(or_(Company.is_hidden == False, Company.is_hidden.is_(None)))
            .group_by(Company.source_company_id)
            .subquery()
        )

        # Main query to fetch companies with their metrics and list associations
        query = (
            db.query(
                company_subquery.c.id,
                company_subquery.c.created_at,
                company_subquery.c.name,
                Company.source_company_id,
                Company.website_urls,
                Company.description,
                Company.location,
                Company.comments,
                Company.relevence_stage,
                Company.is_hidden,
                Company.rank,
                CompanyMetric.employees,
                CompanyMetric.funding,
                CompanyMetric.funding_rounds,
                Source.name.label("source_name"),
                list_subquery.c.lists,
                list_subquery.c.added_at,  # Fetch the added_at for the specific list_id
            )
            .join(Company, Company.id == company_subquery.c.id)
            .join(CompanyMetric, Company.id == CompanyMetric.company_id)
            .outerjoin(Signal, Company.signal_id == Signal.id)
            .outerjoin(Source, Signal.source_id == Source.id)
            .outerjoin(list_subquery, Company.id == list_subquery.c.company_id)
            .order_by(
                company_subquery.c.created_at.desc(), company_subquery.c.name.asc()
            )
        )

        # Filter by name if provided
        if name:
            query = query.filter(
                or_(
                    Company.name.ilike(f"%{name}%"),
                    Company.legal_name.ilike(f"%{name}%"),
                    Company.name_aliases.any(name),
                )
            )

        # Filter by source_name if provided
        if source_name:
            query = query.filter(Source.name == source_name)

        # Filter by list_id if provided
        if list_id is not None:
            query = query.join(
                ListEntityAssociation, Company.id == ListEntityAssociation.entity_id
            ).filter(
                and_(
                    ListEntityAssociation.entity_type == "company",
                    ListEntityAssociation.list_id
                    == list_id,  # Filter for specific list_id
                )
            )

        if created_at:
            query = query.filter(
                func.date(Company.created_at) == created_at  # Filter by date
            )

        # Apply pagination
        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        return query.all()

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get("/companies", response_model=List[AllCompanyResponse])
def get_companies(
    name: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    list_id: Optional[int] = None,
    created_at: Optional[date] = Query(
        None, description="Filter people by creation date"
    ),
    source_name: Optional[str] = None,
    _=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        company_rows = search_companies_by_name(
            db, name, skip, limit, list_id, created_at, source_name
        )

        # Collect all employee IDs from the company rows
        all_employee_ids = []
        for row in company_rows:
            employees = row.employees or []
            key_employees = [
                int(employee["person"].split(":")[-1])
                for employee in employees
                if (employee.get("role_type", "") == "FOUNDER")
                or any(
                    key_title in employee.get("title", "").lower()
                    for key_title in FOUNDING_TITLES
                    if employee.get("title", "") != None
                )
            ]
            all_employee_ids.extend(key_employees)

        # Batch Harmonic API call
        harmonic_data = (
            get_all_employees(all_employee_ids)["data"]["getPersonsByIds"]
            if all_employee_ids
            else []
        )

        # Parse company data with harmonic employee data
        companies = parse_company_data(company_rows, harmonic_data, list_id)

        return companies

    except HTTPException as e:
        traceback.print_exc()
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )
