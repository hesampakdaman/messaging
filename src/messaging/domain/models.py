from dataclasses import dataclass
from datetime import datetime
from typing import Any, NewType, TypeAlias
from uuid import UUID

JSON: TypeAlias = dict[str, Any]
Channel = NewType("Channel", str)
Consumer = NewType("Consumer", str)
MessageID = NewType("MessageID", UUID)


@dataclass
class Message:
    id: MessageID
    channel: Channel
    payload: JSON
    published_at: datetime
