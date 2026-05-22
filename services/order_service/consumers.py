from packages.messaging.broker import (
    broker,
    ecommerce_exchange,
    payment_result_queue,
)

from .repository import OrderRepository
from .service import clear_cart

from packages.database.session import AsyncSessionLocal
from packages.config.settings import settings


@broker.subscriber(
    queue=payment_result_queue,
    exchange=ecommerce_exchange,
)
async def payment_result(event: dict):

    try:

        print("Received event:", event)

        async with AsyncSessionLocal() as db:

            # PAYMENT SUCCESS
            if (
                event["event_type"]
                == settings.payment_success_routing_key
            ):

                order = await OrderRepository.update_status(
                    db,
                    event["order_id"],
                    "CONFIRMED"
                )

                if not order:

                    print(
                        f"Order {event['order_id']} not found"
                    )

                    return
                await db.commit()  # ✅ persist the status change

                await clear_cart(event["user_id"])
                print(f"Order {event['order_id']} confirmed")

              

            # PAYMENT FAILED
            elif (
                event["event_type"]
                == settings.payment_failed_routing_key
            ):

                order = await OrderRepository.update_status(
                    db,
                    event["order_id"],
                    "CANCELLED"
                )

                if not order:

                    print(
                        f"Order {event['order_id']} not found"
                    )

                    return

                await db.commit()  # ✅ persist the status change
                print(f"Order {event['order_id']} cancelled")

            else:

                print(
                    f"Unknown event type: {event['event_type']}"
                )

    except Exception as e:

        print(
            "PAYMENT RESULT CONSUMER ERROR:",
            str(e)
        )