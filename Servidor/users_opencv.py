import cv2
import numpy as np
from sqlite3 import ProgrammingError
from pyzbar.pyzbar import decode
from PIL import Image
from json import dumps, loads
from hashlib import sha256
from Crypto.Cipher import AES
import base64
import pyqrcode
from os import urandom
import io
from datetime import datetime

# Nombre del archivo con la base de datos de usuarios
usersFileName = "Datos/datos.txt"
parking_file = "Datos/puestos.txt"

# Variables globales
date = None
key = None
umbral = 30  # Valor inicial por defecto

# Puestos de parqueo
puestos = [
    ((455, 19), (539, 129)),
    ((378, 19), (458, 129)),
    ((295, 19), (377, 129)),
    ((212, 19), (293, 129)),
    ((128, 19), (211, 129)),
    ((37, 19), (125, 129)),
    ((464, 230), (540, 343)),
    ((375, 230), (464, 342)),
    ((293, 230), (373, 338)),
]

# Zonas vacías conocidas para referencia
zonas_referencia = [
    ((295, 135), (380, 229)),
    ((251, 132), (290, 340)),
    ((461, 139), (537, 226)),
]

# Función para encriptar
def encrypt_AES_GCM(msg, secretKey):
    aesCipher = AES.new(secretKey, AES.MODE_GCM)
    ciphertext, authTag = aesCipher.encrypt_and_digest(msg)
    return (ciphertext, aesCipher.nonce, authTag)

# Función para desencriptar
def decrypt_AES_GCM(encryptedMsg, secretKey):
    (ciphertext, nonce, authTag) = encryptedMsg
    aesCipher = AES.new(secretKey, AES.MODE_GCM, nonce)
    plaintext = aesCipher.decrypt_and_verify(ciphertext, authTag)
    return plaintext

# Función que genera un código QR
def generateQR(id, program, role, buffer):
    global key, date
    data = {'id': id, 'program': program, 'role': role}
    datas = dumps(data).encode("utf-8")

    if key is None or date != datetime.today().strftime('%Y-%m-%d'):
        key = urandom(32)
        date = datetime.today().strftime('%Y-%m-%d')

    encrypted = list(encrypt_AES_GCM(datas, key))
    qr_text = dumps({
        'qr_text0': base64.b64encode(encrypted[0]).decode('ascii'),
        'qr_text1': base64.b64encode(encrypted[1]).decode('ascii'),
        'qr_text2': base64.b64encode(encrypted[2]).decode('ascii')
    })

    qrcode = pyqrcode.create(qr_text)
    qrcode.png(buffer, scale=8)

# Función para registrar un usuario
def registerUser(id: int, password: str, program: str, role: str):
    try:
        with open(usersFileName, 'r') as file:
            usuarios = [loads(line) for line in file]
    except FileNotFoundError:
        usuarios = []

    for u in usuarios:
        if u['id'] == str(id):
            print("User already registered")
            return "User already registered"

    user = {'id': str(id), 'password': password, 'program': program, 'role': role}
    with open(usersFileName, 'a') as file:
        file.write(dumps(user) + "\n")

    print("User successfully registered")
    return "User successfully registered"

# Función que genera el código QR
def getQR(id: int, password: str):
    try:
        with open(usersFileName, 'r') as file:
            usuarios = [loads(line) for line in file]
    except FileNotFoundError:
        print("User credentials invalid")
        return None

    for usuario in usuarios:
        if usuario['id'] == str(id) and usuario['password'] == password:
            buffer = io.BytesIO()
            generateQR(usuario['id'], usuario['program'], usuario['role'], buffer)
            return buffer

    print("User credentials invalid")
    return None

# Función que recibe el código QR como PNG y asigna un puesto
def sendQR(png):
    global key
    
    decodedQR = decode(Image.open(io.BytesIO(png)))[0].data.decode('ascii')
    data = loads(decodedQR)
    decrypted = loads(decrypt_AES_GCM(
            (base64.b64decode(data["qr_text0"]),
             base64.b64decode(data["qr_text1"]),
             base64.b64decode(data["qr_text2"])),
            key))
    

    try:
        with open(usersFileName, 'r') as file:
            users = [loads(line) for line in file]
    except FileNotFoundError:
        print("Usuario no registrado")
        return None

    user_found = next((user for user in users if user['id'] == decrypted['id'] and
                      user['program'] == decrypted['program'] and
                      user['role'] == decrypted['role']), None)

    if user_found is None:
        print("Usuario no registrado")
        return None

    try:
        with open(parking_file, 'r') as file:
            parking_spots = loads(file.read())
    except FileNotFoundError:
        parking_spots = {
            'profesor': {'disponibles': ['P1', 'P2', 'P3', 'P4', 'P5'], 'ocupados': []},
            'estudiante': {'disponibles': ['S1', 'S2', 'S3', 'S4', 'S5'], 'ocupados': []}
        }

    role = user_found['role']
    if role not in parking_spots:
        print(f"Rol inválido: '{role}'. Solo 'profesor' o 'estudiante'")
        return None

    if parking_spots[role]['disponibles']:
        puesto_asignado = parking_spots[role]['disponibles'].pop(0)
        parking_spots[role]['ocupados'].append(puesto_asignado)

        with open(parking_file, 'w') as file:
            file.write(dumps(parking_spots))

        print(f"Puesto asignado: {puesto_asignado}")
        return puesto_asignado
    else:
        print("No hay puestos disponibles")
        return None

# Función para contar contornos en un área
def contornos(area):
    gris = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
    bordes = cv2.Canny(gris, 100, 200)
    contorno, _ = cv2.findContours(bordes, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return len(contorno)

# Función para calibrar el umbral
def calibrar_umbral(frame):
    suma_contornos = 0
    for z1, z2 in zonas_referencia:
        zona = frame[z1[1]:z2[1], z1[0]:z2[0]]
        suma_contornos += contornos(zona)
        cv2.rectangle(frame, z1, z2, (255, 0, 255), 2)
    nuevo_umbral = suma_contornos / len(zonas_referencia)
    print(f"[CALIBRACIÓN] Umbral ajustado a: {nuevo_umbral:.2f}")
    return nuevo_umbral

# Función para mostrar el estado de los puestos
def mostrar_estado_puestos(frame, umbral):
    print("[ESTADO DE PUESTOS]")
    for i, (p1, p2) in enumerate(puestos):
        area_puesto = frame[p1[1]:p2[1], p1[0]:p2[0]]
        n = contornos(area_puesto)
        estado = "Ocupado" if n > umbral + 15 else "Libre"
        print(f"Puesto {i+1}: {estado} (Contornos: {n})")

# Función para visualizar la ocupación con cámara
def visualizar_ocupacion_con_camara():
    global umbral
    video = cv2.VideoCapture(0)

    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break

        for i, (p1, p2) in enumerate(puestos):
            area_puesto = frame[p1[1]:p2[1], p1[0]:p2[0]]
            n = contornos(area_puesto)
            color = (0, 0, 255) if n > umbral + 15 else (0, 255, 0)
            cv2.rectangle(frame, p1, p2, color, 2)
            cv2.putText(frame, f"{i+1}", (p1[0]+5, p1[1]+20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.imshow("Estado de Puestos", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # Enter para calibrar
            umbral = calibrar_umbral(frame.copy())
            mostrar_estado_puestos(frame.copy(), umbral)
        elif key == ord('1'):
            break

    video.release()
    cv2.destroyAllWindows()
