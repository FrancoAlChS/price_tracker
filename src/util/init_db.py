import sqlite3

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