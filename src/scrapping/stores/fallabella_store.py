import json
import re
from typing import Any
from playwright.async_api import Page
from src.util.pase_numero import parse_numero
from src.config.enviroments import MINIMUN_DISCOUNT
from src.scrapping.stores.store_page import StorePage

class FallabellaStore(StorePage):
    async def scrapping(self, page: Page, url: str) -> list[Any]:
        productos: list[Any] = []
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(4000)

        next_data = await page.evaluate("""
            () => {
                const el = document.getElementById('__NEXT_DATA__');
                return el ? el.textContent : null;
            }
        """)
        if not next_data:
            return productos

        try:
            data = json.loads(next_data)
        except json.JSONDecodeError:
            return productos

        results = data.get("props", {}).get("pageProps", {}).get("results", [])
        if not results:
            return productos

        for item in results:
            try:
                nombre = item.get("displayName", "Sin nombre")
                prices = item.get("prices", [])

                # Buscar precio de oferta (eventPrice o internetPrice) y precio normal (normalPrice)
                precio_actual = None
                precio_original = None

                for p in prices:
                    ptype = p.get("type", "")
                    pval = p.get("price", [])
                    if pval:
                        val = parse_numero(pval[0])
                    else:
                        val = None

                    if ptype in ("eventPrice", "internetPrice") and val:
                        precio_actual = val
                    elif ptype == "normalPrice" and val:
                        precio_original = val

                if not precio_actual:
                    continue

                if not precio_original:
                    precio_original = precio_actual

                # Usar discountBadge si existe
                badge = item.get("discountBadge", {}).get("label", "")
                badge_match = re.search(r"(\d+)", badge)
                if badge_match:
                    descuento = float(badge_match.group(1))
                else:
                    descuento = ((precio_original - precio_actual) / precio_original * 100) if precio_original > 0 else 0

                if descuento <  MINIMUN_DISCOUNT:
                    continue

                product_url = item.get("url", "")
                if product_url and not product_url.startswith("http"):
                    product_url = f"https://www.falabella.com.pe{product_url}"

                # Categoria desde la URL
                cat_match = re.search(r"/category/[^/]+/(.+?)(?:\?|$)", url)
                categoria = cat_match.group(1).replace("-", " ").title() if cat_match else "General"

                productos.append({
                    "tienda": "Falabella",
                    "producto": nombre[:100],
                    "precio_actual": precio_actual,
                    "precio_original": precio_original,
                    "descuento_pct": descuento,
                    "categoria": categoria,
                    "url": product_url,
                })

            except Exception:
                continue

        return productos