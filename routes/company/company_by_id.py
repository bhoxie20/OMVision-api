from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy import case, distinct, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import Company, CompanyMetric
from database import get_db
from auth import get_current_user
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from config import settings
import requests


class Contact(BaseModel):
    emails: Optional[List[str]] = None
    phone_numbers: Optional[List[str]] = None
    exec_emails: Optional[List[str]] = None


class FoundingDate(BaseModel):
    date: Optional[str] = None
    granularity: Optional[str] = None


class WebsiteURLs(BaseModel):
    url: Optional[str] = None
    domain: Optional[str] = None
    is_broken: Optional[bool] = None


class Location(BaseModel):
    address_formatted: Optional[str] = None
    location: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    
    @validator('zip', pre=True, always=True)
    def ensure_zip_is_string(cls, value):
        if value is not None:
            return str(value)
        return value


class Tag(BaseModel):
    display_value: Optional[str] = None
    type: Optional[str] = None
    date_added: Optional[str] = None
    entity_urn: Optional[str] = None
    company_urn: Optional[str] = None


class SocialLink(BaseModel):
    url: Optional[str] = None
    follower_count: Optional[int] = None
    username: Optional[str] = None
    status: Optional[str] = None
    following_count: Optional[int] = None
    like_count: Optional[int] = None


class Socials(BaseModel):
    LINKEDIN: Optional[SocialLink] = None
    TWITTER: Optional[SocialLink] = None
    CRUNCHBASE: Optional[SocialLink] = None
    PITCHBOOK: Optional[SocialLink] = None
    INSTAGRAM: Optional[SocialLink] = None
    FACEBOOK: Optional[SocialLink] = None
    ANGELLIST: Optional[SocialLink] = None
    STACKOVERFLOW: Optional[SocialLink] = None


class RelatedCompanies(BaseModel):
    beta_notice: Optional[str] = None
    acquisitions: Optional[List] = None
    acquired_by: Optional[Dict[str, str]] = None
    subsidiaries: Optional[List] = None
    subsidiary_of: Optional[str] = None


class Investor(BaseModel):
    entity_urn: Optional[str] = None
    name: Optional[str] = None


class Funding(BaseModel):
    funding_total: Optional[int] = None
    num_funding_rounds: Optional[int] = None
    investors: Optional[List[Investor]] = None


class Employee(BaseModel):
    fullName: Optional[str] = None
    profilePictureUrl: Optional[str] = None
    socials: Optional[Dict[str, Dict[str, str]]] = None
    title: Optional[str] = None


class Investor(BaseModel):
    entity_urn: Optional[str] = None
    is_lead: Optional[bool] = None
    investor_name: Optional[str] = None
    association_urn: Optional[str] = None
    investor_urn: Optional[str] = None
    visibility_status: Optional[str] = None


class EmployeeHighlight(BaseModel):
    category: Optional[str] = None
    date_added: Optional[str] = None
    text: Optional[str] = None
    company_urn: Optional[str] = None


class FundingRound(BaseModel):
    announcement_date: Optional[str] = None
    funding_round_type: Optional[str] = None
    funding_amount: Optional[int] = None
    funding_currency: Optional[str] = None
    investors: Optional[List[Investor]] = None
    post_money_valuation: Optional[int] = None
    entity_urn: Optional[str] = None
    company_urn: Optional[str] = None
    source_url: Optional[str] = None


class Metric(BaseModel):
    timestamp: datetime = None
    metric_value: Optional[float] = None


class HistoricalData(BaseModel):
    value: Optional[float] = None
    change: Optional[float] = None
    percent_change: Optional[float] = None


class SocialMetric(BaseModel):
    _14d_ago: Optional[HistoricalData] = None
    _30d_ago: Optional[HistoricalData] = None
    _90d_ago: Optional[HistoricalData] = None
    _180d_ago: Optional[HistoricalData] = None
    _365d_ago: Optional[HistoricalData] = None
    metrics: List[Metric] = None
    latest_metric_value: Optional[float] = None


class TractionMetrics(BaseModel):
    facebook_like_count: Optional[SocialMetric] = None
    external_facebook_like_count: Optional[SocialMetric] = None
    facebook_follower_count: Optional[SocialMetric] = None
    external_facebook_follower_count: Optional[SocialMetric] = None
    facebook_following_count: Optional[SocialMetric] = None
    external_facebook_following_count: Optional[SocialMetric] = None
    linkedin_follower_count: Optional[SocialMetric] = None
    external_linkedin_follower_count: Optional[SocialMetric] = None
    instagram_follower_count: Optional[SocialMetric] = None
    external_instagram_follower_count: Optional[SocialMetric] = None
    twitter_follower_count: Optional[SocialMetric] = None
    external_twitter_follower_count: Optional[SocialMetric] = None
    headcount: Optional[SocialMetric] = None
    corrected_headcount: Optional[SocialMetric] = None
    external_headcount: Optional[SocialMetric] = None
    funding_total: Optional[SocialMetric] = None
    web_traffic: Optional[SocialMetric] = None
    headcount_advisor: Optional[SocialMetric] = None
    headcount_customer_success: Optional[SocialMetric] = None
    headcount_data: Optional[SocialMetric] = None
    headcount_design: Optional[SocialMetric] = None
    headcount_engineering: Optional[SocialMetric] = None
    headcount_finance: Optional[SocialMetric] = None
    headcount_legal: Optional[SocialMetric] = None
    headcount_marketing: Optional[SocialMetric] = None
    headcount_operations: Optional[SocialMetric] = None
    headcount_other: Optional[SocialMetric] = None
    headcount_people: Optional[SocialMetric] = None


class TeamConnection(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None


class CompanyResponse(BaseModel):

    # Company
    id: Optional[int] = None
    total_signals: Optional[List[int]] = None
    total_searches: Optional[List[int]] = None
    source_company_id: Optional[int] = None
    type: Optional[str] = None
    name: Optional[str] = None
    name_aliases: Optional[List[str]] = None
    legal_name: Optional[str] = None
    description: Optional[str] = None
    contact: Optional[Contact] = None
    founding_date: Optional[FoundingDate] = None
    website_urls: Optional[WebsiteURLs] = None
    logo_url: Optional[str] = None
    ownership_status: Optional[str] = None
    location: Optional[Location] = None
    tags: Optional[List[Tag]] = None
    socials: Optional[Socials] = None
    rank: Optional[int] = None
    related_companies: Optional[RelatedCompanies] = None
    created_at: datetime
    updated_at: datetime

    # CompanyMetric

    stage: Optional[str] = None
    headcount: Optional[int] = None
    traction_metrics: Optional[TractionMetrics] = None
    funding: Optional[Funding] = None
    employee_highlights: Optional[List[EmployeeHighlight]] = None
    investor_urn: Optional[str] = None
    funding_rounds: Optional[List[FundingRound]] = None

    # Harmonic
    employees: Optional[List[Employee]] = None
    team_connections: Optional[List[TeamConnection]] = None


router = APIRouter()


def get_company_data(company_id: int, db: Session):
    company_counts_subquery = (
        db.query(
            Company.name.label("name"),
            func.array_agg(case((Company.signal_id != None, Company.signal_id)))
            .filter(Company.signal_id != None)
            .label("signal_ids"),
            func.array_agg(case((Company.search_id != None, Company.search_id)))
            .filter(Company.search_id != None)
            .label("search_ids"),
        )
        .group_by(Company.name)
        .subquery()
    )

    query = (
        db.query(
            Company,
            company_counts_subquery.c.signal_ids,
            company_counts_subquery.c.search_ids,
            CompanyMetric.stage,
            CompanyMetric.headcount,
            CompanyMetric.traction_metrics,
            CompanyMetric.funding,
            CompanyMetric.employees,
            CompanyMetric.employee_highlights,
            CompanyMetric.investor_urn,
            CompanyMetric.funding_rounds,
        )
        .filter(Company.id == company_id)
        .outerjoin(
            company_counts_subquery, Company.name == company_counts_subquery.c.name
        )
        .join(CompanyMetric, Company.id == CompanyMetric.company_id)
        .order_by(Company.id)
    )

    result = query.one_or_none()

    return result


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


def get_all_team_connections(employee_ids):
    query = """
        query Query($getCompanyByIdId: Int!) {
            getCompanyById(id: $getCompanyByIdId) {
                userConnections {
                    user {
                        email
                        name
                    }
                }
            }
        }
    """
    variables = {"getCompanyByIdId": employee_ids}
    return make_harmonic_request(query, variables)


def make_harmonic_request(query, variables=None):
    url = "https://api.harmonic.ai/graphql"
    headers = {"Content-Type": "application/json", "apikey": settings.harmonic_api_key}
    payload = {
        "query": query,
    }
    if variables:
        payload["variables"] = variables
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Query failed with status code {response.status_code}")
        print("Response:", response.text)


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_companies(
    company_id: int,
    _=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = get_company_data(company_id, db)

        harmonic_employee = None

        if result:

            (
                company,
                total_signals,
                total_searches,
                stage,
                headcount,
                traction_metrics,
                funding,
                employees,
                employee_highlights,
                investor_urn,
                funding_rounds,
            ) = result

            person_ids = [
                int(employee["person"].split(":")[-1]) for employee in employees
            ]

            if person_ids:
                harmonic_employee = get_all_employees(person_ids)["data"][
                    "getPersonsByIds"
                ]

            if employees and harmonic_employee:
                for employee in employees:
                    for employee_harmonic in harmonic_employee:
                        if employee.get("person") == employee_harmonic.get("entityUrn"):
                            employee_harmonic["title"] = employee["title"]

            harmonic_team_connections = get_all_team_connections(
                int(company.source_company_id)
            )["data"]["getCompanyById"]["userConnections"]

            team_connections = [
                TeamConnection(
                    email=team_connection["user"]["email"],
                    name=team_connection["user"]["name"],
                )
                for team_connection in harmonic_team_connections
            ]

            return CompanyResponse(
                id=company.id,
                total_signals=total_signals,
                total_searches=total_searches,
                source_company_id=company.source_company_id,
                type=company.type,
                name=company.name,
                name_aliases=company.name_aliases,
                legal_name=company.legal_name,
                description=company.description,
                contact=company.contact,
                founding_date=company.founding_date,
                website_urls=company.website_urls,
                logo_url=company.logo_url,
                ownership_status=company.ownership_status,
                location=company.location,
                tags=company.tags,
                socials=company.socials,
                rank=company.rank,
                related_companies=company.related_companies,
                created_at=company.created_at,
                updated_at=company.updated_at,
                stage=stage,
                headcount=headcount,
                traction_metrics=traction_metrics,
                funding=funding,
                employees=harmonic_employee,
                employee_highlights=employee_highlights,
                investor_urn=investor_urn,
                funding_rounds=funding_rounds,
                team_connections=team_connections,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )
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
