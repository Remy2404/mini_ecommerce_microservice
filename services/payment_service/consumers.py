"""Payment consumer."""

import asyncio
import random
import uuid

from datetime import datetime

from faststream import FastStream

from packages.database.session import AsyncSessionLocal
from packages.messaging.broker import (
    broker,
    ecommerce_exchange,
)
# payment consumer
from packages.messaging.broker import (
    broker,
    ecommerce_exchange,
    payment_order_created_queue,  # ✅ import the RabbitQueue object
)
from packages.contracts.topics import RoutingKey

from .service import PaymentService
from .repository import PaymentRepository
from packages.config.settings import settings 

@broker.subscriber(
    queue=payment_order_created_queue,    # ✅ RabbitQueue, not a string
    exchange=ecommerce_exchange,
)
async def process_payment(msg: dict):

    try:

        print("Payment service received:", msg)

        await asyncio.sleep(random.randint(1, 3))

        payment_data = await PaymentService.process_payment(
            order_id=msg["order_id"],
            user_id=msg["user_id"],
            amount=msg["amount"]
        )

        async with AsyncSessionLocal() as db:

            payment = await PaymentRepository.create(
                db=db,
                payment=payment_data
            )

            await db.commit()

        # PAYMENT SUCCESS
        if payment.status == "SUCCESS":

            event = {
                "event_id": str(uuid.uuid4()),
                "event_type": "payment.success",
                "payment_id": str(payment.id),
                "order_id": msg["order_id"],
                "user_id": msg["user_id"],
                "amount": msg["amount"],
                "status": payment.status,
                "created_at": datetime.utcnow().isoformat()
            }

            await broker.publish(
                event,
                routing_key=RoutingKey.PAYMENT_SUCCESS,
                exchange=ecommerce_exchange,
            )

            print("Published payment.success")

        # PAYMENT FAILED
        else:

            event = {
                "event_id": str(uuid.uuid4()),
                "event_type": "payment.failed",
                "payment_id": str(payment.id),
                "order_id": msg["order_id"],
                "user_id": msg["user_id"],
                "amount": msg["amount"],
                "status": "FAILED",
                "created_at": datetime.utcnow().isoformat()
            }

            await broker.publish(
                event,
                routing_key=RoutingKey.PAYMENT_FAILED,
                exchange=ecommerce_exchange,
            )

            print("Published payment.failed")

    except Exception as e:

        print("PAYMENT PROCESSING ERROR:", str(e))


app = FastStream(broker)


async def main():

    await broker.start()

    print("Payment consumer started")

    try:
        await asyncio.Event().wait()

    finally:
        await broker.close()


if __name__ == "__main__":
    asyncio.run(main())