from playwright.sync_api import sync_playwright
import sqlite3
from datetime import datetime
import re

def limpiar_precio(texto):
    if not texto:
        return None
    numeros = re.sub(r'[^\d]', '', texto)
    try:
        val = float(numeros)
        return val if val > 100 else None
    except:
        return None

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
            return limpiar_precio(texto)
    except Exception as e:
        print(f"  Error: {e}")
    return None

def scrape_precio_vtex(page, url):
    try:
        page.goto(url, timeout=30000)
        page.wait_for_load_state('networkidle', timeout=15000)
        elemento = page.query_selector('[class*="sellingPrice"]')
        if elemento:
            texto = elemento.inner_text().strip()
            return limpiar_precio(texto)
    except Exception as e:
        print(f"  Error: {e}")
    return None

def scrape_precio_naturallife(page, url):
    try:
        page.goto(url, timeout=30000)
        page.wait_for_load_state('networkidle', timeout=15000)
        elementos = page.query_selector_all('[class*="price"]')
        for el in elementos:
            clase = el.get_attribute('class') or ''
            if 'flexRow--product-prices' in clase:
                texto = el.inner_text().strip()
                lineas = texto.split('\n')
                for linea in lineas:
                    if '$' in linea and 'impuesto' not in linea.lower() and 'lista' not in linea.lower():
                        precio = limpiar_precio(linea)
                        if precio:
                            return precio
    except Exception as e:
        print(f"  Error: {e}")
    return None

def scrape_precio_drovenort(page, url):
    try:
        page.goto(url, timeout=30000)
        page.wait_for_load_state('networkidle', timeout=15000)
        elemento = page.query_selector('.text-no-wrap.mr-2.price')
        if elemento:
            texto = elemento.inner_text().strip()
            return limpiar_precio(texto)
    except Exception as e:
        print(f"  Error: {e}")
    return None

def guardar_precio(producto_id, tienda, precio):
    conn = sqlite3.connect('precios.db')
    c = conn.cursor()
    c.execute(
        'INSERT INTO precios (producto_id, tienda, precio, fecha) VALUES (?, ?, ?, ?)',
        (producto_id, tienda, precio, datetime.now())
    )
    conn.commit()
    conn.close()

def obtener_productos():
    conn = sqlite3.connect('precios.db')
    c = conn.cursor()
    c.execute('SELECT * FROM productos')
    productos = c.fetchall()
    conn.close()
    return productos

def correr_scraping():
    productos = obtener_productos()
    if not productos:
        print("No hay productos cargados todavía")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for prod in productos:
            id, nombre, url_puppis, url_naturallife, url_nutrican, url_drovenort, variante_nutrican = prod
            print(f"Scrapeando: {nombre}")

            if url_puppis:
                precio = scrape_precio_vtex(page, url_puppis)
                guardar_precio(id, 'puppis', precio)
                print(f"  puppis: {precio}")

            if url_naturallife:
                precio = scrape_precio_naturallife(page, url_naturallife)
                guardar_precio(id, 'naturallife', precio)
                print(f"  naturallife: {precio}")

            if url_nutrican:
                precio = scrape_precio_meta(page, url_nutrican, variante=variante_nutrican)
                guardar_precio(id, 'nutrican', precio)
                print(f"  nutrican: {precio}")

            if url_drovenort:
                precio = scrape_precio_drovenort(page, url_drovenort)
                guardar_precio(id, 'drovenort', precio)
                print(f"  drovenort: {precio}")

        browser.close()
    print("Scraping completado")

if __name__ == '__main__':
    correr_scraping()