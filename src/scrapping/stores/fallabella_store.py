import json
import re
from playwright.async_api import Page
from src.util.pase_numero import parse_numero
from src.config.enviroments import MINIMUN_DISCOUNT
from src.scrapping.stores.store_page import StorePage
from src.models.product import Product
from src.scrapping.store_enum import Stores

class FallabellaStore(StorePage):
    async def scrapping(self, page: Page, url: str) -> list[Product]:
        products: list[Product] = []
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(4000)

        next_data = await page.evaluate("""
            () => {
                const el = document.getElementById('__NEXT_DATA__');
                return el ? el.textContent : null;
            }
        """)
        if not next_data:
            return products

        try:
            data = json.loads(next_data)
        except json.JSONDecodeError:
            return products

        results = data.get("props", {}).get("pageProps", {}).get("results", [])
        if not results:
            return products

        for item in results:
            try:
                name = item.get("displayName", "Sin nombre")
                prices = item.get("prices", [])

                # Buscar precio de oferta (eventPrice o internetPrice) y precio normal (normalPrice)
                current_price = None
                original_price = None

                for p in prices:
                    ptype = p.get("type", "")
                    pval = p.get("price", [])
                    if pval:
                        val = parse_numero(pval[0])
                    else:
                        val = None

                    if ptype in ("eventPrice", "internetPrice") and val:
                        current_price = val
                    elif ptype == "normalPrice" and val:
                        original_price = val

                if not current_price:
                    continue

                if not original_price:
                    original_price = current_price

                # Usar discountBadge si existe
                badge = item.get("discountBadge", {}).get("label", "")
                badge_match = re.search(r"(\d+)", badge)
                if badge_match:
                    discount = float(badge_match.group(1))
                else:
                    discount = ((original_price - current_price) / original_price * 100) if original_price > 0 else 0

                if discount <  MINIMUN_DISCOUNT:
                    continue

                product_url = item.get("url", "")
                if product_url and not product_url.startswith("http"):
                    product_url = f"https://www.falabella.com.pe{product_url}"

                # Categoria desde la URL
                cat_match = re.search(r"/category/[^/]+/(.+?)(?:\?|$)", url)
                category = cat_match.group(1).replace("-", " ").title() if cat_match else "General"


                product = Product(
                    Stores.FALLABELLA, 
                    name[:100],
                    original_price,
                    discount,
                    current_price,
                    category,
                    product_url)
                
                products.append(product)

            except Exception:
                continue

        return products