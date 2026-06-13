from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto('https://www.nutrican.com.ar/productos/Royal-Canin-Medium-Adulto/', timeout=30000)
    page.wait_for_load_state('networkidle', timeout=15000)

    # Hacer clic en 15 Kg
    botones = page.query_selector_all('a.js-insta-variant')
    for boton in botones:
        if '15' in boton.inner_text():
            print("Clickeando 15 Kg...")
            boton.click()
            page.wait_for_timeout(2000)
            break

    # Buscar precio después del clic
    for selector in ['.js-price-display', '.product-price', '[class*="precio"]', '[class*="price"]', '.price']:
        elementos = page.query_selector_all(selector)
        for el in elementos[:2]:
            texto = el.inner_text().strip()
            if texto and '$' in texto:
                print(f"[{selector}] {repr(texto[:60])}")

    browser.close()