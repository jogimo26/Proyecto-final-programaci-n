"""Identificación de código QR válido"""
"""Alexander López Parrado"""

# Módulos de Qt 
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# Módulos OpenCV
import cv2,imutils #pip install imutils


# Módulo de código QR
from pyzbar.pyzbar import decode

# Clase hilo para captura de la cámara
class MyThread(QThread):
    
    # Señal que se emite a la ventana para indicar un nuevo frame
    frame_signal = pyqtSignal(QImage,bool)


    # Método run del hilo
    def run(self):
        # Inicialmente está corriendo
        self.is_running=True

        # Abre cámara
        self.cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)

        # Ciclo mientras esté corriendo
        while self.is_running:

            # Lee frame
            _,frame = self.cap.read()

            # Se convierte a imagende Qt
            qframe = self.cvimage_to_qimage(frame)

            # Decodifica el código QR
            decodedQR = decode(frame)

            # Se retorna una lista, si no está vacía hay un código QR válido
            if len(decodedQR):
                # Se detiene la captura
                self.cap.release()
                # Se emite la señal con el frame y la bandera en True
                self.frame_signal.emit(qframe,True)
                # Se detiene el hilo
                self.is_running=False
                return
            # Emite señal que visualiza imagen
            self.frame_signal.emit(qframe,False)

        # Si se detiene la captura se cierra la cámara    
        self.cap.release()
    
    # Se convierte imagen de OpenCV a imagen de Qt
    def cvimage_to_qimage(self,image):
        image = imutils.resize(image,width = 640)
        image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        image = QImage(image,
                       image.shape[1],
                       image.shape[0],
                       QImage.Format_RGB888)
        return image
    
    # Slot para detener la captura como una señal desde la ventana
    @pyqtSlot()
    def stop_capture(self):        
        self.is_running=False


# Ventana principal
class MainApp(QMainWindow):

    # Señal para detener la captura que se emite hacia el hilo
    stop_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.show()
    
    def init_ui(self):
        self.setFixedSize(640,640)
        self.setWindowTitle("QR Scanner")
        self.is_streaming=False

        # Widget central
        widget = QWidget(self)

        # Con layout vertical
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Label para la visualización de los frames de la cámara
        self.label = QLabel()
        layout.addWidget(self.label)

        # Botón para abrir/cerrar la cámara
        self.open_btn = QPushButton("Open The Camera", clicked=self.open_close_camera)
        layout.addWidget(self.open_btn)

       

        self.setCentralWidget(widget)

    # Método para detener el streaming
    def stop_streaming(self):
        self.open_btn.setText("Open The Camera")
        self.is_streaming=False
        self.camera_thread.frame_signal.disconnect()
        
    # Método para abrir/cerrar la cámara     
    def open_close_camera(self):       
        if self.is_streaming:
            self.stop_streaming()
            self.stop_signal.emit()
            self.camera_thread.wait()
        else:
            # Se crea el hilo
            self.camera_thread = MyThread()
            # Conecta la señal de los frames para que sea bloqueante
            self.camera_thread.frame_signal.connect(self.setImage,Qt.BlockingQueuedConnection)
            # Conecta la señal de detener la captura
            self.stop_signal.connect(self.camera_thread.stop_capture)
            self.is_streaming=True
            self.open_btn.setText("Close The Camera")
            # Inicia el hilo de captura
            self.camera_thread.start()
            
       
    # Slot de la señal que proviene de hilo que envía el frame
    @pyqtSlot(QImage,bool)
    def setImage(self,image,flag):              
        # Si no ha detectado código Qr visualiza la imagen
        if flag==False:
            self.label.setPixmap(QPixmap.fromImage(image))
        else:
          
            # Imprime que el código Qr es válido
            print('Valid Qr')

            # Se debe enviar un archivo png al servidor

            # Dibuja un cuadro verde                
            painter=QPainter(self.label.pixmap())
            painter.setBrush(QBrush(QColor("green")))
            painter.setPen(QPen(QColor("green")))
            x1,y1,x2,y2=image.rect().getCoords()
            painter.drawRect(x1,y1,x2,y2)
            painter.end()
            self.label.repaint()
            self.stop_streaming()
          



# Crea la aplicación
app = QApplication([])

# Crea la ventana principal
main_window = MainApp()

# Lanza el manejador de eventos
app.exec()
