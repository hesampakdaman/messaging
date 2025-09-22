CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY,
    seq BIGSERIAL NOT NULL,
    channel TEXT NOT NULL,
    payload JSONB NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_channel_seq
    ON messages (channel, seq);

CREATE TABLE IF NOT EXISTS message_reads (
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    consumer TEXT NOT NULL,
    read_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (message_id, consumer)
);

CREATE TABLE IF NOT EXISTS channel_sequences (
  channel  TEXT PRIMARY KEY,
  last_seq BIGINT NOT NULL
);
