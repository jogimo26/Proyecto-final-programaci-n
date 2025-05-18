import parking_client
import users# Aquí está la función visualizar_ocupacion_con_camara
from PIL import Image
import io
import time

# Datos del usuario
id = 70770
password = "maradona"
program = "Electronics Engineering"
role = "profesor"
url = "http://localhost:80"

# 1. Registrar el usuario
print("Registrando usuario...")
print(parking_client.registerUser(url, id, password, program, role))

# 2. Solicitar código QR
print("Solicitando QR...")
imgBytes = parking_client.getQR(url, id, password)
if imgBytes is None:
    print("No se pudo obtener el QR.")
    exit()

# 3. Mostrar y guardar QR
image = Image.open(io.BytesIO(imgBytes))
image.show()
image.save("codigo_qr.png")
print("QR guardado como 'codigo_qr.png'.")

# 4. Enviar QR al servidor para asignar puesto
print("Enviando QR al servidor...")
puesto = parking_client.sendQR(url, "codigo_qr.png")
if puesto is None:
    print("No se pudo asignar un puesto.")
    exit()

print(f"Puesto asignado: {puesto}")

# 5. Visualizar ocupación usando OpenCV
print("Abriendo cámara para visualizar ocupación...")
time.sleep(2)
users.visualizar_ocupacion_con_camara()
