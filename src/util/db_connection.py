import sqlite3

def db_connection():
    conn = sqlite3.connect("precios.db")

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON;")

    return conn