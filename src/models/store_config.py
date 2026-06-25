from dataclasses import dataclass
from src.scrapping.store_enum import Stores

@dataclass
class StoreConfig:
    name: Stores
    urls: list[str]
    note: str | None = None