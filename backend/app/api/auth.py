from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    get_current_active_user
)
from app.models.user import User
from app.models.organization import Organization, OrganizationType
from app.schemas.user import UserCreate, User as UserSchema, UserWithOrganization, Token, UserUpdate
import re

router = APIRouter()


def create_slug(name: str) -> str:
    """Create URL-friendly slug from organization name"""
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug.strip('-')


@router.post(
    "/register-simple", 
    response_model=UserWithOrganization,
    status_code=status.HTTP_201_CREATED,
    summary="Simple User Registration",
    description="Register a new user account without requiring organization setup",
    response_description="Newly created user account",
    responses={
        201: {"description": "User successfully registered"},
        400: {"description": "Email already registered"},
        422: {"description": "Invalid input data"}
    }
)
async def register_simple(
    user_data: dict,
    db: Session = Depends(get_db)
):
    """
    # 🔐 Simple User Registration
    
    Register a new user account quickly without organization setup.
    Users can join organizations later through the profile settings.
    
    ## Request Parameters
    - **email**: User's email address (required)
    - **password**: User's password (required, minimum 8 characters)
    - **full_name**: User's full name (optional)
    
    ## Example Usage
    ```bash
    curl -X POST "http://localhost:8000/api/auth/register-simple" \
         -H "Content-Type: application/json" \
         -d '{
           "email": "newuser@example.com",
           "password": "securepass123",
           "full_name": "New User"
         }'
    ```
    
    ## Security Features
    - Email uniqueness validation
    - Password hashing
    - Automatic account activation
    """
    # Check if user already exists
    email = user_data.get("email")
    password = user_data.get("password")
    full_name = user_data.get("full_name")
    
    if not email or not password:
        raise HTTPException(
            status_code=400,
            detail="Email and password are required"
        )
    
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Validate password length
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long"
        )
    
    # Create new user
    hashed_password = get_password_hash(password)
    db_user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_active=True,
        role="member"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Return user info
    return UserWithOrganization(
        id=db_user.id,
        email=db_user.email,
        full_name=db_user.full_name,
        is_active=db_user.is_active,
        is_superuser=db_user.is_superuser,
        organization_id=db_user.organization_id,
        role=db_user.role,
        organization_name=None,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )

@router.post(
    "/register", 
    response_model=UserWithOrganization,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description="Register a new user account with optional organization creation or joining",
    response_description="Newly created user with organization information",
    responses={
        201: {"description": "User successfully registered"},
        400: {"description": "Email already registered or organization name exists"},
        422: {"description": "Invalid input data"}
    }
)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    # 🔐 Register New User
    
    Register a new user account with flexible organization options.
    
    ## Registration Options
    
    ### 1. **Create New Organization**
    - Set `create_organization` to `true`
    - Provide `organization_name`
    - User becomes organization owner
    
    ### 2. **Join Existing Organization**
    - Set `create_organization` to `false`
    - Provide `organization_id`
    - User becomes organization member
    
    ### 3. **Individual Account**
    - Set both `create_organization` to `false` and `organization_id` to `null`
    - User can join organizations later
    
    ## Request Body Example
    ```json
    {
        "email": "user@example.com",
        "password": "securepassword123",
        "full_name": "John Doe",
        "create_organization": true,
        "organization_name": "My AI Company"
    }
    ```
    
    ## Security Features
    - Password requirements: minimum 8 characters
    - Email uniqueness validation
    - Organization name uniqueness validation
    - Automatic role assignment based on registration type
    """
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    organization = None
    
    # Handle organization creation or joining
    if user.create_organization and user.organization_name:
        # Create new organization
        existing_org = db.query(Organization).filter(Organization.name == user.organization_name).first()
        if existing_org:
            raise HTTPException(
                status_code=400,
                detail="Organization with this name already exists"
            )
        
        # Create slug
        slug = create_slug(user.organization_name)
        existing_slug = db.query(Organization).filter(Organization.slug == slug).first()
        if existing_slug:
            slug = f"{slug}-new"
        
        organization = Organization(
            name=user.organization_name,
            slug=slug,
            type=OrganizationType.SMALL_BUSINESS,
            is_active=True
        )
        db.add(organization)
        db.flush()  # Get the ID without committing
        
    elif user.organization_id:
        # Join existing organization
        organization = db.query(Organization).filter(
            Organization.id == user.organization_id,
            Organization.is_active == True
        ).first()
        if not organization:
            raise HTTPException(
                status_code=400,
                detail="Selected organization not found or inactive"
            )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_active=True,
        organization_id=organization.id if organization else None,
        role="owner" if user.create_organization else "member"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Prepare response with organization info
    response = UserWithOrganization(
        id=db_user.id,
        email=db_user.email,
        full_name=db_user.full_name,
        is_active=db_user.is_active,
        is_superuser=db_user.is_superuser,
        organization_id=db_user.organization_id,
        role=db_user.role,
        organization_name=organization.name if organization else None,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )
    
    return response


@router.post(
    "/login", 
    response_model=Token,
    summary="User Login",
    description="Authenticate user and return JWT access token for API access",
    response_description="JWT access token for authenticated requests",
    responses={
        200: {"description": "Login successful, token returned"},
        401: {"description": "Invalid credentials"},
        400: {"description": "User account is inactive"}
    }
)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    # 🔑 User Login
    
    Authenticate user credentials and return a JWT access token for API access.
    
    ## Authentication Process
    1. **Email Verification**: Check if user exists in the system
    2. **Password Validation**: Verify password against stored hash
    3. **Account Status**: Ensure user account is active
    4. **Token Generation**: Create JWT token with user ID
    
    ## Usage Instructions
    
    ### Form Data (application/x-www-form-urlencoded)
    - **username**: User's email address (required)
    - **password**: User's password (required)
    
    ### Example Request
    ```bash
    curl -X POST "http://localhost:8000/api/auth/login" \
         -H "Content-Type: application/x-www-form-urlencoded" \
         -d "username=user@example.com&password=securepassword123"
    ```
    
    ### Example Response
    ```json
    {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer"
    }
    ```
    
    ## Token Usage
    Include the token in subsequent requests:
    ```
    Authorization: Bearer your_access_token_here
    ```
    
    ## Token Properties
    - **Expiration**: 30 minutes (configurable)
    - **Algorithm**: HS256
    - **Claims**: User ID, issued time, expiration time
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/me", 
    response_model=UserWithOrganization,
    summary="Get Current User Profile",
    description="Get detailed information about the currently authenticated user including organization details",
    response_description="Current user profile with organization and department information",
    responses={
        200: {"description": "User profile retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Access denied"}
    }
)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    # 👤 Get Current User Profile
    
    Retrieve comprehensive information about the currently authenticated user.
    
    ## Returned Information
    
    ### User Details
    - **Basic Info**: ID, email, full name, status
    - **Account Status**: Active status, superuser flag
    - **Timestamps**: Creation and last update times
    
    ### Organization Context
    - **Organization**: Name and ID if user belongs to an organization
    - **Department**: Department name and ID if assigned
    - **Role**: User's role within the organization
    
    ## Authorization Required
    This endpoint requires a valid JWT token in the Authorization header:
    ```
    Authorization: Bearer your_access_token_here
    ```
    
    ## Example Response
    ```json
    {
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe",
        "is_active": true,
        "is_superuser": false,
        "organization_id": 5,
        "organization_name": "My AI Company",
        "department_id": 2,
        "department_name": "Data Science",
        "role": "member",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-16T14:20:00Z"
    }
    ```
    
    ## Use Cases
    - **Profile Display**: Show user information in UI
    - **Authorization**: Check user roles and permissions
    - **Organization Context**: Display organization-specific information
    - **Navigation**: Determine available features based on user role
    """
    organization_name = None
    
    if current_user.organization_id:
        organization = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
        if organization:
            organization_name = organization.name
    
    return UserWithOrganization(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        organization_id=current_user.organization_id,
        role=current_user.role,
        organization_name=organization_name,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.put("/me", response_model=UserWithOrganization)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    # Update fields that are provided
    update_data = user_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "password" and value:
            # Hash the new password
            current_user.hashed_password = get_password_hash(value)
        elif field == "username" and value:
            # Map username to full_name for compatibility
            current_user.full_name = value
        elif hasattr(current_user, field):
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    # Return updated user info
    organization_name = None
    if current_user.organization_id:
        organization = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
        if organization:
            organization_name = organization.name
    
    return UserWithOrganization(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        organization_id=current_user.organization_id,
        role=current_user.role,
        organization_name=organization_name,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    ) 

@router.get(
    "/demo-users",
    summary="Get Demo Users",
    description="Get list of demo users available for testing the login functionality",
    response_description="List of demo users with their credentials"
)
async def get_demo_users(db: Session = Depends(get_db)):
    """
    # 🧪 Get Demo Users
    
    Retrieve a list of demo users that can be used for testing the login functionality.
    This endpoint returns actual users from the database with their login credentials.
    
    ## Returned Information
    - **Superadmin**: Platform administrator with full access
    - **Organization Admins**: Organization administrators
    - **Organization Members**: Standard users for testing member functionality
    
    ## Example Response
    ```json
    {
        "demo_users": [
            {
                "email": "superadmin@platform.com",
                "password": "SuperAdmin123!",
                "role": "admin",
                "description": "Platform Superadmin",
                "organization": null
            }
        ]
    }
    ```
    
    ## Use Cases
    - **Testing**: Quick access to test accounts
    - **Demo**: Show available accounts to demo users
    - **Development**: Easy login for development purposes
    """
    try:
        # Get users from database
        users = db.query(User).filter(User.is_active == True).all()
        
        demo_users = []
        
        # Define demo user credentials for existing demo accounts
        demo_credentials = {
            # Current seed data users with correct passwords
            "admin@example.com": {
                "password": "SuperAdmin123!",
                "description": "System Administrator"
            },
            "alice@techcorp.com": {
                "password": "Password123!",
                "description": "TechCorp Solutions - Data Analyst"
            },
            "bob@dataanalytics.com": {
                "password": "Password123!",
                "description": "Data Analytics Inc - Data Scientist"
            }
        }
        
        # Add any users that have demo passwords
        for user in users:
            demo_password = None
            description = ""
            
            # Check if user has predefined demo credentials
            if user.email in demo_credentials:
                creds = demo_credentials[user.email]
                demo_password = creds["password"]
                description = creds["description"]
            # Add superusers not already in the list
            elif user.is_superuser and user.email not in demo_credentials:
                demo_password = "admin123"
                description = f"Administrator Account - {user.full_name}"
            
            if demo_password:
                organization_name = None
                if user.organization_id:
                    organization = db.query(Organization).filter(Organization.id == user.organization_id).first()
                    if organization:
                        organization_name = organization.name
                
                demo_users.append({
                    "email": user.email,
                    "password": demo_password,
                    "role": user.role or ("admin" if user.is_superuser else "member"),
                    "description": description,
                    "organization": organization_name,
                    "full_name": user.full_name,
                    "is_superuser": user.is_superuser
                })
        
        return {
            "demo_users": demo_users,
            "total_count": len(demo_users),
            "message": "Demo users retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving demo users: {str(e)}"
        )