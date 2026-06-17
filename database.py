import psycopg2
import os

def get_conn():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return psycopg2.connect(db_url)
    return psycopg2.connect('postgresql://comparador_db_d60h_user:bOEPAQ9cVlgJfc9uqWvUzbvWf6wLhJD3@dpg-d8mkph8js32c73cqeoqg-a.oregon-postgres.render.com/comparador_db_d60h')

def init_db():
    conn = get_conn()
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            url_puppis TEXT,
            url_naturallife TEXT,
            url_nutrican TEXT,
            url_drovenort TEXT,
            variante_nutrican TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS precios (
            id SERIAL PRIMARY KEY,
            producto_id INTEGER,
            tienda TEXT NOT NULL,
            precio REAL,
            precio_descuento REAL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    ''')

    try:
        c.execute('ALTER TABLE precios ADD COLUMN precio_descuento REAL')
        conn.commit()
    except:
        conn.rollback()

    try:
        c.execute('ALTER TABLE productos ADD COLUMN url_kangoopet TEXT')
        conn.commit()
    except:
        conn.rollback()

    c.execute('''
        CREATE TABLE IF NOT EXISTS scraping_log (
            id SERIAL PRIMARY KEY,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            estado TEXT NOT NULL,
            detalle TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente")

if __name__ == '__main__':
    init_db()