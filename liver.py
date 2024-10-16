# Integrante 01: André Fellipe Carvalho Silveira
# Integrante 02: Leonardo Kamei Yukio

import sys
from pathlib import Path
from skimage.feature import graycomatrix
from skimage.feature import graycoprops
from scipy.stats import entropy
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt
import scipy.io
from include import utility, toolbar, image_viewer, menubar, crop_window, histogram
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
        self.imagem = imagem
        self.distancias = [1, 2, 4, 8]
        self.angulos = [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]
        self.rotulos_angulos = ['0°', '45°', '90°', '135°']
        self.pagina_atual = 0

        self.total_paginas = len(self.distancias)

        self.fig, self.axs = plt.subplots(2, 2, figsize=(10, 8))
        self.atualizar_graficos()
      
        plt.subplots_adjust(bottom=0.2)
        self.botao_anterior = plt.Button(plt.axes([0.35, 0.05, 0.1, 0.075]), 'Anterior')
        self.botao_proximo = plt.Button(plt.axes([0.55, 0.05, 0.1, 0.075]), 'Próximo')

        self.botao_anterior.on_clicked(self.pagina_anterior)
        self.botao_proximo.on_clicked(self.proxima_pagina)
        plt.show()

    def atualizar_graficos(self):
        for ax in self.axs.flatten():
            ax.clear()

        # Obtém a distância atual
        distancia = self.distancias[self.pagina_atual]

        for a_idx, angulo in enumerate(self.angulos):
            glcm = graycomatrix(self.imagem, distances=[distancia], angles=[angulo], normed=True)
            glcm_homogeneidade = graycoprops(glcm, 'homogeneity')[0, 0]
            glcm_normed2D = glcm[:, :, 0, 0]
            glcm_flattened = glcm_normed2D.ravel()  # Achata para ficar um vetor de probabilidade
            glcm_entropia = entropy(glcm_flattened, base=2)

            ax = self.axs.flatten()[a_idx]
            ax.imshow(glcm[:, :, 0, 0], cmap='coolwarm')
            ax.set_title(f'Distância {distancia},     Ângulo {self.rotulos_angulos[a_idx]}\n'
                         f'Homogeneidade: {glcm_homogeneidade:.4f},      Entropia: {glcm_entropia:.4f}')
            ax.axis('off')

        plt.suptitle(f'GLCM para Distância {distancia}')
        plt.draw()

    def proxima_pagina(self, event):
        if self.pagina_atual < self.total_paginas - 1:
            self.pagina_atual += 1
            self.atualizar_graficos()

    def pagina_anterior(self, event):
        if self.pagina_atual > 0:
            self.pagina_atual -= 1
            self.atualizar_graficos()
    
    # FIM Interface GLCM Raízes ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------  
    
    def calcular_coocorenciaRadiais(self):
        pixmap_atual = self.visualizador_imagem.get_pixmap()
        imagem = self.histograma.qpixmap_to_numpy(pixmap_atual)
        visualizador = self.VisualizadorGLCM(imagem)
    
    # FIM Interface GLCM Raízes ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def abrir_janela_crop(self):
        pixmap_atual = self.visualizador_imagem.get_pixmap()
        if pixmap_atual:
            self.janela_crop = crop_window.CropWindow(pixmap_atual)
            self.janela_crop.show()


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
