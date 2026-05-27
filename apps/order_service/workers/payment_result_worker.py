import asyncio

from apps.order_service.app.infrastructure.messaging.payment_result_consumer import main


if __name__ == "__main__":
    asyncio.run(main())
