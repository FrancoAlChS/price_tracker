
import time
from playwright.async_api import async_playwright
from src.scrapping.scrapping_factory import ScrappingFactory
from src.util.send_telegram import send_telegram
from src.util.db_connection import db_connection
from src.models.product import Product
from src.services.scraping_service import ScrapingService

async def scrapping_page():
    scraping_service = ScrapingService()
    stores = scraping_service.get_stores_config()
    telegram_config = scraping_service.get_telegram_config()

    if not telegram_config:
        print("\n[ERROR] No hay configuración de Telegram registrada. Use POST /api/telegram-config/")
        return

    ofertas_enviadas = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="es-PE",
        )
        page = await context.new_page()
        await page.add_init_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')

        for store_config in stores:
            store_name = store_config.name

            if store_config.note != None:
                print(f"\n[OMITIDO] {store_name}: {store_config.note}")
                continue

            print(f"\n{'='*50}")
            print(f"Escaneando: {store_name}")
            print(f"{'='*50}")

            total_offers:list[Product] = []

            for url in store_config.urls:
                print(f"\n  URL: {url}")
                
                try:

                    offers = await ScrappingFactory.scrapping(store_name, url, page)
                    total_offers.extend(offers)

                except Exception as e:
                    print(f"Error: {e}")

                time.sleep(3)

            for offer in total_offers:
                with db_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute(
                        "SELECT id FROM ofertas WHERE url = ? AND tienda = ? AND fecha > datetime('now', '-1 day')",
                        (offer.url, offer.store),
                    )
                    if cursor.fetchone():
                        continue

                    message = formatear_mensaje(offer)
                    if send_telegram(message, telegram_config.token, telegram_config.chat_id):
                        ofertas_enviadas += 1
                        print(f"  [ENViado] {offer.name[:50]} - {offer.discount:.0f}%")

                    cursor.execute(
                        """INSERT INTO ofertas
                           (tienda, producto, precio_actual, precio_original, descuento_pct, categoria, url, enviado)
                           VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                        (
                            offer.store,
                            offer.name,
                            offer.discount_price,
                            offer.price,
                            offer.discount,
                            offer.category,
                            offer.url,
                        ),
                    )
                    conn.commit()
                time.sleep(1.5)

        await browser.close()

    print(f"\n{'='*50}")
    print(f"COMPLETADO - Ofertas enviadas a Telegram: {ofertas_enviadas}")
    print(f"{'='*50}")


def formatear_mensaje(prod:Product):
    ahorro = prod.price - prod.discount_price
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
