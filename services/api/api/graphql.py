import asyncio
from typing import AsyncGenerator
from functools import cached_property
import strawberry
from strawberry.fastapi import BaseContext, GraphQLRouter
from strawberry.permission import BasePermission
from strawberry.types import Info as _Info
from strawberry.types.info import RootValueType
from confluent_kafka import Consumer, KafkaException
import logging

from . import auth, db

logger = logging.getLogger(__name__)

#### Context ####

class Context(BaseContext):
    @cached_property
    def user(self) -> dict | None:
        if self.request:
            if auth_ := self.request.headers.get("Authorization"):
                method, token = auth_.split(" ")
                if method == 'Bearer':
                    if data := auth.decode_jwt(token):
                        return data

async def get_context() -> Context:
    return Context()

Info = _Info[Context, RootValueType]

#### Auth ####

class IsAuthenticated(BasePermission):
    message = "User is not authenticated."

    def has_permission(self, source, info: Info, **kwargs):
        return info.context.user is not None

#### Mutations ####

@strawberry.type
class Mutation:
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def add_product(self, name: str) -> db.Product:
        return db.create_product(name)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def remove_product(self, id: str) -> None:
        db.delete_product(id)

#### Queries ####

@strawberry.type
class Query:
    @strawberry.field
    def products(self) -> list[db.Product]:
        return db.list_products()

#### Subscriptions ####

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def product_added(self) -> AsyncGenerator[db.Product, None]:
        # Create a Kafka consumer
        consumer = Consumer({
            'bootstrap.servers': 'localhost:9092',  # replace with your Kafka server address
            'group.id': 'product-group',
            'auto.offset.reset': 'earliest'
        })

        # Subscribe to the 'products' topic
        consumer.subscribe(['products'])

        try:
            while True:
                msg = consumer.poll(1.0)

                if msg is None:
                    continue
                if msg.error():
                    raise KafkaException(msg.error())
                else:
                    # Assume the message is a serialized Product object
                    product = deserialize_product(msg.value())
                    yield product

        except KeyboardInterrupt:
            pass
        finally:
            # Close down consumer to commit final offsets.
            consumer.close()

#### API ####

def get_app():
    return GraphQLRouter(
        strawberry.Schema(Query, mutation=Mutation, subscription=Subscription),
        context_getter=get_context
    )
