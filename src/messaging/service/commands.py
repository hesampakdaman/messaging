from dataclasses import dataclass
from datetime import datetime

from messaging.domain import models


@dataclass(frozen=True)
class Publish:
    message: models.Message


@dataclass(frozen=True)
class ListUnread:
    channel: models.Channel
    consumer: models.Consumer


@dataclass(frozen=True)
class ListFromSequence:
    channel: models.Channel
    from_seq: int


@dataclass(frozen=True)
class Ack:
    id: models.MessageID
    consumer: models.Consumer
    read_at: datetime
