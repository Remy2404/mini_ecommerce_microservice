import asyncio

from apps.payment_service.app.infrastructure.messaging.payment_flow import main


if __name__ == "__main__":
    asyncio.run(main())

