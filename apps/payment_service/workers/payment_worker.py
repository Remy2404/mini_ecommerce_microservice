import asyncio

from apps.payment_service.app.infrastructure.messaging.order_created_consumer import (
    main,
)


if __name__ == "__main__":
    asyncio.run(main())
