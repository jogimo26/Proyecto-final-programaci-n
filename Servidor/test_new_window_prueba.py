from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import cv2
import imutils
from pyzbar.pyzbar import decode
import users  # Keep users for direct access to camera functions and sendQR
import parking_client  # Keep parking_client for registerUser and getQR
from PIL import Image
import sys
import json
import numpy as np

class MyThread(QThread):
    frame_signal = pyqtSignal(QImage, bool)
    # Signal to emit the decoded QR data string
    qr_decoded_string_signal = pyqtSignal(str) 

    def run(self):
        self.is_running = True
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                continue

            frame = cv2.flip(frame, 1)
            qframe = self.cvimage_to_qimage(frame)
            decodedQR = decode(frame)

            if len(decodedQR):
                qr_data_string = decodedQR[0].data.decode('utf-8')
                self.cap.release()
                self.frame_signal.emit(qframe, True)
                self.qr_decoded_string_signal.emit(qr_data_string) # Emit the decoded string
                self.is_running = False
                return

            self.frame_signal.emit(qframe, False)

        self.cap.release()

    def cvimage_to_qimage(self, image):
        image = imutils.resize(image, width=640)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return QImage(image, image.shape[1], image.shape[0], QImage.Format_RGB888)

    @pyqtSlot()
    def stop_capture(self):
        self.is_running = False


class QRScannerWindow(QMainWindow):
    stop_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(640, 640)
        self.setWindowTitle("QR Scanner")
        self.is_streaming = False

        widget = QWidget(self)
        layout = QVBoxLayout()
        widget.setLayout(layout)

        self.label = QLabel()
        layout.addWidget(self.label)

        self.open_btn = QPushButton("Abrir Cámara", clicked=self.open_close_camera)
        layout.addWidget(self.open_btn)

        self.setCentralWidget(widget)

    def stop_streaming(self):
        self.open_btn.setText("Abrir Cámara")
        self.is_streaming = False
        if hasattr(self, 'camera_thread'):
            self.camera_thread.frame_signal.disconnect()
            self.camera_thread.qr_decoded_string_signal.disconnect() # Disconnect the new signal

    def open_close_camera(self):
        if self.is_streaming:
            self.stop_streaming()
            self.stop_signal.emit()
            if hasattr(self, 'camera_thread'):
                self.camera_thread.wait()
        else:
            self.camera_thread = MyThread()
            self.camera_thread.frame_signal.connect(self.setImage, Qt.BlockingQueuedConnection)
            # Connect the new signal to process the decoded QR string
            self.camera_thread.qr_decoded_string_signal.connect(self.processQRAndAssignSpot) 
            self.stop_signal.connect(self.camera_thread.stop_capture)
            self.is_streaming = True
            self.open_btn.setText("Cerrar Cámara")
            self.camera_thread.start()

    @pyqtSlot(QImage, bool)
    def setImage(self, image, flag):
        if not flag:
            self.label.setPixmap(QPixmap.fromImage(image))
        else:
            print('QR válido detectado en la UI')
            painter = QPainter(self.label.pixmap())
            painter.setBrush(QBrush(QColor("green")))
            painter.setPen(QPen(QColor("green")))
            x1, y1, x2, y2 = image.rect().getCoords()
            painter.drawRect(x1, y1, x2, y2)
            painter.end()
            self.label.repaint()
            self.stop_streaming()

    @pyqtSlot(str) 
    def processQRAndAssignSpot(self, qr_data_string):
        print(f"Processing decoded QR string: {qr_data_string}")
        try:
            # Here, we directly call users.sendQR as parking_client.sendQR
            # is just a wrapper for it in your current setup.
            # users.sendQR expects the raw JSON string of the QR, encoded as bytes.
            qr_raw_data_bytes = qr_data_string.encode('utf-8') 

            # This is the direct call to the users module to assign the spot
            puesto = users.sendQR(qr_raw_data_bytes) 

            if puesto is None:
                print("No se pudo asignar un puesto.")
                QMessageBox.warning(self, "Error", "No se pudo asignar un puesto o el QR no es válido.")
            else:
                print(f"Puesto asignado: {puesto}")
                QMessageBox.information(self, "Puesto Asignado", f"Puesto asignado: {puesto}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al procesar el QR: {str(e)}")
        finally:
            self.close() # Close the QR scanner window after processing

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro")
        # Se crean los labels
        l1 = QLabel('ID: ')
        l2 = QLabel('Contraseña: ')
        l3 = QLabel('Programa: ')
        l4 = QLabel('Rol: ')

        # Se crean los campos de entrada
        self.e1 = QLineEdit()
        self.e2 = QLineEdit()
        self.e3 = QLineEdit()
        self.e4 = QLineEdit()

        b1 = QPushButton('Registrar Usuario')
        b1.clicked.connect(self.newWindow)
        
        gridLayout = QGridLayout()
        
        # Se añaden los widgets al layout
        gridLayout.addWidget(l1, 0, 0)
        gridLayout.addWidget(l2, 1, 0)
        gridLayout.addWidget(l3, 2, 0)
        gridLayout.addWidget(l4, 3, 0)
        
        gridLayout.addWidget(self.e1, 0, 1)
        gridLayout.addWidget(self.e2, 1, 1)
        gridLayout.addWidget(self.e3, 2, 1)
        gridLayout.addWidget(self.e4, 3, 1)

        gridLayout.addWidget(b1, 4, 0, 1, 2)
        
        widget = QWidget()
        widget.setLayout(gridLayout)
        self.setCentralWidget(widget)
        self.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint)
    
    def newWindow(self):
        id = self.e1.text()
        password = self.e2.text()
        program = self.e3.text()
        role = self.e4.text()

        if len(id) and len(password) and len(program) and len(role):
            url = "http://localhost:80" # This URL is still needed for parking_client.registerUser/getQR

            # Register user via parking_client
            Usuario = parking_client.registerUser(url, id, password, program, role)
            
            if Usuario == "User successfully registered":
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setText("Usuario registrado con éxito")
                msgBox.setWindowTitle("Información")
                msgBox.exec()

                try:
                    # Get QR data as PNG bytes via parking_client
                    qr_data_png_bytes = parking_client.getQR(url, int(id), password)
                    
                    if qr_data_png_bytes:
                        filename = f"{id}_qr.png"
                        with open(filename, "wb") as f:
                            f.write(qr_data_png_bytes)
                        
                        Image.open(filename).show()
                        
                        # Hide the main window before opening the OpenCV camera
                        self.hide() 
                        
                        # Call the blocking OpenCV function
                        users.visualizar_ocupacion_con_camara() 
                        
                        # After the OpenCV window closes (by pressing '1'),
                        # show the QR scanner window.
                        self.qr_scanner = QRScannerWindow()
                        self.qr_scanner.show()
                        
                    else:
                        QMessageBox.warning(self, "Error", "No se pudo generar el QR")
                except Exception as e:
                    QMessageBox.critical(self, "Error QR", f"Error al generar QR: {str(e)}")
            else:
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Warning)
                msgBox.setText("Usuario ya existente dentro del sistema")
                msgBox.setWindowTitle("Alerta")
                msgBox.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())
