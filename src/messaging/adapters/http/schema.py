from pydantic import BaseModel

from messaging.domain import models


class PublishRequest(BaseModel):
    payload: models.JSON


class PublishResponse(BaseModel):
    id: models.MessageID


class GetMessagesResponse(BaseModel):
    messages: list[models.Message]
