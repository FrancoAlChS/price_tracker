from dataclasses import dataclass

@dataclass
class TelegramConfig:
    token: str
    chat_id: str
    id: int | None = None
