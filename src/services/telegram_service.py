from typing import Any
from src.util.db_connection import db_connection

TABLE_NAME = "telegram_config"

class TelegramService:
    def get(self):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = 1")
            row = cursor.fetchone()

            if row:
                return dict(row)
        return None
    
    def create_or_update(self, body: Any):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = 1")
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    f"UPDATE {TABLE_NAME} SET token = ?, chat_id = ?, updatedAt = CURRENT_TIMESTAMP WHERE id = 1",
                    (body["token"], body["chat_id"])
                )
            else:
                cursor.execute(
                    f"INSERT INTO {TABLE_NAME} (id, token, chat_id) VALUES (1, ?, ?)",
                    (body["token"], body["chat_id"])
                )
            
            conn.commit()

        return self.get()
