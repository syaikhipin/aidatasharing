from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
import re
from app.core.database import get_db
from app.core.auth import get_current_active_user, get_current_superuser
from app.models.user import User
from app.models.organization import Organization, Department, OrganizationType, DataSharingLevel
from app.schemas.organization import (
    OrganizationCreate, 
    OrganizationUpdate, 
    Organization as OrganizationSchema,
    OrganizationWithDepartments,
    OrganizationOption,
    DepartmentCreate,
    DepartmentUpdate,
    Department as DepartmentSchema,
    OrganizationMember
)

router = APIRouter()


def create_slug(name: str) -> str:
    """Create URL-friendly slug from organization name"""
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug.strip('-')


@router.get("/options", response_model=List[OrganizationOption])
async def get_organization_options(
    db: Session = Depends(get_db)
):
    """Get list of organizations for registration dropdown"""
    organizations = db.query(Organization).filter(
        Organization.is_active == True
    ).all()
    
    return [
        OrganizationOption(
            id=org.id,
            name=org.name,
            type=org.type,
            description=org.description
        ) for org in organizations
    ]


@router.post("/", response_model=OrganizationSchema)
async def create_organization(
    org: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new organization"""
    # Check if organization name already exists
    existing_org = db.query(Organization).filter(Organization.name == org.name).first()
    if existing_org:
        raise HTTPException(
            status_code=400,
            detail="Organization with this name already exists"
        )
    
    # Create slug
    slug = create_slug(org.name)
    existing_slug = db.query(Organization).filter(Organization.slug == slug).first()
    if existing_slug:
        # Append user ID to make it unique
        slug = f"{slug}-{current_user.id}"
    
    # Create organization
    db_org = Organization(
        name=org.name,
        slug=slug,
        description=org.description,
        type=org.type,
        allow_external_sharing=org.allow_external_sharing,
        default_sharing_level=org.default_sharing_level,
        website=org.website,
        contact_email=org.contact_email
    )
    
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    
    # Make the creator the owner
    current_user.organization_id = db_org.id
    current_user.role = "owner"
    db.commit()
    
    return db_org


@router.get("/", response_model=List[OrganizationSchema])
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List organizations accessible to user"""
    if current_user.is_superuser:
        # Superuser can see all organizations
        organizations = db.query(Organization).offset(skip).limit(limit).all()
    elif current_user.organization_id:
        # Regular user can only see their own organization
        organizations = db.query(Organization).filter(
            Organization.id == current_user.organization_id
        ).all()
    else:
        # User not in any organization
        organizations = []
    
    return organizations


@router.get("/my")
async def get_my_organization(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's organization with departments"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=404,
            detail="User is not part of any organization"
        )
    
    # Get organization
    organization = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )
    
    # Manually load departments
    departments = db.query(Department).filter(
        Department.organization_id == organization.id
    ).all()
    
    # Create a dictionary response
    return {
        "id": organization.id,
        "name": organization.name,
        "slug": organization.slug,
        "description": organization.description,
        "type": organization.type.value,
        "is_active": organization.is_active,
        "allow_external_sharing": organization.allow_external_sharing,
        "default_sharing_level": organization.default_sharing_level.value,
        "website": organization.website,
        "contact_email": organization.contact_email,
        "created_at": organization.created_at,
        "updated_at": organization.updated_at,
        "departments": [
            {
                "id": dept.id,
                "name": dept.name,
                "description": dept.description,
                "is_active": dept.is_active,
                "organization_id": dept.organization_id,
                "created_at": dept.created_at,
                "updated_at": dept.updated_at
            } for dept in departments
        ]
    }


@router.get("/{organization_id}", response_model=OrganizationWithDepartments)
async def get_organization(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get organization by ID"""
    # Check if user has access to this organization
    if not current_user.is_superuser and current_user.organization_id != organization_id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to access this organization"
        )
    
    organization = db.query(Organization).options(
        joinedload(Organization.departments)
    ).filter(Organization.id == organization_id).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return organization


@router.put("/{organization_id}", response_model=OrganizationSchema)
async def update_organization(
    organization_id: int,
    org_update: OrganizationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update organization (owner/admin only)"""
    # Check permissions
    if not current_user.is_superuser and (
        current_user.organization_id != organization_id or 
        current_user.role not in ["owner", "admin"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to update this organization"
        )
    
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Update fields
    update_data = org_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "name" and value:
            # Update slug if name changes
            new_slug = create_slug(value)
            existing_slug = db.query(Organization).filter(
                Organization.slug == new_slug,
                Organization.id != organization_id
            ).first()
            if existing_slug:
                new_slug = f"{new_slug}-{organization_id}"
            organization.slug = new_slug
        
        setattr(organization, field, value)
    
    db.commit()
    db.refresh(organization)
    return organization


@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete organization (owner only)"""
    # Check permissions
    if not current_user.is_superuser and (
        current_user.organization_id != organization_id or 
        current_user.role != "owner"
    ):
        raise HTTPException(
            status_code=403,
            detail="Only organization owners can delete organizations"
        )
    
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Soft delete by setting is_active to False
    organization.is_active = False
    db.commit()
    
    return {"message": "Organization deleted successfully"}


@router.get("/{organization_id}/members", response_model=List[OrganizationMember])
async def get_organization_members(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get organization members"""
    # Check permissions
    if not current_user.is_superuser and current_user.organization_id != organization_id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to view organization members"
        )
    
    members = db.query(User).filter(User.organization_id == organization_id).all()
    
    result = []
    for member in members:
        department_name = None
        if member.department_id:
            dept = db.query(Department).filter(Department.id == member.department_id).first()
            if dept:
                department_name = dept.name
        
        result.append(OrganizationMember(
            id=member.id,
            email=member.email,
            full_name=member.full_name,
            role=member.role,
            department_id=member.department_id,
            department_name=department_name,
            is_active=member.is_active,
            created_at=member.created_at
        ))
    
    return result


# Department endpoints
@router.post("/{organization_id}/departments", response_model=DepartmentSchema)
async def create_department(
    organization_id: int,
    dept: DepartmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new department"""
    # Check permissions
    if not current_user.is_superuser and (
        current_user.organization_id != organization_id or 
        current_user.role not in ["owner", "admin"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to create departments"
        )
    
    # Create Department model with organization_id set
    db_dept = Department(
        name=dept.name,
        description=dept.description,
        is_active=dept.is_active,
        organization_id=organization_id
    )
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    
    return db_dept


@router.get("/{organization_id}/departments", response_model=List[DepartmentSchema])
async def get_departments(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get organization departments"""
    # Check permissions
    if not current_user.is_superuser and current_user.organization_id != organization_id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to view departments"
        )
    
    departments = db.query(Department).filter(
        Department.organization_id == organization_id,
        Department.is_active == True
    ).all()
    
    return departments 