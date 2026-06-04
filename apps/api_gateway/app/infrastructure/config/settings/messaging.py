"""Messaging settings."""

from pydantic import Field


class MessagingSettings:
    rabbitmq_host: str = Field(..., validation_alias="RABBITMQ_HOST")
    rabbitmq_port: int = Field(..., validation_alias="RABBITMQ_PORT")
    rabbitmq_user: str = Field(..., validation_alias="RABBITMQ_USER")
    rabbitmq_password: str = Field(..., validation_alias="RABBITMQ_PASSWORD")
    rabbitmq_vhost: str = Field(..., validation_alias="RABBITMQ_VHOST")
    rabbitmq_url: str = Field(..., validation_alias="RABBITMQ_URL")
    rabbitmq_exchange: str = Field(..., validation_alias="RABBITMQ_EXCHANGE")

    order_created_routing_key: str = Field(..., validation_alias="ORDER_CREATED_ROUTING_KEY")
    payment_success_routing_key: str = Field(..., validation_alias="PAYMENT_SUCCESS_ROUTING_KEY")
    payment_failed_routing_key: str = Field(..., validation_alias="PAYMENT_FAILED_ROUTING_KEY")
    order_confirmed_routing_key: str = Field(..., validation_alias="ORDER_CONFIRMED_ROUTING_KEY")
    order_cancelled_routing_key: str = Field(..., validation_alias="ORDER_CANCELLED_ROUTING_KEY")
    cart_restored_routing_key: str = Field(..., validation_alias="CART_RESTORED_ROUTING_KEY")

    order_created_queue: str = Field(..., validation_alias="ORDER_CREATED_QUEUE")
    payment_result_queue: str = Field(..., validation_alias="PAYMENT_RESULT_QUEUE")
    cart_restore_queue: str = Field(..., validation_alias="CART_RESTORE_QUEUE")
    dead_letter_queue: str = Field(..., validation_alias="DEAD_LETTER_QUEUE")
    rabbitmq_retry_max_attempts: int = Field(3, validation_alias="RABBITMQ_RETRY_MAX_ATTEMPTS")
    rabbitmq_retry_delay_ms: int = Field(5000, validation_alias="RABBITMQ_RETRY_DELAY_MS")
    rabbitmq_retry_backoff_multiplier: float = Field(
        2.0,
        validation_alias="RABBITMQ_RETRY_BACKOFF_MULTIPLIER",
    )
