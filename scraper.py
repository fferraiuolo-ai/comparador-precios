from playwright.sync_api import sync_playwright
import psycopg2
import os
from datetime import datetime
import re
from alertas import enviar_alerta, enviar_alerta_url_rota

def get_conn():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return psycopg2.connect(db_url)
    return psycopg2.connect('postgresql://comparador_db_d60h_user:bOEPAQ9cVlgJfc9uqWvUzbvWf6wLhJD3@dpg-d8mkph8js32c73cqeoqg-a.oregon-postgres.render.com/comparador_db_d60h')

def limpiar_precio(texto):
    if not texto:
        return None
    numeros = re.sub(r'[^\d]', '', texto)
    try:
        val = float(numeros)
        return val if val > 100 else None
    except:
        return None

def scrape_precio_vtex(page, url):
    try:
        page.goto(url, timeout=30000)
        page.wait_for_load_state('networkidle', timeout=15000)
        elemento = page.query_selector('[class*="sellingPrice"]')
        if elemento:
            texto = elemento.inner_text().strip()
            return limpiar_precio(texto), None
    except Exception as e:
        print(f"  Error: {e}")
    return None, None

def scrape_precio_naturallife(page, url):
    try:
        page.goto(url, timeout=30000)
        page.wait_for_load_state('networkidle', timeout=15000)
        precio_lista = None
        precio_descuento = None

        elementos = page.query_selector_all('[class*="price"]')
        for el in elementos:
            clase = el.get_attribute('class') or ''
            if 'flexRow--product-prices' in clase:
                texto = el.inner_text().strip()
                lineas = texto.split('\n')
                for i, linea in enumerate(lineas):
                    linea = linea.strip()
                    if 'Lista' in linea:
                        for j in range(i+1, min(i+3, len(lineas))):
                            p = limpiar_precio(lineas[j])
                            if p:
                                precio_lista = p
                                break
                    if 'Débito' in linea or 'Credito' in linea or 'Crédito' in linea:
                        for j in range(i+1, min(i+3, len(lineas))):
                            p = limpiar_precio(lineas[j])
                            if p:
                                precio_descuento = p
                                break
                break

        return precio_lista, precio_descuento
    except Exception as e:
        print(f"  Error: {e}")
    return None, None

def scrape_precio_meta(page, url, variante=None):
    try:
        page.goto(url, timeout=30000)
        page.wait_for_load_state('networkidle', timeout=15000)
        if variante:
            botones = page.query_selector_all('a.js-insta-variant')
            for boton in botones:
                if variante in boton.inner_text():
                    boton.click()
                    page.wait_for_timeout(2000)
                    break
        elemento = page.query_selector('.js-price-display')
        if elemento:
            texto = elemento.inner_text().strip()
            return limpiar_precio(texto), None
    except Exception as e:
        print(f"  Error: {e}")
    return None, None

def scrape_precio_drovenort(page, url):
    try:
        page.goto(url, timeout=30000)
        page.wait_for_load_state('networkidle', timeout=15000)
        elemento = page.query_selector('.text-no-wrap.mr-2.price')
        if elemento:
            texto = elemento.inner_text().strip()
            return limpiar_precio(texto), None
    except Exception as e:
        print(f"  Error: {e}")
    return None, None

def obtener_ultimo_precio(producto_id, tienda):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        SELECT precio FROM precios
        WHERE producto_id = %s AND tienda = %s
        ORDER BY fecha DESC LIMIT 1
    ''', (producto_id, tienda))
    resultado = c.fetchone()
    conn.close()
    return resultado[0] if resultado else None

def guardar_precio(producto_id, tienda, precio, precio_descuento=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO precios (producto_id, tienda, precio, precio_descuento, fecha) VALUES (%s, %s, %s, %s, %s)',
        (producto_id, tienda, precio, precio_descuento, datetime.now())
    )
    conn.commit()
    conn.close()

def obtener_productos():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM productos')
    productos = c.fetchall()
    conn.close()
    return productos

def procesar_precio(producto_id, nombre, tienda, precio_nuevo, precio_descuento, url):
    precio_anterior = obtener_ultimo_precio(producto_id, tienda)
    
    if precio_nuevo is None:
        if precio_anterior is not None:
            enviar_alerta_url_rota(nombre, tienda, url)
    else:
        guardar_precio(producto_id, tienda, precio_nuevo, precio_descuento)
        if precio_anterior and precio_anterior != precio_nuevo:
            enviar_alerta(nombre, tienda, precio_anterior, precio_nuevo)

def scrape_producto(page, prod):
    id, nombre, url_puppis, url_naturallife, url_nutrican, url_drovenort, variante_nutrican = prod
    print(f"Scrapeando: {nombre}")

    if url_puppis:
        precio, desc = scrape_precio_vtex(page, url_puppis)
        procesar_precio(id, nombre, 'puppis', precio, desc, url_puppis)
        print(f"  puppis: {precio}")

    if url_naturallife:
        precio, desc = scrape_precio_naturallife(page, url_naturallife)
        procesar_precio(id, nombre, 'naturallife', precio, desc, url_naturallife)
        print(f"  naturallife: lista={precio} descuento={desc}")

    if url_nutrican:
        precio, desc = scrape_precio_meta(page, url_nutrican, variante=variante_nutrican)
        procesar_precio(id, nombre, 'nutrican', precio, desc, url_nutrican)
        print(f"  nutrican: {precio}")

    if url_drovenort:
        precio, desc = scrape_precio_drovenort(page, url_drovenort)
        procesar_precio(id, nombre, 'drovenort', precio, desc, url_drovenort)
        print(f"  drovenort: {precio}")

def correr_scraping_producto(prod):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        scrape_producto(page, prod)
        browser.close()
    print("Scraping completado")

def correr_scraping():
    productos = obtener_productos()
    if not productos:
        print("No hay productos cargados todavía")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for prod in productos:
            scrape_producto(page, prod)
        browser.close()
    print("Scraping completado")

if __name__ == '__main__':
    correr_scraping()