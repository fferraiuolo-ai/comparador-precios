import sqlite3

def init_db():
    conn = sqlite3.connect('precios.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            tienda TEXT NOT NULL,
            precio REAL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    ''')

    # Agregar columna si ya existe la tabla sin ese campo
    try:
        c.execute('ALTER TABLE productos ADD COLUMN variante_nutrican TEXT')
    except:
        pass
    
    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente")

if __name__ == '__main__':
    init_db()