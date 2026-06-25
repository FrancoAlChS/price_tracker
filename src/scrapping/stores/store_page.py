from abc import ABC, abstractmethod
from playwright.async_api import Page
from src.models.product import Product

class StorePage(ABC):

    @abstractmethod
    async def scrapping(self, page: Page, url: str) -> list[Product]:
        pass
    