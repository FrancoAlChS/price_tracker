from abc import ABC, abstractmethod
from playwright.async_api import Page
from typing import Any

class StorePage(ABC):

    @abstractmethod
    async def scrapping(self, page: Page, url: str) -> list[Any]:
        pass
    