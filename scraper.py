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
    texto = texto.strip()
    # Formato argentino: puntos como miles, coma como decimal (ej: $119.445,50)
    if re.search(r'\d\.\d{3}', texto):
        texto = texto.replace('.', '').replace(',', '.')
    else:
        texto = texto.replace(',', '')
    numeros = re.sub(r'[^\d.]', '', texto)
    try:
        val = float(numeros)
        return val if val > 100 else None
    except:
        return None

def scrape_precio_vtex(page, url):
    try:
        page.goto(url, timeout=30000)
        page.wait_for_load_state('networkidle', timeout=15000)
        page.wait_for_timeout(2000)
        # Si el SKU seleccionado no tiene stock, no tomar precio
        sin_stock = page.query_selector('[class*="skuSelectorItem--selected"][class*="unavailable"]')
        if sin_stock:
            print(f"  Sin stock, precio omitido")
            return 'sin_stock', None
        elemento = page.query_selector('[class*="sellingPrice"]')
        if elemento:
            texto = elemento.inner_text().strip()
            return limpiar_precio(texto), None
    except Exception as e:
        print(f"  Error: {e}")
    return None, None

def scrape_precio_kangoopet(page, url):
    try:
        page.goto(url, timeout=30000)
        page.wait_for_load_state('networkidle', timeout=15000)
        # El primer sellingPrice es siempre el precio del producto principal
        elem_venta = page.query_selector('[class*="sellingPrice"]')
        precio_venta = limpiar_precio(elem_venta.inner_text().strip()) if elem_venta else None
        # El primer listPrice es el precio tachado del mismo producto (si existe)
        elem_lista = page.query_selector('[class*="listPrice"]')
        precio_lista = limpiar_precio(elem_lista.inner_text().strip()) if elem_lista else None
        # Solo mostrar listPrice si es mayor que sellingPrice (descuento real)
        if precio_lista and precio_venta and precio_lista > precio_venta * 1.05:
            return precio_lista, precio_venta
        return precio_venta, None
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
        precio_lista = None
        precio_desc = None
        if elemento:
            precio_lista = limpiar_precio(elemento.inner_text().strip())
        elem_desc = page.query_selector('.js-payment-discount-price-product-container')
        if elem_desc:
            precio_desc = limpiar_precio(elem_desc.inner_text().strip())
        return precio_lista, precio_desc
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

errores_scraping = []

def procesar_precio(producto_id, nombre, tienda, precio_nuevo, precio_descuento, url):
    precio_anterior = obtener_ultimo_precio(producto_id, tienda)

    if precio_nuevo == 'sin_stock':
        return  # Sin stock no es un error, simplemente no se guarda precio
    if precio_nuevo is None:
        msg = f"URL rota: {nombre} en {tienda}"
        errores_scraping.append(msg)
        if precio_anterior is not None:
            enviar_alerta_url_rota(nombre, tienda, url)
    else:
        guardar_precio(producto_id, tienda, precio_nuevo, precio_descuento)
        if precio_anterior and precio_anterior != precio_nuevo:
            enviar_alerta(nombre, tienda, precio_anterior, precio_nuevo, url)

def guardar_log_scraping(estado, detalle=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO scraping_log (fecha, estado, detalle) VALUES (NOW(), %s, %s)', (estado, detalle))
    conn.commit()
    conn.close()

def scrape_producto(page, prod):
    id, nombre, url_puppis, url_naturallife, url_nutrican, url_drovenort, variante_nutrican, url_kangoopet = prod[:8] if len(prod) >= 8 else (*prod, None)
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

    if url_kangoopet:
        precio, desc = scrape_precio_kangoopet(page, url_kangoopet)
        procesar_precio(id, nombre, 'kangoopet', precio, desc, url_kangoopet)
        print(f"  kangoopet: lista={precio} descuento={desc}")

def correr_scraping_producto(prod):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        scrape_producto(page, prod)
        browser.close()
    print("Scraping completado")

def correr_scraping():
    global errores_scraping
    errores_scraping = []

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

    if errores_scraping:
        detalle = '\n'.join(errores_scraping)
        guardar_log_scraping('error', detalle)
    else:
        guardar_log_scraping('ok')

    print("Scraping completado")

if __name__ == '__main__':
    correr_scraping()