# Estos son los paquetes que se deben instalar
# pip install pycryptodome
# pip install pyqrcode
# pip install pypng
# pip install pyzbar
# pip install pillow

# No modificar estos módulos que se importan
from sqlite3 import ProgrammingError
from pyzbar.pyzbar import decode
from PIL import Image
from json import dumps
from json import loads
from hashlib import sha256
from Crypto.Cipher import AES
import base64
import pyqrcode
from os import urandom
import io
from datetime import datetime

# Nombre del archivo con la base de datos de usuarios
usersFileName="Datos/datos.txt"


# Fecha actual
date=None
# Clave aleatoria para encriptar el texto de los códigos QR
key=None

# Función para encriptar (no modificar)
def encrypt_AES_GCM(msg, secretKey):
    aesCipher = AES.new(secretKey, AES.MODE_GCM)
    ciphertext, authTag = aesCipher.encrypt_and_digest(msg)
    return (ciphertext, aesCipher.nonce, authTag)

# Función para desencriptar (no modificar)
def decrypt_AES_GCM(encryptedMsg, secretKey):
    (ciphertext, nonce, authTag) = encryptedMsg
    aesCipher = AES.new(secretKey, AES.MODE_GCM, nonce)
    plaintext = aesCipher.decrypt_and_verify(ciphertext, authTag)
    return plaintext

# Función que genera un código QR (no modificar)
def generateQR(id,program,role,buffer):
    # Variables globales para la clave y la fecha
    global key
    global date

    # Información que irá en el código QR, antes de encriptar
    data={'id': id, 'program':program,'role':role}
    datas=dumps(data).encode("utf-8")

    # Si no se ha asignado una clave se genera
    if key is None:
        key =urandom(32) 
        # Se almacena la fecha actual
        date=datetime.today().strftime('%Y-%m-%d')
    
    # Si cambió la fecha actual se genera una nueva clave y 
    # se actualiza la fecha
    if date !=datetime.today().strftime('%Y-%m-%d'):
        key =urandom(32) 
        date=datetime.today().strftime('%Y-%m-%d')

    # Se encripta la información
    encrypted = list(encrypt_AES_GCM(datas,key))

    # Se crea un JSON convirtiendo los datos encriptados a base64 para poder usar texto en el QR
    qr_text=dumps({'qr_text0':base64.b64encode(encrypted[0]).decode('ascii'),
                                'qr_text1':base64.b64encode(encrypted[1]).decode('ascii'),
                                'qr_text2':base64.b64encode(encrypted[2]).decode('ascii')})
    
    # Se crea el código QR a partir del JSON
    qrcode = pyqrcode.create(qr_text)

    # Se genera una imagen PNG que se escribe en el buffer                    
    qrcode.png(buffer,scale=8)          


# Se debe codificar esta función
# Argumentos: id (entero), password (cadena), program (cadena) y role (cadena)
# Si el usuario ya existe deber retornar  "User already registered"
# Si el usuario no existe debe registar el usuario en la base de datos y retornar  "User succesfully registered"
def registerUser(id: int, password: str, program: str, role: str):
    verificador = []
    with open(usersFileName, 'r') as file:
        verificador = file.readlines() # Lee todas las líneas del archivo de usuarios

    usuarios = []
    for i in verificador:
        usuarios.append(loads(i))# Convierte cada línea (JSON) en un diccionario de Python


    for u in usuarios:
        if u['id'] == str(id):# Verifica si ya existe un usuario con el mismo ID
            print("User already registered")
            return "User already registered" #Retorna si el usuario ya existe


    user = {'id': str(id), 'password': password, 'program': program, 'role': role}
    with open(usersFileName, 'a') as file:
        file.write(dumps(user) + "\n") # Guarda el nuevo usuario en formato JSON

    print("User successfully registered")
    return "User successfully registered"




#Se debe complementar esta función
# Función que genera el código QR
# retorna el código QR si el id y la contraseña son correctos (usuario registrado)
# Ayuda (debe usar la función generateQR)
def getQR(id: int, password: str):
    buffer = io.BytesIO()
    with open(usersFileName, 'r') as file:
        verificador = file.readlines() # Lee todos los usuarios registrados

    for lineas in verificador:
        # Convierte la línea en un diccionario
        usuario = loads(lineas)
        
        if usuario['id'] == str(id) and usuario['password'] == password:
            # Llama la función para generar el QR
            generateQR(usuario['id'], usuario['program'], usuario['role'], buffer)
            return buffer
    # Si no se encontró usuario válido
    print("User credentials invalid")
    return None    



# Se debe complementar esta función
# Función que recibe el código QR como PNG
# debe verificar si el QR contiene datos que pueden ser desencriptados con la clave (key), y si el usuario está registrado
# Debe asignar un puesto de parqueadero dentro de los disponibles.
def sendQR(png):
    # Decodifica código QR
    decodedQR = decode(Image.open(io.BytesIO(png)))[0].data.decode('ascii')
    data = loads(decodedQR)
    # Desencripta con la clave actual, decodificando antes desde base64. Posteriormente convierte a diccionario (generar error si la clave expiró)
    decrypted=loads(decrypt_AES_GCM((base64.b64decode(data["qr_text0"]),base64.b64decode(data["qr_text1"]),base64.b64decode(data["qr_text2"])), key))


# En este punto la función debe determinar que el texto del código QR corresponde a un usuario registrado.
    # Luego debe verificar qué puestos de parqueadero existen disponibles según el rol, si hay disponibles le debe asignar 
    # un puesto al usuario y retornarlo como una cadena
    # Verifica usuario registrado

    with open(usersFileName, 'r') as file:
        users = []
        for line in file:
            users.append(loads(line))


    user_found = None
    for user in users:
        if (user['id'] == decrypted['id'] and 
            user['program'] == decrypted['program'] and 
            user['role'] == decrypted['role']):
            user_found = user
            break

    if user_found == None:  # Cambiado de 'if not user_found'
        print("Usuario no registrado")
        return None

    # Archivo de puestos (versión más simple sin try-except)
    parking_file = "Datos/puestos.txt"
    parking_spots = {'profesor': {'disponibles': ['P1', 'P2', 'P3', 'P4', 'P5'], 'ocupados': []},'estudiante': {'disponibles': ['S1', 'S2', 'S3', 'S4', 'S5'], 'ocupados': []}}
    
    # Intenta cargar el archivo si existe
    file = open(parking_file, 'r')
    parking_spots = loads(file.read())
    file.close()

    role = user_found['role']
    
    if role != 'profesor' and role != 'estudiante':
        print(f"Rol inválido: '{role}'. Solo 'profesor' o 'estudiante'")
        return None

    if len(parking_spots[role]['disponibles']) > 0:
        puesto_asignado = parking_spots[role]['disponibles'].pop(0)
        parking_spots[role]['ocupados'].append(puesto_asignado)
        
        with open(parking_file, 'w') as file:
            file.write(dumps(parking_spots))
        
        print(f"Puesto asignado: {puesto_asignado}")
        return puesto_asignado
    else:
        print("No hay puestos disponibles")
        return None
