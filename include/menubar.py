from PyQt5.QtWidgets import QAction, QFileDialog, QMenuBar
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import pyqtSignal
import cv2

class MenuBar(QMenuBar):
    add_image = pyqtSignal(str, QPixmap)
    crop_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        open_file = QAction('Abrir Imagem', self)
        open_file.triggered.connect(self.open_image)
        file_menu = self.addMenu('Arquivos')
        file_menu.addAction(open_file)

        file_menu = self.addMenu('ROIs')
        crop_image = QAction('Recortar Imagem', self)
        crop_image.triggered.connect(self.crop_signal.emit)
        file_menu.addAction(crop_image)

    def open_image(self, file_name):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de Imagem", "", "Images (*.png *.jpg *.bmp *.mat);;All Files (*)", options=options)
        if file_name:
            if file_name.endswith('.mat'):
                pass
            else:
                image = cv2.imread(file_name, cv2.IMREAD_GRAYSCALE)
                height, width = image.shape
                q_img = QImage(image.data, width, height, QImage.Format_Grayscale8)
                pixmap = QPixmap.fromImage(q_img)
                self.add_image.emit(file_name, pixmap)