from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("=== NUTRICAN ===")
    page.goto('https://www.nutrican.com.ar/productos/Royal-Canin-Medium-Adulto/', timeout=30000)
    page.wait_for_load_state('networkidle', timeout=15000)
    with open('nutrican.html', 'w', encoding='utf-8') as f:
        f.write(page.content())
    print("Guardado en nutrican.html")

    print("=== NATURAL LIFE ===")
    page.goto('https://www.natural-life.com.ar/royal-canin-perro-adulto-mediano-x-15-kg/p', timeout=30000)
    page.wait_for_load_state('networkidle', timeout=15000)
    with open('naturallife.html', 'w', encoding='utf-8') as f:
        f.write(page.content())
    print("Guardado en naturallife.html")

    browser.close()