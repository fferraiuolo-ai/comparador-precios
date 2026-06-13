from flask import Flask, render_template, request, jsonify import os
import sqlite3
from scraper import correr_scraping

app = Flask(__name__)

def query_db(query, args=(), one=False):
    conn = sqlite3.connect('precios.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(query, args)
    rv = c.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    productos = query_db('SELECT * FROM productos')
    return render_template('index.html', productos=productos)

@app.route('/producto/<int:id>')
def producto(id):
    prod = query_db('SELECT * FROM productos WHERE id = ?', [id], one=True)
    precios_raw = query_db('''
        SELECT tienda, precio, fecha 
        FROM precios 
        WHERE producto_id = ? 
        ORDER BY fecha DESC
    ''', [id])
    precios = [dict(p) for p in precios_raw]
    return render_template('producto.html', producto=prod, precios=precios)

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if request.method == 'POST':
        conn = sqlite3.connect('precios.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO productos (nombre, url_puppis, url_naturallife, url_nutrican, url_drovenort, variante_nutrican)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            request.form['nombre'],
            request.form['url_puppis'],
            request.form['url_naturallife'],
            request.form['url_nutrican'],
            request.form['url_drovenort'],
            request.form['variante_nutrican'],
        ))
        conn.commit()
        conn.close()
        return index()
    return render_template('agregar.html')

@app.route('/eliminar/<int:id>')
def eliminar(id):
    conn = sqlite3.connect('precios.db')
    c = conn.cursor()
    c.execute('DELETE FROM precios WHERE producto_id = ?', [id])
    c.execute('DELETE FROM productos WHERE id = ?', [id])
    conn.commit()
    conn.close()
    return index()

@app.route('/scraping')
def scraping():
    correr_scraping()
    return jsonify({'status': 'ok', 'mensaje': 'Scraping completado'})

if __name__ == '__main__':
app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)