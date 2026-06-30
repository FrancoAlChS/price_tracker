from typing import Any
from src.util.db_connection import db_connection


TABLE_NAME = "links"

class LinkService:
    def list(self):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {TABLE_NAME}")
            rows = cursor.fetchall()

            offers = [dict(row) for row in rows]

        return offers
    
    def create(self, body:Any):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO {TABLE_NAME} (name, url, store_id) VALUES (?, ?, ?)", (body["name"], body["url"], body["store_id"]))
            
            conn.commit()

        return body
    
    def update(self, id:int, body:Any):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE {TABLE_NAME} SET name = ?, url = ?, store_id = ? WHERE id = ?", (body["name"], body["url"], body["store_id"], id))
            
            conn.commit()

        return body
    
    def delete(self, id:int):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE id = ?", (str(id)))
            conn.commit()

        return "Eliminado correctamente"