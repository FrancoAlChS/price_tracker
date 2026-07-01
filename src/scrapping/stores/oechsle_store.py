from playwright.async_api import Page
from src.util.pase_numero import parse_numero
from src.config.enviroments import MINIMUN_DISCOUNT
import re
from src.scrapping.stores.store_page import StorePage
from src.models.product import Product
from src.scrapping.store_enum import Stores

class OechsleStore(StorePage):

    async def scrapping(self, page: Page, url: str) -> list[Product]:
        products: list[Product] = []
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(2000)

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
        category = cat_match.group(1).replace("-", " ").title() if cat_match else "General"

        for item in items:
            try:
                name = item.get("name", "")
                if not name:
                    continue

                current_price = parse_numero(item.get("currentPrice", ""))
                original_price = parse_numero(item.get("originalPrice", ""))

                if not current_price:
                    continue
                if not original_price:
                    original_price = current_price

                discount = ((original_price - current_price) / original_price * 100) if original_price > 0 else 0

                if discount < MINIMUN_DISCOUNT:
                    continue

                href = item.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://www.oechsle.pe{href}"


                product = Product(
                    Stores.OECHSLE, 
                    name[:100], 
                    original_price, 
                    round(discount, 1), 
                    current_price, 
                    category, 
                    href)

                products.append(product)
              
            except Exception:
                continue

        return products