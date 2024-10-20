# Integrante 01: André Fellipe Carvalho Silveira
# Integrante 02: Leonardo Kamei Yukio

import sys
from pathlib import Path
from skimage.feature import graycomatrix, graycoprops
from scipy.stats import entropy
from PyQt5.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QVBoxLayout, QRubberBand, QApplication, QMainWindow
from PyQt5.QtGui import QPixmap, QColor,QPainter
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QRect, QSize
import scipy.io
from include import utility, toolbar, image_viewer, menubar, histogram
import matplotlib.pyplot as plt
import numpy as np

class ProcessadorDeImagens(QMainWindow):
    def __init__(self, imagens=None):
        super().__init__()
        self.visualizador_imagem = image_viewer.ImageViewer()
        self.toolbar_imagens = toolbar.ToolBarImages(imagens)
        self.menubar = menubar.MenuBar()
        self.addToolBar(Qt.LeftToolBarArea, self.toolbar_imagens)
        self.visualizador_imagem.cropped.connect(self.toolbar_imagens.create_image_from_cropped)  # Comunicação ImageViewer -> ToolBarImage

        self.toolbar_imagens.display.connect(self.visualizador_imagem.display_image)  # Comunicação ToolBarImage -> ImageViewer
        self.toolbar_imagens.display.connect(self.mostrar_histograma)  # Comunicação ToolBarImage -> ImageViewer
        self.toolbar_imagens.display.connect(self.calcular_coocorenciaRadiais)

        self.menubar.add_image.connect(self.toolbar_imagens.display_image)  # Comunicação ImageViewer -> ToolBarImages
        self.menubar.crop_signal.connect(self.abrir_janela_crop)  # Comunicação MenuBar -> QMainWindow

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Aplicação de Processamento de Imagens (API)')
        # Tamanho mínimo da tela != Tamanho máximo do visualizador de imagens
        self.setMenuBar(self.menubar)
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)
        self.setCentralWidget(self.visualizador_imagem)
        self.show()
    
    def mostrar_histograma(self):
        pixmap_atual = self.visualizador_imagem.get_pixmap()
        if pixmap_atual:
            self.histograma = histogram.Histogram(pixmap_atual)
            self.histograma.show()

    # Interface GLCM Raízes ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def VisualizadorGLCM(self, imagem):
        distancias = [1, 2, 4, 8]
        rotulos_distancias = ['1', '2', '4', '8']
        fig, axs = plt.subplots(2, 2, figsize=(10, 8))

        for ax in axs.flatten():
            ax.clear()

        for d_idx, distancia in enumerate(distancias):
            glcm = graycomatrix(imagem, distances=[distancia], angles=[0], normed=True)
            glcm_homogeneidade = graycoprops(glcm, 'homogeneity')[0, 0]
            glcm_flattened = glcm[:, :, 0, 0].ravel()
            glcm_entropia = entropy(glcm_flattened, base=2)
            ax = axs.flatten()[d_idx]
            ax.set_title(f'Distância {rotulos_distancias[d_idx]}\n'
                         f'Homogeneidade: {glcm_homogeneidade:.4f}, Entropia: {glcm_entropia:.4f}')
            ax.axis('off')
        
        plt.suptitle('GLCM')
        plt.show()

    def calcular_coocorenciaRadiais(self):
        pixmap_atual = self.visualizador_imagem.get_pixmap()
        imagem = self.histograma.qpixmap_to_numpy(pixmap_atual)
        self.VisualizadorGLCM(imagem)
    
    def abrir_janela_crop(self):
        pixmap_atual = self.visualizador_imagem.get_pixmap()
        if pixmap_atual:
            self.janela_crop = CropWindow(pixmap_atual)
            self.janela_crop.show()


class CropWindow(QWidget):
    cropped = pyqtSignal(int, QPixmap)
    
    def __init__(self, pixmap):
        super().__init__()
        self.view = QGraphicsView()
        self.scene = QGraphicsScene(self.view)
        self.view.setScene(self.scene)
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(pixmap_item)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        self.count_cropped = 0

        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Recorte de Imagem")
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)
        self.show()
        

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.origin, QSize(28, 28)))
            self.rubber_band.show()
    
    def mouseMoveEvent(self, event):
     if not self.origin.isNull() and self.rubber_band.isVisible():
        # Calcula o tamanho atual do retângulo de seleção
        current_rect = QRect(self.origin, event.pos()).normalized()
        
        # Limita o tamanho do retângulo para 28x28 pixels
        size = min(current_rect.width(), 28), min(current_rect.height(), 28)
        limited_rect = QRect(self.origin, QSize(*size))
        self.rubber_band.setGeometry(limited_rect)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rubber_band.hide()
            rubber_band_rect = self.rubber_band.geometry()
            scene_rect = self.view.mapToScene(rubber_band_rect).boundingRect()
            pixmap_item = self.scene.items()[0]
            original_pixmap = pixmap_item.pixmap()
            cropped_pixmap = original_pixmap.copy(scene_rect.toRect())
            self.cropped.emit(self.count_cropped, cropped_pixmap)
            self.count_cropped += 1


def obter_conjunto_imagens():
    # Colocar a localização da pasta "liver" para ajudar na procura da pasta
    path_input_dir = Path("liver")
    path_data = path_input_dir / "dataset_liver_bmodes_steatosis_assessment_IJCARS.mat"
    data = scipy.io.loadmat(path_data)
    data.keys()
    data_array = data['data']
    return data_array['images'][0]

if __name__ == '__main__':
    imagens_liver = obter_conjunto_imagens()
    app = QApplication(sys.argv)
    ex = ProcessadorDeImagens(imagens_liver)

    sys.exit(app.exec_())
