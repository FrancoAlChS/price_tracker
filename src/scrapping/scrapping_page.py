
import asyncio
from playwright.async_api import BrowserContext, async_playwright
from src.scrapping.scrapping_factory import ScrappingFactory
from src.util.send_telegram import send_telegram
from src.util.db_connection import db_connection
from src.models.product import Product
from src.models.store_config import StoreConfig
from src.models.telegram_config import TelegramConfig
from src.services.scraping_service import ScrapingService
from src.scrapping.store_enum import Stores

MAX_CONCURRENT = 5

semaphore = asyncio.Semaphore(MAX_CONCURRENT)


async def _scrape_url(context: BrowserContext, store_name: Stores, url: str) -> list[Product]:
    async with semaphore:
        page = await context.new_page()
        await page.add_init_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')
        try:
            return await ScrappingFactory.scrapping(store_name, url, page)
        except Exception as e:
            print(f"  Error en {url}: {e}")
            return []
        finally:
            await page.close()


async def scrapping_page() -> None:
    scraping_service = ScrapingService()
    stores: list[StoreConfig] = scraping_service.get_stores_config()
    telegram_config: TelegramConfig | None = scraping_service.get_telegram_config()

    if telegram_config is None:
        print("\n[ERROR] No hay configuración de Telegram registrada. Use POST /api/telegram-config/")
        return

    ofertas_enviadas: int = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="es-PE",
        )

        for store_config in stores:
            store_name: Stores = store_config.name

            if store_config.note is not None:
                print(f"\n[OMITIDO] {store_name}: {store_config.note}")
                continue

            print(f"\n{'='*50}")
            print(f"Escaneando: {store_name}")
            print(f"{'='*50}")

            tasks = [
                _scrape_url(context, store_name, url)
                for url in store_config.urls
            ]

            results: list[list[Product]] = await asyncio.gather(*tasks)
            total_offers: list[Product] = [offer for batch in results for offer in batch]

            print(f"  Encontradas: {len(total_offers)} ofertas")

            for offer in total_offers:
                with db_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute(
                        "SELECT id FROM offers WHERE url = ? AND store = ? AND createdAt > datetime('now', '-1 day')",
                        (offer.url, offer.store),
                    )
                    if cursor.fetchone():
                        continue

                    message: str = formatear_mensaje(offer)
                    if send_telegram(message, telegram_config.token, telegram_config.chat_id):
                        ofertas_enviadas += 1
                        print(f"  [ENViado] {offer.name[:50]} - {offer.discount:.0f}%")

                    cursor.execute(
                        """INSERT INTO offers
                           (store, category, url, current_price, original_price, discount, product_name, sent)
                           VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                        (
                            offer.store,
                            offer.category,
                            offer.url,
                            offer.discount_price,
                            offer.price,
                            offer.discount,
                            offer.name,
                        ),
                    )
                    conn.commit()
                await asyncio.sleep(1.5)

        await browser.close()

    print(f"\n{'='*50}")
    print(f"COMPLETADO - Ofertas enviadas a Telegram: {ofertas_enviadas}")
    print(f"{'='*50}")


def formatear_mensaje(prod: Product) -> str:
    ahorro: float = prod.price - prod.discount_price
    return (
        f"{'='*40}\n"
        f"TIENDA: {prod.store}\n"
        f"CATEGORIA: {prod.category}\n\n"
        f"{prod.store}\n\n"
        f"Antes: S/. {prod.price:.2f}\n"
        f"Ahora: S/. {prod.discount_price:.2f}\n"
        f"DESCUENTO: {prod.discount:.0f}% (-S/. {ahorro:.2f})\n\n"
        f"{prod.url}"
    )
