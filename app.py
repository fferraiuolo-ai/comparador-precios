from flask import Flask, render_template, request, jsonify
import psycopg2
import psycopg2.extras
import os
from scraper import correr_scraping

app = Flask(__name__)

def get_conn():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return psycopg2.connect(db_url)
    return psycopg2.connect('postgresql://comparador_db_d60h_user:bOEPAQ9cVlgJfc9uqWvUzbvWf6wLhJD3@dpg-d8mkph8js32c73cqeoqg-a.oregon-postgres.render.com/comparador_db_d60h')

def query_db(query, args=(), one=False):
    conn = get_conn()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute(query, args)
    rv = c.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    conn = get_conn()
    c = conn.cursor()
    c.execute(query, args)
    conn.commit()
    conn.close()

def obtener_ultimos_precios(producto_id):
    filas = query_db('''
        SELECT DISTINCT ON (tienda) tienda, precio
        FROM precios
        WHERE producto_id = %s
        ORDER BY tienda, fecha DESC
    ''', [producto_id])
    return {f['tienda']: f['precio'] for f in filas}

@app.route('/')
def index():
    productos_raw = query_db('SELECT * FROM productos ORDER BY nombre')
    productos = []
    for p in productos_raw:
        prod = dict(p)
        prod['precios'] = obtener_ultimos_precios(p['id'])
        productos.append(prod)
    return render_template('index.html', productos=productos)

@app.route('/producto/<int:id>')
def producto(id):
    prod = query_db('SELECT * FROM productos WHERE id = %s', [id], one=True)
    precios_raw = query_db('''
        SELECT tienda, precio, fecha 
        FROM precios 
        WHERE producto_id = %s
        ORDER BY fecha DESC
    ''', [id])
    precios = [{**dict(p), 'fecha': str(p['fecha'])} for p in precios_raw]
    return render_template('producto.html', producto=prod, precios=precios)

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if request.method == 'POST':
        execute_db('''
            INSERT INTO productos (nombre, url_puppis, url_naturallife, url_nutrican, url_drovenort, variante_nutrican)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            request.form['nombre'],
            request.form['url_puppis'],
            request.form['url_naturallife'],
            request.form['url_nutrican'],
            request.form['url_drovenort'],
            request.form['variante_nutrican'],
        ))
        return index()
    return render_template('agregar.html')

@app.route('/eliminar/<int:id>')
def eliminar(id):
    execute_db('DELETE FROM precios WHERE producto_id = %s', [id])
    execute_db('DELETE FROM productos WHERE id = %s', [id])
    return index()

@app.route('/scraping')
def scraping():
    correr_scraping()
    return jsonify({'status': 'ok', 'mensaje': 'Scraping completado'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)