"""Auth Service response schemas."""

from pydantic import BaseModel, EmailStr, Field


class RegisterUserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    message: str


# ---------------------------------------------------------------------------
# WSO2 SCIM2 user response DTOs
# ---------------------------------------------------------------------------


class Wso2UserName(BaseModel):
    """SCIM2 user name sub-resource."""

    given_name: str | None = None
    family_name: str | None = None


class Wso2UserProfile(BaseModel):
    """Single WSO2 user normalized from a SCIM2 resource."""

    id: str
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    active: bool = True
    roles: list[str] = Field(default_factory=list)


class Wso2UsersListResponse(BaseModel):
    """Paginated list of WSO2 users returned by SCIM2 ``GET /scim2/Users``."""

    total_results: int = 0
    start_index: int = 1
    items_per_page: int = 0
    users: list[Wso2UserProfile] = Field(default_factory=list)


class Wso2UserDetailResponse(BaseModel):
    """Wrapper for a single WSO2 user detail lookup."""

    user: Wso2UserProfile
