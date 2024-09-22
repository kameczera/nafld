import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QLabel, QRubberBand, QToolBar, QTreeWidget, QTreeWidgetItem
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QPoint, QRect, QSize, pyqtSignal
import cv2
import numpy as np
import matplotlib.pyplot as plt
import scipy

# Classe ToolBarImages: Classe que mostra as imagens adicionadas pelo botao load, "croppadas" e do dataset Liver
class ToolBarImages(QToolBar):
    display = pyqtSignal(QPixmap)
    

    def __init__(self, images = None):
        super().__init__("All Images")
        self.images = images
        self.folder_hierarchy = QTreeWidget()
        self.pixmap_dictionary = {}
        self.addWidget(self.folder_hierarchy)
        self.folder_hierarchy.itemClicked.connect(self.display_image)
        self.folder_hierarchy.setHeaderHidden(True)

        self.cropped_imgs_node = QTreeWidgetItem(self.folder_hierarchy)
        self.cropped_imgs_node.setText(0, f"Coleção de Cortes")

        # Fazendo o a extracao das imagens do formato images[0][n][m] para a hierarquia de pastas
        for id_pacient,patient in enumerate(self.images):
            # Inicialização do nós Raizes (Nó dos pacientes)
            patient_node = QTreeWidgetItem(self.folder_hierarchy)
            patient_node.setText(0, f"Paciente {id_pacient}")
            for id_image,image in enumerate(patient):
                self.open_image_patients(image, id_pacient, id_image, patient_node)

    def display_image(self, item, column):
        # Deixar Nós raiz inclicáveis (nós com header de paciente)
        if item.parent() is None:
            return
        # TODO: Nome dos nós folhas estranho. Mudar aqui
        self.display.emit(self.pixmap_dictionary[f"{item.text(1)}-{item.text(2)}"])

    def open_image_patients(self, image, id_pacient, id_image, father):
        # Inicialização dos nós Folhas (Imagens dos pacientes)
        child_item = QTreeWidgetItem(father)
        child_item.setText(0, f"Imagem {id_image}")
        child_item.setText(1, str(id_pacient))
        child_item.setText(2, str(id_image))
        height, width = image.shape
        image_bytes = image.tobytes()
        q_img = QImage(image_bytes, width, height, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(q_img)
        self.pixmap_dictionary[f"{id_pacient}-{id_image}"] = pixmap
    
    def create_image_from_cropped(self, id_crop, crop_qpixmap):
        child_item = QTreeWidgetItem(self.cropped_imgs_node)
        child_item.setText(0, f"Corte {id_crop}")
        child_item.setText(1, "C")
        child_item.setText(2, str(id_crop))
        self.pixmap_dictionary[f"C-{id_crop}"] = crop_qpixmap

class ImageLabel(QLabel):
    cropped = pyqtSignal(int, QPixmap)

    def __init__(self):
        super().__init__()
        # Tamanho das imagens .mat, setei como tamanho maximo do ImageLabel
        self.setMaximumWidth(636)
        self.setMaximumHeight(434)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        self.is_rubber_band_active = False
        self.count_cropped = 0

    def display_image(self, pixmap):
        self.setPixmap(pixmap)
        self.resize(636, 434)
        self.is_rubber_band_active = True

    # Metodos ja setados para o funcionamento do rubberband (recorte de imagem)
    # ------------------------------------------------------------------------------------------- #

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
        adjusted_qrect = QRect(current_qrect.left(), current_qrect.top(), 
                           current_qrect.width(), current_qrect.height())
        crop_qpixmap = self.pixmap().copy(adjusted_qrect)
        self.cropped.emit(self.count_cropped, crop_qpixmap) # Emissao dos parametros necessarios para a conexao ImageProcessor - ImageLabel add_image_to_toolbar 
        self.count_cropped += 1
    
    # ------------------------------------------------------------------------------------------- #

class ImageProcessor(QMainWindow):
    def __init__(self, images = None):
        super().__init__()
        self.image_label = ImageLabel()
        self.toolbar_images = ToolBarImages(images)
        self.image_label.cropped.connect(self.toolbar_images.create_image_from_cropped) # Comunicacao ImageLabel -> ToolbarImage
        self.toolbar_images.display.connect(self.image_label.display_image) # Comunicacao ToolbarImage -> ImageLabel
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Processing Application (IPA)')
        # Tamanho minimo da tela != Tamanho maximo da image_label
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)

        # Menubar
        # TODO: Adicionar classe para o menubar (ou nao tmb pq ela é bem pequena)
        # ------------------------------------------------------------------------------------------- #

        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        open_file = QAction('Open Image', self)
        open_file.triggered.connect(self.open_image)
        file_menu.addAction(open_file)

        file_menu = menubar.addMenu('ROIs')
        crop_image = QAction('Crop Image', self)
        file_menu.addAction(crop_image)

        # ------------------------------------------------------------------------------------------- #

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
                q_img = QImage(image.data, width, height, QImage.Format_Grayscale8)
                pixmap = QPixmap.fromImage(q_img)
                self.toolbar_images.add_image_to_toolbar(file_name, pixmap)

# Funcao pegar dataset passado pelo professor
def get_images_dataset():
    path_input_dir = Path("liver")
    path_data = path_input_dir / "dataset_liver_bmodes_steatosis_assessment_IJCARS.mat"
    data = scipy.io.loadmat(path_data)
    data.keys()
    data_array = data['data']
    return data_array['images'][0]

if __name__ == '__main__':
    liver_images = get_images_dataset()
    app = QApplication(sys.argv)
    ex = ImageProcessor(liver_images)

    sys.exit(app.exec_())