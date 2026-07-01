from src.util.db_connection import db_connection
from src.models.store_config import StoreConfig
from src.models.telegram_config import TelegramConfig
from src.scrapping.store_enum import Stores


class ScrapingService:
    def get_stores_config(self) -> list[StoreConfig]:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.name as store_name, l.url
                FROM links l
                JOIN stores s ON l.store_id = s.id
            """)
            rows = cursor.fetchall()

        stores_map: dict[str, list[str]] = {}
        notes_map: dict[str, str | None] = {}

        for row in rows:
            store_name = row["store_name"]
            url = row["url"]

            if store_name not in stores_map:
                stores_map[store_name] = []
                notes_map[store_name] = None

            stores_map[store_name].append(url)

        result: list[StoreConfig] = []
        for store_name, urls in stores_map.items():
            try:
                store_enum = Stores(store_name)
            

                result.append(StoreConfig(
                    name=store_enum,
                    urls=urls,
                    note=notes_map[store_name]
                ))

            except ValueError:
                print(f"La tienda {store_name} aún no está permitida")

        return result

    def get_telegram_config(self) -> TelegramConfig | None:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM telegram_config WHERE id = 1")
            row = cursor.fetchone()

            if row:
                return TelegramConfig(
                    id=row["id"],
                    token=row["token"],
                    chat_id=row["chat_id"]
                )
        return None
