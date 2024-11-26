# Integrante 01: André Fellipe Carvalho Silveira 
# Integrante 02: Leonardo Kamei Yukio
import matplotlib
matplotlib.use("QtAgg")
import sys
from pathlib import Path
from skimage.feature import graycomatrix, graycoprops
from scipy.stats import entropy
import seaborn as sns
import time
from PyQt5.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QVBoxLayout, QRubberBand, QApplication, QMainWindow,QAction, QFileDialog, QMenuBar,QToolBar, QTreeWidget, QTreeWidgetItem, QMessageBox,QTextEdit, QLabel, QHBoxLayout
from PyQt5.QtWidgets import QProgressBar, QPushButton,QDialog
from PyQt5.QtGui import QPixmap, QColor,QPainter,QImage,QWheelEvent,QMouseEvent,QPalette,QPen,QBrush
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QRect, QSize,QThread
from matplotlib.widgets import Button
import scipy.io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import cv2
import csv
import ast
import xgboost as xgb
from sklearn.model_selection import LeaveOneGroupOut,  cross_val_score
from sklearn.metrics import confusion_matrix
from tensorflow import keras
from keras.models import Model
from keras.applications.inception_v3 import InceptionV3
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from keras.layers import GlobalAveragePooling2D, Dense, Input
from tensorflow.keras.models import Model
from keras.layers import Dense, Flatten
import tensorflow as tf
from keras.models import load_model
from tensorflow.image import resize
import os


class ProcessadorDeImagens(QMainWindow):
    def __init__(self, imagens=None):
        super().__init__()
        self.visualizador_imagem = VisualizarImagem()
        self.toolbar_imagens = ToolBarImages(imagens)
        self.menubar = MenuBar()
        self.progress_window = None  
        
        self.momentHu = MomentHu(self.visualizador_imagem) 


        self.addToolBar(Qt.LeftToolBarArea, self.toolbar_imagens)

        self.visualizador_imagem.cropped.connect(self.toolbar_imagens.create_image_from_cropped)  # Comunicação VisualizarImagem -> ToolBarImage
        self.toolbar_imagens.display.connect(self.visualizador_imagem.exibir_Imagem)  # Comunicação ToolBarImage -> VisualizarImagem

        
        self.menubar.add_image.connect(self.toolbar_imagens.abrirImagem)  # Comunicação VisualizarImagem -> ToolBarImages
        self.menubar.crop_signal.connect(self.abrir_janela_crop)  # Comunicação MenuBar -> QMainWindow
        self.menubar.glcm_signal.connect(self.calcular_coocorenciaRadiais)
        self.menubar.histograma_signal.connect(self.mostrar_histograma)
        self.menubar.momento_Hu_signal.connect(self.exibir_momento_hu)
        self.menubar.save_signal.connect(self.toolbar_imagens.save_all_crops)

        self.menubar.Xgboost_signal.connect(self.mostrar_progress_window)
        self.menubar.Inception_signal.connect(self.exibir_Inception)

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Aplicação de Processamento de Imagens (API)')
        self.setMenuBar(self.menubar)
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)
        self.setCentralWidget(self.visualizador_imagem)
        self.show()

    def mostrar_histograma(self):
        pixmap_atual = self.visualizador_imagem.get_pixmap()
        if pixmap_atual:
            self.histograma = Histogram(pixmap_atual)
            self.histograma.show()

    def exibir_momento_hu(self):
        self.momentHu.momentos_invariantes_Hu()
        self.momentHu.show()

    def exibir_Inception(self):
        self.imagens_liver = obtain_steatosis_images()
        self.X, self.Y = preparate_image_rois("./og.csv", self.imagens_liver)
        
        test_inception_cross_val(self.X,self.Y)
        

    def mostrar_progress_window(self):
        self.progress_window = ProgressWindow(self)
        self.progress_window.show()  



    # Interface GLCM Raízes -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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
        inicio = time.time()
        for ax in self.axs.flatten():
            ax.clear()

        # Obtém a distância atual
        distancia = self.distancias[self.pagina_atual]

        for a_idx, angulo in enumerate(self.angulos):
            glcm = graycomatrix(self.imagem, distances=[distancia], angles=[angulo], normed=True)
            glcm_homogeneidade = graycoprops(glcm, 'homogeneity')[0, 0]
            glcm_normed2D = glcm[:, :, 0, 0]
            glcm_achatada = glcm_normed2D.ravel()
            glcm_entropia = entropy(glcm_achatada, base=2)

            ax = self.axs.flatten()[a_idx]
            #ax.imshow(glcm[:, :, 0, 0], cmap='coolwarm')
            ax.set_title(f'Distância {distancia},     Ângulo {self.rotulos_angulos[a_idx]}\n'
                         f'Homogeneidade: {glcm_homogeneidade:.4f},      Entropia: {glcm_entropia:.4f}')
            ax.axis('off')

        fim = time.time()
        print("Tempo de Execucao GLCM: ", fim-inicio)
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

    def calcular_coocorenciaRadiais(self):
        pixmap_atual = self.visualizador_imagem.get_pixmap()
        imagem = self.qpixmap_to_numpy(pixmap_atual)
        self.VisualizadorGLCM(imagem)

    def abrir_janela_crop(self):
        pixmap_atual = self.visualizador_imagem.get_pixmap()
        if pixmap_atual:
            self.janela_crop = CropWindow(pixmap_atual)
            self.janela_crop.show()

    def qpixmap_to_numpy(self, pixmap):
        qimage = pixmap.toImage()
        width = qimage.width()
        height = qimage.height()

        ptr = qimage.bits()
        ptr.setsize(height * width)
        arr = np.array(ptr).reshape((height, width))

        return arr

class MomentHu(QWidget):
    def __init__(self, visualizador_imagem):
        super().__init__()

        self.visualizador_imagem = visualizador_imagem


        self.layout = QVBoxLayout(self)


        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.layout.addWidget(self.text_edit)

    def momentos_invariantes_Hu(self):
        inicio = time.time()
        pixmap_atual = self.visualizador_imagem.get_pixmap()
        imagem = self.qpixmap_to_numpy(pixmap_atual) 

        if imagem is not None:

            momentos_centrais = cv2.moments(imagem)

            hu_moments = cv2.HuMoments(momentos_centrais).flatten()

            texto = "\nMomentos de Hu:\n"
            for i, value in enumerate(hu_moments):
                texto += f'Hu[{i + 1}]: {value:.4e}\n'

            self.text_edit.setPlainText(texto)
        else:
            print("Erro: A imagem não pôde ser convertida.")

        fim = time.time()
        print("Tempo de Execucao Hu: ", fim-inicio)
      

    def qpixmap_to_numpy(self, pixmap):
        qimage = pixmap.toImage()
        width = qimage.width()
        height = qimage.height()

        ptr = qimage.bits()
        ptr.setsize(height * width)
        arr = np.array(ptr).reshape((height, width))

        return arr
    
class CropWindow(QWidget):

    def __init__(self, imagem_orgaos):
        super().__init__()
        self.view = QGraphicsView()
        self.scene = QGraphicsScene(self.view)
        self.view.setScene(self.scene)
        self.hi = 0
        self.initUI(imagem_orgaos)

    def initUI(self, imagem_orgaos):
        self.setWindowTitle("Recorte de Imagem")
        main_layout = QVBoxLayout()  

        # Layout horizontal para as imagens
        images_layout = QHBoxLayout()

        for organ, data in imagem_orgaos.items():
            pixmap = data["pixmap"]
            coords = data["coords"]


            pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(pixmap_item)

            # Layout para cada imagem
            imagem_layout = QVBoxLayout()
            imagem_label = QLabel(organ)
            imagem_label.setAlignment(Qt.AlignCenter)
            imagem_layout.addWidget(imagem_label)

            pixmap_view = QGraphicsView()
            pixmap_scene = QGraphicsScene()
            pixmap_scene.addItem(pixmap_item)
            pixmap_view.setScene(pixmap_scene)

            imagem_layout.addWidget(pixmap_view)
            images_layout.addLayout(imagem_layout)

        main_layout.addLayout(images_layout)

        # Fígado com Hi
        self.new_liver_pix_map = self.calculoHi(imagem_orgaos)
        self.new_liver_numpy = self.qpixmap_to_numpy(self.new_liver_pix_map)
        self.momentosHu = self.get_moment_hu()
        self.homogeneity, self.entropy = self.calcular_homogeneidade_entropia()

        # Obter a previsão
        prediction, probabilities = self.test_new_liver_pixmap()

        # Layout para o fígado com Hi
        liver_layout = QVBoxLayout()
        pixmap_item = QGraphicsPixmapItem(self.new_liver_pix_map)
        self.scene.addItem(pixmap_item)

        pixmap_view = QGraphicsView()
        pixmap_scene = QGraphicsScene()
        pixmap_scene.addItem(pixmap_item)
        pixmap_view.setScene(pixmap_scene)

        liver_layout.addWidget(pixmap_view)

        # Exibir os resultados da previsão
        result_label = QLabel(f"Previsão: {'Saudável' if prediction == 0 else 'Doente'}\n"
                            f"Probabilidades (Saudável/Doente): {probabilities[0]:.2f}/{probabilities[1]:.2f}")
        result_label.setAlignment(Qt.AlignCenter)
        liver_layout.addWidget(result_label)

        # Adicionar layout do fígado ao layout principal
        main_layout.addLayout(liver_layout)

        # Configurar o layout principal na janela
        self.setLayout(main_layout)
        self.show()

    def test_new_liver_pixmap(self):
        X, Y = preparate_descriptors("./og.csv")
        X_test = np.array([self.momentosHu + self.homogeneity + self.entropy])  # Garantir listas homogêneas

        model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='mlogloss')
        model.fit(X, Y)

        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)

        return y_pred[0], y_pred_proba[0]

    def qpixmap_to_numpy(self, pixmap):
        qimage = pixmap.toImage()
        width = qimage.width()
        height = qimage.height()

        ptr = qimage.bits()
        ptr.setsize(height * width)
        arr = np.array(ptr).reshape((height, width))

        return arr

    def calcular_homogeneidade_entropia(self):
        distances = [1, 2, 4, 8]
        angles = [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]
        homogeneity_results = []
        entropy_results = []
        for distance_idx, distance in enumerate(distances):
            for angle_idx, angle in enumerate(angles):
                glcm = graycomatrix(self.new_liver_numpy, distances=[distance], angles=[angle], normed=True)
                glcm_homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]
                glcm_normed2D = glcm[:, :, 0, 0]
                glcm_flattened = glcm_normed2D.ravel()
                glcm_entropy = entropy(glcm_flattened, base=2)
                homogeneity_results.append(glcm_homogeneity)
                entropy_results.append(glcm_entropy)
        return homogeneity_results, entropy_results

    def get_moment_hu(self):
        if self.new_liver_numpy is not None:
            momentos_centrais = cv2.moments(self.new_liver_numpy)
            hu_moments = cv2.HuMoments(momentos_centrais).flatten()
            momentos_hu = hu_moments.tolist()
            return momentos_hu
        else:
            print("Erro:Nao foi possivel salvar o Hu junto com a ROI")

    def calculoHi(self, imagem_orgaos):
        figado = self.calculate_avg(imagem_orgaos["fígado"]["pixmap"])
        rim = self.calculate_avg(imagem_orgaos["rim"]["pixmap"])

        self.hi = figado / rim
        image = imagem_orgaos["fígado"]["pixmap"].toImage()
        nova_Imagem = QImage(image.size(), QImage.Format_Grayscale8)

        for x in range(image.width()):
            for y in range(image.height()):
                valor_Pixel = image.pixelColor(x, y).red()
                novo_Valor = min(int(valor_Pixel * self.hi), 255) # Tem que colocar esse limite, porque é 8bits de grayscale
                nova_Imagem.setPixel(x, y, QColor(novo_Valor, novo_Valor, novo_Valor).rgba())
        return QPixmap.fromImage(nova_Imagem)

    def calculate_avg(self, pixmap):
        imagem = pixmap.toImage()
        numero_Pixels = imagem.width() * imagem.height()
        somatorio_Pixels = 0

        for x in range(imagem.width()):
            for y in range(imagem.height()):
                valor_Pixel = imagem.pixelColor(x, y).red()
                somatorio_Pixels += valor_Pixel

        return somatorio_Pixels / numero_Pixels

    def get_new_liver_pix_map(self):
        return self.new_liver_pix_map

    def get_hi(self):
        return self.hi

class MenuBar(QMenuBar):
    add_image = pyqtSignal(str, QPixmap)
    crop_signal = pyqtSignal()
    glcm_signal = pyqtSignal()
    histograma_signal = pyqtSignal()
    momento_Hu_signal = pyqtSignal()
    save_signal = pyqtSignal()
    Xgboost_signal = pyqtSignal()
    AbrirImagem_signal = pyqtSignal()
    Inception_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        open_file = QAction('Abrir Imagem', self)
        open_file.triggered.connect(self.abrir_imagem)
        file_menu = self.addMenu('Arquivos')
        file_menu.addAction(open_file)

        file_menu = self.addMenu('ROIs')
        crop_image = QAction('Recortar Imagem', self)
        crop_image.triggered.connect(self.crop_signal.emit)
        file_menu.addAction(crop_image)

        save_rois = QAction('Salvar ROIs', self)
        save_rois.triggered.connect(self.save_signal.emit)
        file_menu.addAction(save_rois)

        # Menu GLCM Descritores
        glcm_menu = self.addMenu('GLCM Descritores')
        glcm_action = QAction('Mostrar GLCM', self)
        glcm_action.triggered.connect(self.glcm_signal.emit)  
        glcm_menu.addAction(glcm_action)

        # Menu GLCM Descritores
        histograma_menu = self.addMenu('Histograma')
        histograma_action = QAction('Mostrar Histograma', self)
        histograma_action.triggered.connect(self.histograma_signal.emit) 
        histograma_menu.addAction(histograma_action)

        #Menu Momento de Hu
        momento_hu_menu = self.addMenu('Momentos Invariantes de Hu')
        momento_hu_action = QAction('Mostrar Dados',self)
        momento_hu_action.triggered.connect(self.momento_Hu_signal.emit)
        momento_hu_menu.addAction(momento_hu_action)

        #Menu IA
        Xgboost_menu = self.addMenu('Xgboost')
        Xgboost_action = QAction('XGBOOST',self)
        Xgboost_action.triggered.connect(self.Xgboost_signal.emit)
        Xgboost_menu.addAction(Xgboost_action)

        #Inception Menu
        Inception_menu = self.addMenu('Inception')
        Inception_action = QAction('INCEPTION', self)
        Inception_action.triggered.connect(self.Inception_signal.emit)
        Inception_menu.addAction(Inception_action)

    def abrir_imagem(self, file_name):
        opcoes = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de Imagem", "", "Images (*.png *.jpg *.bmp *.mat);;All Files (*)", options=opcoes)
        if file_name:
            if file_name.endswith('.mat'):
                pass
            else:
                imagem = cv2.imread(file_name, cv2.IMREAD_GRAYSCALE)
                altura, largura = imagem.shape
                q_img = QImage(imagem.data, largura, altura, QImage.Format_Grayscale8)
                pixmap = QPixmap.fromImage(q_img)
                self.add_image.emit(file_name, pixmap)


 #Histograma---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class Histogram(QWidget):
    def __init__(self, pixmap):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.canvas = FigureCanvas(Figure())
        self.layout.addWidget(self.canvas)

        self.ax = self.canvas.figure.subplots()

        self.calcular_Histograma(pixmap)

    def calcular_Histograma(self, pixmap):
        imagem = self.qpixmap_to_numpy(pixmap)

        hist = cv2.calcHist([imagem], [0], None, [256], [0,255])

        self.ax.plot(hist, color='black')

        self.ax.set_ylim(0, 3000)
        self.ax.margins(y=0)

        self.ax.set_title('Histograma Preto-Branco')
        self.ax.set_xlabel('Intensidade do Pixel')
        self.ax.set_ylabel('Frequencia')
        self.canvas.draw()

    def qpixmap_to_numpy(self, pixmap):
        qimage = pixmap.toImage()
        width = qimage.width()
        height = qimage.height()

        ptr = qimage.bits()
        ptr.setsize(height * width)
        arr = np.array(ptr).reshape((height, width))

        return arr


 #Imagem Viewer ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class VisualizarImagem(QGraphicsView):
    cropped = pyqtSignal(QPixmap, int, int, int, int)

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setDragMode(QGraphicsView.NoDrag)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle,self)
        

        # Variáveis de controle de interação com rubber band
        # ---------------------------------------------------------- #
        
        self.zoom_factor = 1.15
        self.is_dragging = False
        self.enable_cropping = False
        self.is_resizing_rb = False
        self.is_translating = False
        self.direction = -1

        self.origin = QPoint()
        self.last_mouse_pos = QPoint()
        self.current_rect = QRect()

        # ---------------------------------------------------------- #

        self.setScene(self.scene)

        # Guardar o paciente e imagem do crop
        self.pacient_n = 0
        self.image_n = 0

    def exibir_Imagem(self, pixmap, nome):
        self.pacient_n, self.image_n = map(str, nome.split("-"))
        self.enable_cropping = True
        self.scene.clear()
        self.resetTransform()
        self.pix_map = pixmap
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(pixmap_item)

        # Definindo a cor da borda do rubber band para verde
        self.rubber_band.setStyleSheet("border: 2px solid green;")  # Borda verde


    def get_pixmap(self):
        return self.pix_map

    # Metodos ja setados para o funcionamento recorte de imagem e zoom
    # ------------------------------------------------------------------------------------------- #

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.scale(self.zoom_factor, self.zoom_factor)
        else:
            self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)

    def mousePressEvent(self, event):
        self.origin = event.pos()
        self.last_mouse_pos = event.pos()
        self.direction = self.click_near_border(event.pos())

        # Usuário clicando na borda do rubber band? -> Se sim, ativar Resize
        # Obs: Resize desativado porque sao ROIs 28x28 tamanho fixo
        if event.button() == Qt.LeftButton and self.direction != -1:
            self.is_resizing_rb = True

    # Usuário clicando dentro do rubber band? -> Se sim, ativar translação
        elif self.current_rect.contains(event.pos()):
            self.is_translating = True

    # Usuário está criando um novo quadrado? -> Se sim, criar um novo quadrado
        elif event.button() == Qt.LeftButton and self.enable_cropping:
            self.current_rect = QRect(self.origin, QSize(28, 28))
            self.rubber_band.setGeometry(self.current_rect)
            self.rubber_band.show()

    # Usuário está arrastando a visualização da imagem? -> Se sim, ative is_dragging
        elif event.button() == Qt.RightButton:
            self.is_dragging = True
            self.setCursor(Qt.ClosedHandCursor)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
    # Escalando ou Arrastando a visualização da imagem
        if self.is_dragging:
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())

        # Dimensionando o rubber band
        elif self.is_resizing_rb:
            match self.direction:
                case 1:
                    self.current_rect.setRight(event.pos().x())
                case 2:
                    self.current_rect.setTop(event.pos().y())
                case 3:
                    self.current_rect.setLeft(event.pos().x())
                case 4:
                    self.current_rect.setBottom(event.pos().y())
            self.rubber_band.setGeometry(self.current_rect.normalized())
        # Transladando o rubber band
        elif self.is_translating:
            delta = event.pos() - self.last_mouse_pos
            self.current_rect.translate(delta)
            self.rubber_band.setGeometry(self.current_rect.normalized())
            self.last_mouse_pos = event.pos()
        else:
            self.current_rect = QRect(self.origin, event.pos())
            self.current_rect = self.current_rect.normalized()  # Ajusta para evitar retângulos invertidos
            self.rubber_band.setGeometry(self.current_rect)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        self.is_translating = False
        self.is_resizing_rb = False

        if event.button() == Qt.RightButton:

            self.setCursor(Qt.ArrowCursor)

        super().mouseReleaseEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Space:
            rubber_band_rect = self.rubber_band.geometry()
            scene_rect = self.mapToScene(rubber_band_rect).boundingRect()
            pixmap_item = self.scene.items()[0]
            original_pixmap = pixmap_item.pixmap()
            cropped_pixmap = original_pixmap.copy(scene_rect.toRect())
            self.cropped.emit(cropped_pixmap, int(self.pacient_n), int(self.image_n), int(scene_rect.x()), int(scene_rect.y()))
    # ------------------------------------------------------------------------------------------- #

    def click_near_border(self, pos):
        band_rect = self.rubber_band.geometry()

        margin = 5 # Margem de detecção de proximidade de borda (Mudar caso necessário)

        # Rosa dos ventos (Leste, Norte, Oeste, Sul - 1, 2, 3, 4) simplesmente para deixar o código mais eficiente, se tiver muito ilegível mudar
        # if (abs(pos.x() - band_rect.right()) < margin): return 1 
        # elif (abs(pos.y() - band_rect.top()) < margin): return 2
        # elif (abs(pos.x() - band_rect.left()) < margin): return 3
        # elif (abs(pos.y() - band_rect.bottom()) < margin): return 4
        
        return -1



# Classe ToolBarImages: Classe que mostra as imagens adicionadas pelo botao load, "croppadas" e do dataset Liver -----------------------------------------------------------------------------------------------------------
class ToolBarImages(QToolBar):
    display = pyqtSignal(QPixmap, str)


    def __init__(self, images = None):
        super().__init__("All Images")
        self.images = images

        self.has_selected_liver = False
        self.has_selected_cortex = False
        self.has_selected_kidney = False

        self.organ_images = {}
        self.pacient_id = 0
        self.image_id = 0
        self.crop_id = 0

        self.crop_window = None

        # Inicialização da hierarquia de pastas
        # ------------------------------------------------------------------------------------------- #

        self.folder_hierarchy = QTreeWidget()
        self.pixmap_dictionary = {}
        self.addWidget(self.folder_hierarchy)


        self.folder_hierarchy.itemClicked.connect(self.exibir_Imagem)
        self.folder_hierarchy.setHeaderHidden(True)

        self.imagem_adicionadas = QTreeWidgetItem(self.folder_hierarchy)
        self.imagem_adicionadas.setText(0, f"Imagens Adicionadas")

        self.cropped_imgs_node = QTreeWidgetItem(self.folder_hierarchy)
        self.cropped_imgs_node.setText(0, f"Coleção de Cortes")



        # ------------------------------------------------------------------------------------------- #

        # Fazendo o a extracao das imagens do formato images[0][n][m] para a hierarquia de pastas
        for id_pacient,patient in enumerate(self.images):
            # Inicialização do nós Raizes (Nó dos pacientes)
            patient_node = QTreeWidgetItem(self.folder_hierarchy)
            patient_node.setText(0, f"Paciente {id_pacient}")
            for id_image,image in enumerate(patient):
                self.abrir_imagem_paciente(image, id_pacient, id_image, patient_node)

    
    def exibir_Imagem(self, item, column):
        # Deixar Nós raiz inclicáveis (nós com header de paciente)
        if item.parent() is None:
            return



        self.display.emit(self.pixmap_dictionary[f"{item.text(1)}-{item.text(2)}"], f"{item.text(1)}-{item.text(2)}")
        self.has_selected_liver = False
        self.has_selected_cortex = False
        self.has_selected_kidney = False

    def abrir_imagem_paciente(self, image, id_pacient, id_image, father):
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

    def create_image_from_cropped(self, crop_qpixmap, paciente_n, imagem_n, coord_x, coord_y):
        if paciente_n != self.pacient_id and imagem_n != self.image_id:
            self.organ_images = {}
            self.pacient_id = paciente_n
            self.image_id = imagem_n

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText("Informe o órgao dessa imagem")
        msg.setWindowTitle("Recorte")

        button_liver = button_cortex = button_kidney = None

        if not self.has_selected_liver:
            button_liver = msg.addButton("Fígado", QMessageBox.ActionRole)
        if not self.has_selected_cortex:
            button_cortex = msg.addButton("Cortex Renal", QMessageBox.ActionRole)
        if not self.has_selected_kidney:
            button_kidney = msg.addButton("Rim", QMessageBox.ActionRole)

        msg.exec_()

        if msg.clickedButton() == button_liver:
            self.has_selected_liver = True
            organ = "fígado"
        elif msg.clickedButton() == button_cortex:
            self.has_selected_cortex = True
            organ = "córtex"
        else:
            self.has_selected_kidney = True
            organ = "rim"

        #EntropiaHomogeneidadeCSV = salvar_entropia_homogeneidadeCSV()
        self.organ_images[organ] = {
            "pixmap": crop_qpixmap,
            "coords": (coord_x, coord_y),
            "organ": organ
        }


        if self.has_selected_liver and self.has_selected_cortex and self.has_selected_kidney:
            self.crop_window = CropWindow(self.organ_images)
            coords_liver = self.organ_images["fígado"]["coords"]
            coords_kidney = self.organ_images["rim"]["coords"]
            # new_liver_pix_map nao é passado por emit pois self.save_img precisa de todos esses parametros para funcionar
            self.save_img(self.crop_window.get_new_liver_pix_map(),f"ROI_{paciente_n}_{imagem_n}", coords_liver, coords_kidney, paciente_n, self.crop_window.get_hi(), 
                          self.crop_window.get_moment_hu(), self.crop_window.calcular_homogeneidade_entropia())
            # nao precisa das ROIs do rim

            # self.save_img(self.organ_images["rim"]["pixmap"], f"RIM_{pacient_n}_{image_n}", coord_x, coord_y, pacient_n)


    def abrirImagem(self,filename,crop_image):
        child_item = QTreeWidgetItem(self.imagem_adicionadas)
        child_item.setText(0, filename)
        child_item.setText(1, "A")
        child_item.setText(2, filename)
        self.pixmap_dictionary[f"A-{filename}"] = crop_image

    def save_img(self, crop_qpixmap, file_name, coords_liver, coords_kidney, paciente_n, hi, hu, homogeneidade_entropia):
        homogeneidade, entropia = homogeneidade_entropia
        child_item = QTreeWidgetItem(self.cropped_imgs_node)
        child_item.setText(0, file_name)
        child_item.setText(1, f"C")
        child_item.setText(2, str(self.crop_id))
        child_item.setText(3, f"{coords_liver}")
        child_item.setText(4, f"{coords_kidney}")
        if paciente_n <= 16:
            child_item.setText(5, "saudável")
        else:
            child_item.setText(5, "esteatose")
        child_item.setText(6, f"{hi}")
        child_item.setText(7, f"{hu}")
        child_item.setText(8, f"{homogeneidade}")
        child_item.setText(9, f"{entropia}")


        self.pixmap_dictionary[f"C-{self.crop_id}"] = crop_qpixmap
        # img = crop_qpixmap.toImage() 
        # img.save(f"./rois/{file_name}.png")
        self.crop_id += 1

    def save_all_crops(self):

        with open("data.csv", mode='w', newline='') as file:
            writer = csv.writer(file)
        
            writer.writerow(["Arquivo", "Classe", "Canto superior esquerdo fígado", "Canto superior esquerdo rim", "Altura", "Comprimento"])

            for i in range(self.cropped_imgs_node.childCount()):
                node = self.cropped_imgs_node.child(i)
                pixmap = self.pixmap_dictionary[f"{node.text(1)}-{node.text(2)}"]

                pixmap_item = QGraphicsPixmapItem(pixmap)

                bounding_rect = pixmap_item.boundingRect()

                height = pixmap.height()
                width = pixmap.width()

                print(f"Arquivo: {node.text(0)}")
                print(f"Classe: {node.text(5)}")
                print(f"Canto superior esquerdo fígado: ({node.text(3)})")
                print(f"Canto superior esquerdo rim: ({node.text(4)})")
                print(f"Altura: {height}, Comprimento: {width}")
                print(f"Hi: ({node.text(6)})")
                print(f"Hu: ({node.text(7)})")
                print(f"Homoogeneidade: ({node.text(8)})")
                print(f"Entropia: ({node.text(9)})")
                print("-" * 30)

                writer.writerow([
                node.text(0),
                node.text(5),
                node.text(3),
                node.text(4),
                height,
                width,
                node.text(6),
                node.text(7),
                node.text(8),
                node.text(9),
                ])

def preparate_descriptors(path):
    X = []
    Y = []
    with open(path, mode='r', encoding='utf-8') as file:
        csv_dict = csv.DictReader(file)
        for line in csv_dict:
            try:
                hu = ast.literal_eval(line["Hu"])
                homogeneity = ast.literal_eval(line["Homogeneidade"])
                entropy = ast.literal_eval(line["Entropia"])

                features = hu + homogeneity + entropy

                label = 0 if line["Classe"] == "saudavel" else 1
                X.append(features)
                Y.append(label)
            except (ValueError, SyntaxError, KeyError) as e:
                print(f"Erro ao processar linha: {line}, erro: {e}")
    
    # Converte para arrays NumPy para usar no XGBoost
    return np.array(X, dtype=np.float32), np.array(Y, dtype=np.int32)



def preparate_image_rois(path, images_liver):
    X, Y = [], []
    with open(path, mode='r', encoding='utf-8') as file:
        csv_dict = csv.DictReader(file)
        for line in csv_dict:
            ids = line["Arquivo"].split("_")
            id_pacient = int(ids[1])
            id_image = int(ids[2])
            x, y = map(int, line["Liver"].strip("()").split(", "))
            image = images_liver[id_pacient][id_image]
            X.append(image[y:y+28, x:x+28].flatten())
            if id_pacient < 17:
                label = 1
            else: 
                label = 0
            Y.append(label)
    return np.array(X), np.array(Y)

class ComponenteProgress(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.confusion_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.layout.addWidget(self.confusion_canvas)
        self.confusion_ax = self.confusion_canvas.figure.add_subplot(111)

        self.barra_progresso = QProgressBar(self)
        self.barra_progresso.setValue(0)
        self.layout.addWidget(self.barra_progresso)

        self.botaoStart = QPushButton("Iniciar Validação Cruzada", self)
        self.botaoStart.clicked.connect(self.comecar_validacao)
        self.layout.addWidget(self.botaoStart)

        self.worker = None

    def comecar_validacao(self):
        self.botaoStart.setEnabled(False)

        X, Y = preparate_descriptors("./og.csv")

        self.worker = Xgboost(X, Y)
        self.worker.progresso_atualizado.connect(self.atualizar_barra_progresso)
        self.worker.trabalho_finalizado.connect(self.trabalho_concluido)
        self.worker.confusao_pronta.connect(self.mostrar_matriz_confusao)
        self.worker.start()

    def atualizar_barra_progresso(self, value):
        self.barra_progresso.setValue(value)

    def trabalho_concluido(self, messagem):
        self.botaoStart.setEnabled(True)
        self.barra_progresso.setValue(100)
        print(messagem)


    def mostrar_matriz_confusao(self, matriz_confusao):
        self.confusion_ax.clear()

        TN, FP, FN, TP = matriz_confusao.ravel()

        annotations = [
            [f"{TN}\nVN", f"{FP}\nFP"],
            [f"{FN}\nFN", f"{TP}\nVP"]
        ]

        sns.heatmap(matriz_confusao, annot=annotations, fmt="s", cmap="Greens", ax=self.confusion_ax,
                    cbar=False, square=True, linewidths=1, linecolor='black')

        self.confusion_ax.set_title("Matriz de Confusão")
        self.confusion_ax.set_xlabel("Predito")
        self.confusion_ax.set_ylabel("Real")

        self.confusion_canvas.draw()

        

class ProgressWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Validação Cruzada - XGBOOST")
        
        self.setGeometry(600, 400, 800, 600)
        
        screen = self.screen()
        rect = screen.availableGeometry()

        x = (rect.width() - self.width()) // 2
        y = (rect.height() - self.height()) // 2
        self.move(x, y)

        self.setWindowModality(Qt.ApplicationModal)

        self.layout = QVBoxLayout(self)

        self.progresso_componente = ComponenteProgress(self)
        self.layout.addWidget(self.progresso_componente)



class Xgboost(QThread):


    progresso_atualizado = pyqtSignal(int)
    trabalho_finalizado = pyqtSignal(str)
    confusao_pronta = pyqtSignal(np.ndarray)

    def __init__(self, X, Y, parent=None):
        super().__init__(parent)
        self.X = X
        self.Y = Y

    def run(self):
        inicio = time.time()
        model = xgb.XGBClassifier(use_label_encoder=False)
        pacientes_indices = np.arange(55)
        grupos = np.repeat(pacientes_indices, 10)
        logo = LeaveOneGroupOut()

        scores = []
        all_y_true = []
        all_y_pred = []
        indices_incorretos = []
        total_splits = len(list(logo.split(self.X, self.Y, grupos)))
        current_split = 0

        for train_index, test_index in logo.split(self.X, self.Y, grupos):
            X_train, X_test = self.X[train_index], self.X[test_index]
            Y_train, Y_test = self.Y[train_index], self.Y[test_index]

            model.fit(X_train, Y_train)
            y_pred = model.predict(X_test)
            all_y_true.extend(Y_test)
            all_y_pred.extend(y_pred)

            incorreto = test_index[Y_test != y_pred]  # Indices de previsões incorretas
            indices_incorretos.extend(incorreto)
            
            acuracia = model.score(X_test, Y_test)
            scores.append(acuracia)
            
            print(test_index," ",acuracia)
            

            current_split += 1
            progresso = int((current_split / total_splits) * 100)
            self.progresso_atualizado.emit(progresso)

        print(indices_incorretos)
        print(len(indices_incorretos))
        acuracia_media = np.mean(scores)
        std_acuracia = np.std(scores)
        matriz_confusao = confusion_matrix(all_y_true, all_y_pred)
        TN, FP, FN, TP = matriz_confusao.ravel()

        
        acuracia = (TP + TN) / (TP + TN + FP + FN)
        sensibilidade = TP / (TP + FN)
        especificidade = TN / (TN + FP)
        resultado_mensagem = (
            f"Acurácia média (cross-validation): {acuracia_media:.2f}\n"
            f"Desvio padrão (cross-validation): {std_acuracia:.2f}\n"
            f"Métricas da matriz de confusão:\n"
            f"Acurácia: {acuracia:.2f}\n"
            f"Sensibilidade: {sensibilidade:.2f}\n"
            f"Especificidade: {especificidade:.2f}"
        )
        fim = time.time()
        print("Tempo do XgBoost total:",fim - inicio)
        self.trabalho_finalizado.emit(resultado_mensagem)
        self.confusao_pronta.emit(matriz_confusao)



#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def resize_all_images(X):
    X = X.reshape((-1, 28, 28))  # Transformar para (550, 28, 28)
    X = np.stack((X,) * 3, axis=-1)
    X = np.array([resize(img, (76, 76)).numpy() for img in X])
    return X

def atualizarInceptionConfusao(idx, ax, matriz_confusaoList):
    ax.clear() 
    sns.heatmap(matriz_confusaoList[idx], annot=True, fmt="d", cmap="Blues",
                xticklabels=["Predito Negativo", "Predito Positivo"],
                yticklabels=["Real Negativo", "Real Positivo"], ax=ax, cbar=False)
    ax.set_title(f'Matriz de Confusão - Validação Cruzada {idx+1}')
    ax.set_ylabel('Real')
    ax.set_xlabel('Predito')
    plt.draw()


def proxima_iteracao(event, index_atual, ax, matriz_confusaoList):
    index_atual[0] = min(index_atual[0] + 1, len(matriz_confusaoList) - 1)
    atualizarInceptionConfusao(index_atual[0], ax, matriz_confusaoList)


def iteracao_anterior(event, index_atual, ax, matriz_confusaoList):
    index_atual[0] = max(index_atual[0] - 1, 0)
    atualizarInceptionConfusao(index_atual[0], ax, matriz_confusaoList)


def test_inception_cross_val(X, Y):
    
    X = resize_all_images(X) 
    print(X.shape)
    pacientes_indices = np.arange(55)
    grupos = np.repeat(pacientes_indices, 10)
    logo = LeaveOneGroupOut()

    acuracias = []
    all_y_true = []
    all_y_pred = []
    # Diretório para salvar os modelos
    save_dir = "saved_models"
    os.makedirs(save_dir, exist_ok=True)
    
    matriz_confusaoList = []  # Lista para armazenar as matrizes de confusão da Inception

    for i, (train_idx, test_idx) in enumerate(logo.split(X, Y, grupos)):
        print(f"Iniciando iteração para o grupo de treino {train_idx[:5]}...")
        # #
        # if i > 4: break
        # # Criar um novo modelo em cada iteração
        # input_tensor = Input(shape=(76, 76, 3))
        # base_modelo = InceptionV3(weights='imagenet', include_top=False, input_tensor=input_tensor)
        # x = base_modelo.output
        # x = GlobalAveragePooling2D()(x)
        # x = Dense(1, activation='sigmoid')(x)
        # model = Model(inputs=base_modelo.input, outputs=x)
        #
        model = load_model(f"./saved_models/model_iteration_{i}.h5")

        

        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

        X_train, X_test = X[train_idx], X[test_idx]
        Y_train, Y_test = Y[train_idx], Y[test_idx]

        #
        # train_datagen = ImageDataGenerator(preprocessing_function=None)
        # test_datagen = ImageDataGenerator(preprocessing_function=None)
        # train_generator = train_datagen.flow(X_train, Y_train, batch_size=32)
        # test_generator = test_datagen.flow(X_test, Y_test, batch_size=32)
        #
        with tf.device('/GPU:0'):
            # model.fit(train_generator, epochs=5, verbose=1)
            y_pred = model.predict(X_test)

            y_pred_class = (y_pred > 0.5).astype(int)  # Converte probabilidades para 0 ou 1

            all_y_true.extend(Y_test)
            all_y_pred.extend(y_pred_class)  
           
        #-----------------------------------------------------
        # acuracia = model.evaluate(test_generator, verbose=0)[1]
        # acuracias.append(acuracia)
        # print(f"Iteração concluída. Acurácia: {acuracia:.2f}")
        # # Salvando o modelo após o treinamento
        # salvar_modelo_path = os.path.join(save_dir, f"model_iteration_{i}.h5")
        # model.save(salvar_modelo_path)
        # print(f"Modelo salvo em: {salvar_modelo_path}")
        # precisao_media = np.mean(acuracias)
        # std_acuracias = np.std(acuracias)
        #--------------------------------------------------------

        # Calcular a matriz de confusão
        matriz_confusao = confusion_matrix(all_y_true, all_y_pred, labels=[0, 1])
        matriz_confusaoList.append(matriz_confusao)  # Salvar a matriz de confusão

        if matriz_confusao.shape == (2, 2):
            TN, FP, FN, TP = matriz_confusao.ravel()
        else:
            print(f"Matriz de confusão inesperada: {matriz_confusao}")
            TN, FP, FN, TP = 0, 0, 0, 0  

        acuracia = (TP + TN) / (TP + TN + FP + FN)
        sensibilidade = TP / (TP + FN)
        especificidade = TN / (TN + FP)
        resultado_mensagem = (
            f"Métricas da matriz de confusão:\n"
            f"Acurácia: {acuracia:.2f}\n"
            f"Sensibilidade: {sensibilidade:.2f}\n"
            f"Especificidade: {especificidade:.2f}"
        )
        print(resultado_mensagem)

    # Exibição interativa das matrizes de confusão
    fig, ax = plt.subplots(figsize=(6, 6))
    index_atual = [0]  # Controlador para navegação entre matrizes
    plt.subplots_adjust(bottom=0.15)

    # Conectar os eventos de tecla para navegação entre as matrizes
    fig.canvas.mpl_connect('key_press_event', lambda event: proxima_iteracao(event, index_atual, ax, matriz_confusaoList) if event.key == 'right' else iteracao_anterior(event, index_atual, ax, matriz_confusaoList) if event.key == 'left' else None)

    atualizarInceptionConfusao(0, ax, matriz_confusaoList)  # Exibir a primeira matriz de confusão
    plt.show()
    print(f"Acurácia média (cross-validation): {np.mean(acuracias):.2f}")
    print(f"Desvio padrão (cross-validation): {np.std(acuracias):.2f}")



#Obter Conjunto ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def obtain_steatosis_images():
    # Colocar a localização da pasta "liver" para ajudar na procura da pasta
    path_input_dir = Path("liver")
    path_data = path_input_dir / "dataset_liver_bmodes_steatosis_assessment_IJCARS.mat"
    data = scipy.io.loadmat(path_data)
    data.keys()
    data_array = data['data']
    return data_array['images'][0]


if __name__ == '__main__':
    imagens_liver = obtain_steatosis_images()
    X, Y = preparate_image_rois("./og.csv", imagens_liver)
    # test_results = test_xgboost_cross_val(X, Y)
    #test_inception_cross_val(X, Y)
    app = QApplication(sys.argv)
    ex = ProcessadorDeImagens(imagens_liver)

    sys.exit(app.exec_())