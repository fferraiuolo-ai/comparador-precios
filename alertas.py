import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = 'fferraiuolo@puppis.com.ar'
GMAIL_PASSWORD = 'cmqv zzlq syzy qroe'
EMAIL_DESTINO = 'fferraiuolo@puppis.com.ar'

def enviar_alerta(producto, tienda, precio_anterior, precio_nuevo):
    diferencia = precio_nuevo - precio_anterior
    porcentaje = (diferencia / precio_anterior) * 100

    asunto = f"Cambio de precio: {producto} en {tienda}"
    
    if diferencia > 0:
        emoji = "📈"
        direccion = "subió"
    else:
        emoji = "📉"
        direccion = "bajó"

    cuerpo = f"""
{emoji} Cambio de precio detectado

Producto: {producto}
Tienda: {tienda}
Precio anterior: ${precio_anterior:,.0f}
Precio nuevo: ${precio_nuevo:,.0f}
Variación: {porcentaje:+.1f}% ({direccion})
"""

    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = EMAIL_DESTINO
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(GMAIL_USER, GMAIL_PASSWORD.replace(' ', ''))
        servidor.sendmail(GMAIL_USER, EMAIL_DESTINO, msg.as_string())
        servidor.quit()
        print(f"  Alerta enviada: {producto} en {tienda}")
    except Exception as e:
        print(f"  Error enviando alerta: {e}")

def enviar_alerta_prueba():
    enviar_alerta('Royal Canin 15kg', 'drovenort', 160000, 155000)

if __name__ == '__main__':
    enviar_alerta_prueba()