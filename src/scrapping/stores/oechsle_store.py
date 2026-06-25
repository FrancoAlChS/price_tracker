from playwright.async_api import Page
from src.util.pase_numero import parse_numero
from src.config.enviroments import MINIMUN_DISCOUNT
from typing import Any
import re
from src.scrapping.stores.store_page import StorePage

class OechsleStore(StorePage):

    async def scrapping(self, page: Page, url: str) -> list[Any]:
        productos: list[Any] = []
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        items = await page.evaluate("""() => {
            const resultItems = document.querySelectorAll('.resultItem');
            const results = [];
            resultItems.forEach(el => {
                const link = el.querySelector('a.resultItem__link');
                const boxPrice = el.querySelector('.box-price');
                const listPrice = el.querySelector('.price.priceList');
                const priceText = el.querySelector('.xoh.price');

                results.push({
                    id: el.getAttribute('data-product-id'),
                    name: el.getAttribute('data-product-name'),
                    href: link ? link.getAttribute('href') : null,
                    currentPrice: boxPrice ? boxPrice.textContent.trim() : null,
                    originalPrice: listPrice ? listPrice.textContent.trim() : null,
                    discountText: priceText ? priceText.textContent.trim() : null,
                });
            });
            return results;
        }""")

        cat_match = re.search(r"oechsle\.pe/([^/]+)", url)
        categoria = cat_match.group(1).replace("-", " ").title() if cat_match else "General"

        for item in items:
            try:
                nombre = item.get("name", "")
                if not nombre:
                    continue

                precio_actual = parse_numero(item.get("currentPrice", ""))
                precio_original = parse_numero(item.get("originalPrice", ""))

                if not precio_actual:
                    continue
                if not precio_original:
                    precio_original = precio_actual

                descuento = ((precio_original - precio_actual) / precio_original * 100) if precio_original > 0 else 0

                if descuento < MINIMUN_DISCOUNT:
                    continue

                href = item.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://www.oechsle.pe{href}"

                productos.append({
                    "tienda": "Oechsle",
                    "producto": nombre[:100],
                    "precio_actual": precio_actual,
                    "precio_original": precio_original,
                    "descuento_pct": round(descuento, 1),
                    "categoria": categoria,
                    "url": href,
                })

            except Exception:
                continue

        return productos