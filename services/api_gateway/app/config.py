from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # WSO2
    WSO2_ISSUER: str           # e.g. https://wso2host:9443/oauth2/token
    WSO2_JWKS_URL: str         # e.g. https://wso2host:9443/oauth2/jwks
    WSO2_AUDIENCE: str         # your client_id registered in WSO2

    # Downstream services
    USER_SERVICE_URL: str
    ORDER_SERVICE_URL: str
    PRODUCT_SERVICE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60   # seconds

    class Config:
        env_file = ".env"

settings = Settings()

if __name__ == "__main__":
    print("WSO2 Issuer  :", settings.WSO2_ISSUER)
    print("WSO2 JWKS    :", settings.WSO2_JWKS_URL)
    print("Audience     :", settings.WSO2_AUDIENCE)
    print("Redis URL    :", settings.REDIS_URL)
    print("User Service :", settings.USER_SERVICE_URL)
    
    
    