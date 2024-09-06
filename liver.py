import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QLabel, QRubberBand, QToolBar
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QPoint, QRect, QSize, pyqtSignal
import cv2
import numpy as np
import matplotlib.pyplot as plt
import scipy

#TODO: Criar uma class para toolbar_image e para o menu

class ImageLabel(QLabel):
    cropped = pyqtSignal(str, QPixmap)

    def __init__(self):
        super().__init__()
        # Tamanho das imagens .mat, setei como tamanho maximo do ImageLabel
        self.setMaximumWidth(434)
        self.setMaximumHeight(636)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        self.is_rubber_band_active = False
        self.count_cropped = 0
    

    # Metodos ja setados para o funcionamento do rubberband (recorte de imagem)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_rubber_band_active == True:
            self.origin = QPoint(event.pos())
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()
       
    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent (self, event):
        self.rubber_band.hide()
        current_qrect = self.rubber_band.geometry()
        self.rubber_band.deleteLater()
        crop_qpixmap = self.pixmap().copy(current_qrect)
        self.cropped.emit(f"output_{self.count_cropped}.png", crop_qpixmap) # Emissao dos parametros necessarios para a conexao ImageProcessor - ImageLabel add_image_to_toolbar 

class ImageProcessor(QMainWindow):
    def __init__(self, images=None):
        super().__init__()
        self.image_label = ImageLabel()
        self.image_label.cropped.connect(self.add_image_to_toolbar) # Comunicacao ImageProcessor - ImageLabel
        self.images = images
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Processing Application (IPA)')
        # Tamanho minimo da tela != Tamanho maximo da image_label
        self.setMinimumWidth(800)
        self.setMinimumHeight(700)

        # Menu bar

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')
        open_file = QAction('Open Image', self)
        open_file.triggered.connect(self.open_image)
        fileMenu.addAction(open_file)

        fileMenu = menubar.addMenu('ROIs')
        crop_image = QAction('Crop Image', self)
        fileMenu.addAction(crop_image)

        self.toolbar_images = QToolBar("All Images")
        self.addToolBar(Qt.LeftToolBarArea, self.toolbar_images)

        self.setCentralWidget(self.image_label)

        self.show()

    def open_image(self, file_name):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Images (*.png *.jpg *.bmp *.mat);;All Files (*)", options=options)
        if file_name:
            if file_name.endswith('.mat'):
                pass
            else:
                image = cv2.imread(file_name, cv2.IMREAD_GRAYSCALE)
                height, width = image.shape
                qImg = QImage(image.data, width, height, QImage.Format_Grayscale8)
                pixmap = QPixmap.fromImage(qImg)
                self.add_image_to_toolbar(file_name, pixmap)
    
    def display_image(self, pixmap):
        self.image_label.setPixmap(pixmap)
        self.image_label.resize(434, 636)
        self.image_label.is_rubber_band_active = True

    def add_image_to_toolbar(self, name, pixmap):
        image_bt_act = QAction(f'{name}', self)
        image_bt_act.setStatusTip("Open Image")
        self.toolbar_images.addAction(image_bt_act)
        image_bt_act.triggered.connect(lambda: self.display_image(pixmap))

def get_images_dataset():
    path_input_dir = Path("liver")
    path_data = path_input_dir / "dataset_liver_bmodes_steatosis_assessment_IJCARS.mat"
    data = scipy.io.loadmat(path_data)
    data.keys()
    data_array = data['data']
    return data_array['images']

if __name__ == '__main__':
    liver_images = get_images_dataset()
    app = QApplication(sys.argv)
    ex = ImageProcessor(liver_images)

    sys.exit(app.exec_())