from dataclasses import dataclass
from src.scrapping.store_enum import Stores

@dataclass
class Product:
    store: Stores
    name: str
    price: float
    discount: float
    discount_price: float
    category: str
    url: str