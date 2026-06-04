"""WSO2 settings."""

from pydantic import Field


class WSO2Settings:
    wso2_base_url: str = Field("https://localhost:9443", validation_alias="WSO2_BASE_URL")
    wso2_issuer: str = Field("https://localhost:9443/oauth2/token", validation_alias="WSO2_ISSUER")
    wso2_audience: str = Field(validation_alias="WSO2_AUDIENCE")
    wso2_jwks_url: str = Field("https://localhost:9443/oauth2/jwks", validation_alias="WSO2_JWKS_URL")
    wso2_token_url: str = Field("https://localhost:9443/oauth2/token", validation_alias="WSO2_TOKEN_URL")
    wso2_introspection_url: str = Field(
        "https://localhost:9443/oauth2/introspect",
        validation_alias="WSO2_INTROSPECTION_URL",
    )
    wso2_userinfo_url: str = Field("https://localhost:9443/oauth2/userinfo", validation_alias="WSO2_USERINFO_URL")
    wso2_client_id: str = Field(..., validation_alias="WSO2_CLIENT_ID")
    wso2_client_secret: str = Field(..., validation_alias="WSO2_CLIENT_SECRET")
    wso2_scim_create_scope: str = Field("internal_user_mgt_create", validation_alias="WSO2_SCIM_CREATE_SCOPE")
    wso2_scim_view_scope: str = Field("internal_user_mgt_view", validation_alias="WSO2_SCIM_VIEW_SCOPE")
    wso2_scim_list_scope: str = Field("internal_user_mgt_list", validation_alias="WSO2_SCIM_LIST_SCOPE")
    wso2_verify_ssl: bool = Field(False, validation_alias="WSO2_VERIFY_SSL")
