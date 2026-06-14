import sqlite3
import requests
import time
import json
import re
from playwright.sync_api import sync_playwright
from src.config.enviroments import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

DESCUENTO_MINIMO = 50


# Paginas de categoria por tienda
TIENDAS = [
    {
        "tienda": "Falabella",
        "urls": [
            "https://www.falabella.com.pe/falabella-pe/category/cat1470534/Zapatillas-urbanas-mujer",
            
        ],
    },
    {
        "tienda": "Oechsle",
        "urls": [
            "https://www.oechsle.pe/tecnologia/",
            
        ],
    },
    {
        "tienda": "Ripley",
        "urls": [
            "https://simple.ripley.com.pe/",
        ],
        "notas": "Ripley bloquea scraping automatizado (Cloudflare). Se omite por ahora.",
    },
]


def init_db():
    conn = sqlite3.connect("precios.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ofertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tienda TEXT,
            producto TEXT,
            precio_actual REAL,
            precio_original REAL,
            descuento_pct REAL,
            categoria TEXT,
            url TEXT,
            enviado BOOLEAN DEFAULT 0,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"  Error Telegram: {e}")
        return False


def parse_numero(texto):
    if not texto:
        return None
    limpio = re.sub(r"[^\d.]", "", texto.replace(",", ""))
    match = re.search(r"(\d+\.?\d*)", limpio)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


# ── FALABELLA ──────────────────────────────────────────────────────────────
# Estructura: __NEXT_DATA__ > props.pageProps.results[]
# Cada item tiene: prices[] (array con types: eventPrice, internetPrice, normalPrice, cmrPrice)
#                  discountBadge.label = "-48%"

def extraer_falabella(page, url):
    productos = []
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)

    next_data = page.evaluate("""
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

            if descuento < DESCUENTO_MINIMO:
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


# ── OECHSLE ────────────────────────────────────────────────────────────────
# Estructura HTML: div.resultItem con data-product-id, data-product-name
# Precios: .box-price = precio actual, .price.priceList = precio original
# Descuento en texto: "-26%" visible en .xoh.price

def extraer_oechsle(page, url):
    productos = []
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)

    items = page.evaluate("""() => {
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

            if descuento < DESCUENTO_MINIMO:
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


# ── MAIN ───────────────────────────────────────────────────────────────────

def formatear_mensaje(prod):
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


def escanear_tiendas():
    conn = init_db()
    cursor = conn.cursor()
    ofertas_enviadas = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="es-PE",
        )
        page = context.new_page()
        page.add_init_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')

        for tienda_config in TIENDAS:
            tienda_nombre = tienda_config["tienda"]

            if "notas" in tienda_config:
                print(f"\n[OMITIDO] {tienda_nombre}: {tienda_config['notas']}")
                continue

            print(f"\n{'='*50}")
            print(f"Escaneando: {tienda_nombre}")
            print(f"{'='*50}")

            todas_ofertas = []

            for url in tienda_config["urls"]:
                print(f"\n  URL: {url}")
                try:
                    if tienda_nombre == "Falabella":
                        ofertas = extraer_falabella(page, url)
                    elif tienda_nombre == "Oechsle":
                        ofertas = extraer_oechsle(page, url)
                    else:
                        ofertas = []

                    print(f"  Ofertas >= {DESCUENTO_MINIMO}%: {len(ofertas)}")
                    todas_ofertas.extend(ofertas)

                except Exception as e:
                    print(f"  Error: {e}")

                time.sleep(3)

            # Enviar ofertas a Telegram
            for oferta in todas_ofertas:
                cursor.execute(
                    "SELECT id FROM ofertas WHERE url = ? AND tienda = ? AND fecha > datetime('now', '-1 day')",
                    (oferta["url"], oferta["tienda"]),
                )
                if cursor.fetchone():
                    continue

                mensaje = formatear_mensaje(oferta)
                if enviar_telegram(mensaje):
                    ofertas_enviadas += 1
                    print(f"  [ENViado] {oferta['producto'][:50]} - {oferta['descuento_pct']:.0f}%")

                cursor.execute(
                    """INSERT INTO ofertas
                       (tienda, producto, precio_actual, precio_original, descuento_pct, categoria, url, enviado)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                    (
                        oferta["tienda"],
                        oferta["producto"],
                        oferta["precio_actual"],
                        oferta["precio_original"],
                        oferta["descuento_pct"],
                        oferta["categoria"],
                        oferta["url"],
                    ),
                )
                conn.commit()
                time.sleep(1.5)

        browser.close()

    conn.close()
    print(f"\n{'='*50}")
    print(f"COMPLETADO - Ofertas enviadas a Telegram: {ofertas_enviadas}")
    print(f"{'='*50}")


if __name__ == "__main__":
    init_db()
    escanear_tiendas()
