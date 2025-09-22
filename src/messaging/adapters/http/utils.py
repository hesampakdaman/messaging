# pyright: reportCallInDefaultInitializer = false
from fastapi import Header, HTTPException, Request

from messaging.domain import models
from messaging.service.service import Service


async def require_consumer(
    consumer: models.Consumer | None = Header(default=None, alias="X-Consumer"),
) -> models.Consumer:
    if not consumer or not str(consumer).strip():
        raise HTTPException(status_code=400, detail="X-Consumer header is required")
    return consumer


def get_service(request: Request) -> Service:
    svc: Service | None = getattr(request.app.state, "service", None)  # pyright: ignore[reportAny]
    if not isinstance(svc, Service):
        raise RuntimeError("Service not configured on app.state.service")
    return svc
