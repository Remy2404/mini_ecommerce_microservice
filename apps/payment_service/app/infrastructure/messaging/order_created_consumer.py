from apps.payment_service.app.infrastructure.messaging.payment_flow import (
    main,
    process_payment,
)

__all__ = [
    "main",
    "process_payment",
]


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
