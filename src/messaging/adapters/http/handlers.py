from datetime import datetime
import uuid

from fastapi import Body, Depends, FastAPI, Path, status

from messaging.domain import models
from messaging.service.service import Service
from messaging.service import commands

from . import schema, utils

app = FastAPI()

# pyright: reportCallInDefaultInitializer = false


@app.post(
    "/channels/{channel}/publish",
    response_model=schema.PublishResponse,
    status_code=status.HTTP_201_CREATED,
)
async def publish(
    channel: models.Channel = Path(..., min_length=1),
    body: schema.PublishRequest = Body(...),
    svc: Service = Depends(utils.get_service),
):
    published_at = datetime.now()
    cmd = commands.Publish(
        models.Message(
            id=models.MessageID(uuid.uuid4()),
            channel=channel,
            payload=body.payload,
            published_at=published_at,
        )
    )
    new_id = await svc.publish(cmd)
    return schema.PublishResponse(id=new_id)


@app.get(
    "/channels/{channel}/messages/unread",
    response_model=schema.GetMessagesResponse,
)
async def get_unread_messages(
    channel: models.Channel = Path(..., min_length=1),
    consumer: models.Consumer = Depends(utils.require_consumer),
    svc: Service = Depends(utils.get_service),
):
    cmd = commands.ListUnread(channel, consumer)
    messages = await svc.list_unread(cmd)
    return schema.GetMessagesResponse(messages=messages)


@app.get(
    "/channels/{channel}/messages/from/{from_seq}",
    response_model=schema.GetMessagesResponse,
)
async def get_messages_from_sequence(
    channel: models.Channel = Path(..., min_length=1),
    from_seq: int = Path(..., ge=0),
    svc: Service = Depends(utils.get_service),
):
    cmd = commands.ListFromSequence(channel, from_seq)
    messages = await svc.list_from_sequence(cmd)
    return schema.GetMessagesResponse(messages=messages)


@app.post(
    "/messages/{id}/ack",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def ack_message(
    id: uuid.UUID = Path(...),
    consumer: models.Consumer = Depends(utils.require_consumer),
    svc: Service = Depends(utils.get_service),
):
    cmd = commands.Ack(models.MessageID(id), consumer, read_at=datetime.now())
    await svc.ack(cmd)
