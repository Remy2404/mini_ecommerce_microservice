"""Payment service logic."""
import random

from .models import Payment


class PaymentService:

    @staticmethod
    async def process_payment(
        order_id: str,
        user_id: str,
        amount: float
    ):

        success = random.random() < 0.7

        payment = Payment(
            order_id=order_id,
            user_id=user_id,
            amount=amount,
            status="SUCCESS" if success else "FAILED"
        )

        return payment