import httpx

from packages.config.settings import settings


async def get_cart_data(user_id: str):

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{settings.cart_service_url}/cart/",
            params={
                "user_id": user_id
            }
        )

        print("STATUS:", response.status_code)
        print("BODY:", response.text)

        if response.status_code != 200:
            return None

        return response.json()


async def clear_cart(user_id: str):

    async with httpx.AsyncClient() as client:

        response = await client.delete(
            f"{settings.cart_service_url}/cart/",
            params={
                "user_id": user_id
            }
        )

        return response.status_code == 200