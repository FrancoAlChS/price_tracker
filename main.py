from flask import Flask
from flask_cors import CORS
from src.controllers.store_controller import store_controller
from src.controllers.link_controller import link_controller
from src.controllers.telegram_controller import telegram_controller
from src.util.db_connection import db_connection
from src.util.scheduler import start_scheduler
from src.config.enviroments import FRONTEND_URL

app = Flask(__name__)
# CORS(app, 
#      resources={r"/*": {"origins": [FRONTEND_URL]}}, 
#      methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#      allow_headers=["Content-Type", "Authorization"])

CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(store_controller, url_prefix="/api/stores")
app.register_blueprint(link_controller, url_prefix="/api/links")
app.register_blueprint(telegram_controller, url_prefix="/api/telegram-config")

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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telegram_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                token TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store TEXT,
                category TEXT,
                url TEXT NOT NULL,
                current_price REAL,
                original_price REAL,
                discount REAL,
                product_name TEXT,
                sent BOOLEAN DEFAULT 0,
                createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        return conn


if __name__ == '__main__':
    init_db()
    start_scheduler()
    app.run(port=4000, debug=True, use_reloader=False)
