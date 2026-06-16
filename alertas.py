import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = 'fferraiuolo@puppis.com.ar'
GMAIL_PASSWORD = 'lehd cues jtea zioe'
EMAILS_DESTINO = ['fferraiuolo@puppis.com.ar', 'comercial@puppis.com.ar']

def enviar_mail(asunto, cuerpo):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = ', '.join(EMAILS_DESTINO)
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(GMAIL_USER, GMAIL_PASSWORD.replace(' ', ''))
        servidor.sendmail(GMAIL_USER, EMAILS_DESTINO, msg.as_string())
        servidor.quit()
        print(f"  Mail enviado: {asunto}")
    except Exception as e:
        print(f"  Error enviando mail: {e}")

def enviar_alerta(producto, tienda, precio_anterior, precio_nuevo):
    diferencia = precio_nuevo - precio_anterior
    porcentaje = (diferencia / precio_anterior) * 100
    direccion = "subió" if diferencia > 0 else "bajó"
    emoji = "📈" if diferencia > 0 else "📉"

    asunto = f"{emoji} Cambio de precio: {producto} en {tienda}"
    cuerpo = f"""
{emoji} Cambio de precio detectado

Producto: {producto}
Tienda: {tienda}
Precio anterior: ${precio_anterior:,.0f}
Precio nuevo: ${precio_nuevo:,.0f}
Variación: {porcentaje:+.1f}% ({direccion})
"""
    enviar_mail(asunto, cuerpo)

def enviar_alerta_url_rota(producto, tienda, url):
    asunto = f"⚠️ URL rota: {producto} en {tienda}"
    cuerpo = f"""
⚠️ URL rota detectada

Producto: {producto}
Tienda: {tienda}
URL: {url}

El scraper no pudo obtener el precio. Es posible que la URL haya cambiado.
Entrá a la app y actualizá la URL usando el botón "Editar".
"""
    enviar_mail(asunto, cuerpo)

def enviar_alerta_prueba():
    enviar_alerta('Royal Canin 15kg', 'drovenort', 160000, 155000)

if __name__ == '__main__':
    enviar_alerta_prueba()