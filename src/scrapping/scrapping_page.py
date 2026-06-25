
import time
from typing import Any
from playwright.async_api import async_playwright
from src.models.store_config import StoreConfig
from src.scrapping.scrapping_factory import ScrappingFactory
from src.util.send_telegram import send_telegram
from src.util.init_db import init_db

async def scrapping_page(stores: list[StoreConfig]):
    conn = init_db()
    cursor = conn.cursor()
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

            total_offers:list[Any] = []

            for url in store_config.urls:
                print(f"\n  URL: {url}")
                
                try:

                    offers = await ScrappingFactory.scrapping(store_name, url, page)
                    total_offers.extend(offers)

                except Exception as e:
                    print(f"Error: {e}")

                time.sleep(3)

            # Enviar ofertas a Telegram
            for offer in total_offers:
                cursor.execute(
                    "SELECT id FROM ofertas WHERE url = ? AND tienda = ? AND fecha > datetime('now', '-1 day')",
                    (offer["url"], offer["tienda"]),
                )
                if cursor.fetchone():
                    continue

                message = formatear_mensaje(offer)
                if send_telegram(message):
                    ofertas_enviadas += 1
                    print(f"  [ENViado] {offer['producto'][:50]} - {offer['descuento_pct']:.0f}%")

                cursor.execute(
                    """INSERT INTO ofertas
                       (tienda, producto, precio_actual, precio_original, descuento_pct, categoria, url, enviado)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                    (
                        offer["tienda"],
                        offer["producto"],
                        offer["precio_actual"],
                        offer["precio_original"],
                        offer["descuento_pct"],
                        offer["categoria"],
                        offer["url"],
                    ),
                )
                conn.commit()
                time.sleep(1.5)

        await browser.close()

    # conn.close()
    print(f"\n{'='*50}")
    print(f"COMPLETADO - Ofertas enviadas a Telegram: {ofertas_enviadas}")
    print(f"{'='*50}")


def formatear_mensaje(prod:Any):
    ahorro = prod["precio_original"] - prod["precio_actual"]
    return (
        f"{'='*40}\n"
        f"TIENDA: {prod['tienda']}\n"
        f"CATEGORIA: {prod['categoria']}\n\n"
        f"{prod['producto']}\n\n"
        f"Antes: S/. {prod['precio_original']:.2f}\n"
        f"Ahora: S/. {prod['precio_actual']:.2f}\n"
        f"DESCUENTO: {prod['descuento_pct']:.0f}% (-S/. {ahorro:.2f})\n\n"
        f"{prod['url']}"
    )
