from playwright.async_api import Page
from src.scrapping.stores.fallabella_store import FallabellaStore
from src.scrapping.stores.oechsle_store import OechsleStore
from src.scrapping.stores.store_page import StorePage
from src.scrapping.store_enum import Stores
from src.models.product import Product


class ScrappingFactory:

    @staticmethod
    async def scrapping(store: Stores, url: str, page: Page) -> list[Product]:
        stores: dict[Stores, StorePage] = {
            Stores.FALLABELLA: FallabellaStore(),
            Stores.OECHSLE: OechsleStore()
        }

        store_definition: StorePage | None = stores.get(store)

        if store_definition is None:
            raise ValueError("No found store definition")

        return await store_definition.scrapping(page, url)
