from collections.abc import Mapping
import logging

from messaging.adapters import repository
from messaging.domain import models

from . import commands


class Service:
    def __init__(self, pg: repository.PostgresManager, logger: logging.Logger) -> None:
        self.pg: repository.PostgresManager = pg
        self.logger: logging.Logger = logger

    def log_with(self, extra: Mapping[str, object]) -> logging.LoggerAdapter[logging.Logger]:
        return logging.LoggerAdapter(self.logger, extra=extra, merge_extra=True)

    async def publish(self, cmd: commands.Publish) -> models.MessageID:
        log = self.log_with({"message_id": cmd.message.id, "channel": cmd.message.channel})
        log.info("publish.start")
        async with self.pg.transaction() as tx:
            new_id = await tx.add(cmd.message)
        log.info("publish.ok", extra={"new_id": new_id})
        return new_id

    async def list_unread(self, cmd: commands.ListUnread) -> list[models.Message]:
        log = self.log_with({"channel": cmd.channel, "consumer": cmd.consumer})
        log.debug("list_unread.start")
        async with self.pg.transaction() as tx:
            messages = await tx.list_unread(cmd.channel, cmd.consumer)
        log.debug("list_unread.ok", extra={"count": len(messages)})
        return messages

    async def list_from_sequence(self, cmd: commands.ListFromSequence) -> list[models.Message]:
        log = self.log_with({"channel": cmd.channel, "from_sequence": cmd.from_seq})
        log.debug("list_from_sequence.start")
        async with self.pg.transaction() as tx:
            messages = await tx.list_from_sequence(cmd.channel, cmd.from_seq)
        log.debug("list_from_sequence.ok", extra={"count": len(messages)})
        return messages

    async def ack(self, cmd: commands.Ack) -> None:
        log = self.log_with({"message_id": cmd.id, "consumer": cmd.consumer})
        log.debug("ack.start")
        async with self.pg.transaction() as tx:
            await tx.mark_read(cmd.id, cmd.consumer, cmd.read_at)
        log.debug("ack.ok")
