from flask import Flask
from src.controllers.store_controller import store_controller
from src.controllers.link_controller import link_controller
from src.util.db_connection import db_connection

app = Flask(__name__)

app.register_blueprint(store_controller, url_prefix="/api/stores")
app.register_blueprint(link_controller, url_prefix="/api/links")

@app.route('/')
def home():
    return '¡Hola desde Flask y UV!'



def init_db():
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                url TEXT NOT NULL,
                store_id INTEGER NOT NULL,
                createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id)
            )
        """)
        conn.commit()
        return conn


if __name__ == '__main__':
    init_db()
    app.run(port=3000, debug=True)
