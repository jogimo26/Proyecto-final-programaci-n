# Estos son los paquetes que se deben instalar
# pip install pycryptodome
# pip install pyqrcode
# pip install pypng
# pip install pyzbar
# pip install pillow

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

usersFileName = "Datos\datos.txt"
date = None
key = None

def encrypt_AES_GCM(msg, secretKey):
    aesCipher = AES.new(secretKey, AES.MODE_GCM)
    ciphertext, authTag = aesCipher.encrypt_and_digest(msg)
    return (ciphertext, aesCipher.nonce, authTag)

def decrypt_AES_GCM(encryptedMsg, secretKey):
    (ciphertext, nonce, authTag) = encryptedMsg
    aesCipher = AES.new(secretKey, AES.MODE_GCM, nonce)
    plaintext = aesCipher.decrypt_and_verify(ciphertext, authTag)
    return plaintext

def generateQR(id, program, role, buffer):
    global key, date

    data = {'id': id, 'program': program, 'role': role}
    datas = dumps(data).encode("utf-8")

    today = datetime.today().strftime('%Y-%m-%d')
    if key == None or date != today:
        key = urandom(32)
        date = today

    encrypted = list(encrypt_AES_GCM(datas, key))

    qr_text = dumps({
        'qr_text0': base64.b64encode(encrypted[0]).decode('ascii'),
        'qr_text1': base64.b64encode(encrypted[1]).decode('ascii'),
        'qr_text2': base64.b64encode(encrypted[2]).decode('ascii')
    })

    qrcode = pyqrcode.create(qr_text)
    qrcode.png(buffer, scale=8)

def registerUser(id: int, password: str, program: str, role: str):
    verificador = []
    with open(usersFileName, 'r') as file:
        verificador = file.readlines()

    usuarios = [loads(i) for i in verificador]

    for u in usuarios:
        if u['id'] == str(id):
            print("User already registered")
            return "User already registered"

    user = {'id': str(id), 'password': password, 'program': program, 'role': role}
    with open(usersFileName, 'a') as file:
        file.write(dumps(user) + "\n")
    print("User successfully registered")
    return "User successfully registered"

def getQR(id: int, password: str):
    buffer = io.BytesIO()
    with open(usersFileName, 'r') as file:
        verificador = file.readlines()

    for line in verificador:
        usuario = loads(line)
        if usuario['id'] == str(id) and usuario['password'] == password:
            generateQR(usuario['id'], usuario['program'], usuario['role'], buffer)
            print("QR generado exitosamente")
            return buffer

    print("User credentials invalid")
    return None

def sendQR(png):
    global key
    decodedQR = decode(Image.open(io.BytesIO(png)))[0].data.decode('ascii')
    data = loads(decodedQR)

    decrypted = loads(decrypt_AES_GCM(( base64.b64decode(data["qr_text0"]), base64.b64decode(data["qr_text1"]),base64.b64decode(data["qr_text2"])), key))

    puestos = {'parqueoEstudiante': ['e1', 'e2', 'e3'],'estudianteocupado': [],'parqueoprofesor': ['p1', 'p2', 'p3'],'profesorocupado': []}

    with open(usersFileName, 'r') as file:
        users = file.readlines()

    for i in users:
        user = loads(i)
        if user['id'] == decrypted['id']:
            if user['role'] == 'estudiante' and puestos['parqueoEstudiante']:
                espacio = puestos['parqueoEstudiante'].pop(0)
                puestos['estudianteocupado'].append(espacio)
                return f'el estudiante fue asignado al puesto {espacio}'
            elif user['role'] == 'profesor' and puestos['parqueoprofesor']:
                espacio = puestos['parqueoprofesor'].pop(0)
                puestos['profesorocupado'].append(espacio)
                return f'el profesor fue asignado al puesto {espacio}'
            else:
                return 'no hay parqueos disponibles'

    return 'usuario no registrado'

