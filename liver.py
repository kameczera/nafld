# Integrante 01: André Fellipe Carvalho Silveira
# Integrante 02: Leonardo Kamei Yukio

import sys
from pathlib import Path
from skimage.feature import graycomatrix, graycoprops
from scipy.stats import entropy
from PyQt5.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QVBoxLayout, QRubberBand, QApplication, QMainWindow,QAction, QFileDialog, QMenuBar,QToolBar, QTreeWidget, QTreeWidgetItem, QMessageBox,QTextEdit, QLabel, QHBoxLayout
from PyQt5.QtGui import QPixmap, QColor,QPainter,QImage,QWheelEvent,QMouseEvent
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QRect, QSize
import scipy.io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import cv2
import csv
import xgboost as xgb
from sklearn.model_selection import LeaveOneGroupOut,  cross_val_score
from tensorflow import keras
from keras.applications.inception_v3 import InceptionV3
from tensorflow.keras.preprocessing.image import ImageDataGenerator

class ProcessadorDeImagens(QMainWindow):
    def __init__(self, imagens=None):
        super().__init__()
        self.visualizador_imagem = ImageViewer()
        self.toolbar_imagens = ToolBarImages(imagens)
        self.menubar = MenuBar()

        # Inicializar o MomentHu com referências ao visualizador e histograma
        self.momentHu = MomentHu(self.visualizador_imagem)  # Passar apenas visualizador_imagem


        self.addToolBar(Qt.LeftToolBarArea, self.toolbar_imagens)

        self.visualizador_imagem.cropped.connect(self.toolbar_imagens.create_image_from_cropped)  # Comunicação ImageViewer -> ToolBarImage
        self.toolbar_imagens.display.connect(self.visualizador_imagem.display_image)  # Comunicação ToolBarImage -> ImageViewer

        self.menubar.add_image.connect(self.toolbar_imagens.display_image)  # Comunicação ImageViewer -> ToolBarImages
        self.menubar.crop_signal.connect(self.abrir_janela_crop)  # Comunicação MenuBar -> QMainWindow
        self.menubar.glcm_signal.connect(self.calcular_coocorenciaRadiais)
        self.menubar.histograma_signal.connect(self.mostrar_histograma)
        self.menubar.momento_Hu_signal.connect(self.exibir_momento_hu)  # Conectar o sinal ao método que irá definir o histograma
        self.menubar.save_signal.connect(self.toolbar_imagens.save_all_crops)

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

    # O restante da sua classe ProcessadorDeImagens permanece o mesmo


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
            #ax.imshow(glcm[:, :, 0, 0], cmap='coolwarm')
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



from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit
import numpy as np
import cv2

class MomentHu(QWidget):
    def __init__(self, visualizador_imagem):
        super().__init__()

        self.visualizador_imagem = visualizador_imagem


        self.layout = QVBoxLayout(self)


        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.layout.addWidget(self.text_edit)

    def momentos_invariantes_Hu(self):
        pixmap_atual = self.visualizador_imagem.get_pixmap()
        imagem = self.qpixmap_to_numpy(pixmap_atual)  # Converter QPixmap para numpy

        if imagem is not None:

            momentos_centrais = cv2.moments(imagem)

            hu_moments = cv2.HuMoments(momentos_centrais).flatten()

            texto = "\nMomentos de Hu:\n"
            for i, value in enumerate(hu_moments):
                texto += f'Hu[{i + 1}]: {value:.4e}\n'  # Usando notação científica

            self.text_edit.setPlainText(texto)
        else:
            print("Erro: A imagem não pôde ser convertida.")

    def qpixmap_to_numpy(self, pixmap):
        qimage = pixmap.toImage()
        width = qimage.width()
        height = qimage.height()

        ptr = qimage.bits()
        ptr.setsize(height * width)
        arr = np.array(ptr).reshape((height, width))

        return arr

class CropWindow(QWidget):

    def __init__(self, organ_images):
        super().__init__()
        self.view = QGraphicsView()
        self.scene = QGraphicsScene(self.view)
        self.view.setScene(self.scene)
        self.hi = 0
        self.initUI(organ_images)

    def initUI(self, organ_images):
        self.setWindowTitle("Recorte de Imagem")
        layout = QVBoxLayout()

        # Crie um layout horizontal para as imagens
        images_layout = QHBoxLayout()

        for organ, data in organ_images.items():
            pixmap = data["pixmap"]
            coords = data["coords"]

            pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(pixmap_item)

            image_layout = QVBoxLayout()
            image_label = QLabel(organ)
            image_label.setAlignment(Qt.AlignCenter)
            image_layout.addWidget(image_label)

            pixmap_view = QGraphicsView()
            pixmap_scene = QGraphicsScene()
            pixmap_scene.addItem(pixmap_item)
            pixmap_view.setScene(pixmap_scene)

            image_layout.addWidget(pixmap_view)

            images_layout.addLayout(image_layout)

        # Fígado com Hi ------------------------------------------------------------- #

        self.new_liver_pix_map = self.calculate_hi(organ_images)
        pixmap_item = QGraphicsPixmapItem(self.new_liver_pix_map)
        self.scene.addItem(pixmap_item)

        image_layout = QVBoxLayout()
        image_label = QLabel("Fígado com Hi")
        image_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(image_label)
        pixmap_view = QGraphicsView()
        pixmap_scene = QGraphicsScene()
        pixmap_scene.addItem(pixmap_item)
        pixmap_view.setScene(pixmap_scene)
        image_layout.addWidget(pixmap_view)
        images_layout.addLayout(image_layout)

        # ------------------------------------------------------------------------ #

        layout.addLayout(images_layout)
        layout.addWidget(self.view)
        self.setLayout(layout)
        self.show()

    def calculate_hi(self, organ_images):
        liver = self.calculate_avg(organ_images["fígado"]["pixmap"])
        kidney = self.calculate_avg(organ_images["rim"]["pixmap"])

        self.hi = liver / kidney
        image = organ_images["fígado"]["pixmap"].toImage()
        new_image = QImage(image.size(), QImage.Format_Grayscale8)

        for x in range(image.width()):
            for y in range(image.height()):
                pixel_value = image.pixelColor(x, y).red()
                new_value = min(int(pixel_value * self.hi), 255) # Tem que colocar esse limite, porque é 8bits de grayscale
                new_image.setPixel(x, y, QColor(new_value, new_value, new_value).rgba())
        return QPixmap.fromImage(new_image)

    def calculate_avg(self, pixmap):
        image = pixmap.toImage()
        num_pixels = image.width() * image.height()
        sum_of_pixels = 0

        for x in range(image.width()):
            for y in range(image.height()):
                pixel_value = image.pixelColor(x, y).red()
                sum_of_pixels += pixel_value

        return sum_of_pixels / num_pixels

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

        save_rois = QAction('Salvar ROIs', self)
        save_rois.triggered.connect(self.save_signal.emit)
        file_menu.addAction(save_rois)

        # Menu GLCM Descritores
        glcm_menu = self.addMenu('GLCM Descritores')
        glcm_action = QAction('Mostrar GLCM', self)
        glcm_action.triggered.connect(self.glcm_signal.emit)  # Emitindo sinal para GLCM
        glcm_menu.addAction(glcm_action)

        # Menu GLCM Descritores
        histograma_menu = self.addMenu('Histograma')
        histograma_action = QAction('Mostrar Histograma', self)
        histograma_action.triggered.connect(self.histograma_signal.emit)  # Emitindo sinal para GLCM
        histograma_menu.addAction(histograma_action)

        #Menu Momento de Hu
        momento_hu_menu = self.addMenu('Momentos Invariantes de Hu')
        momento_hu_action = QAction('Mostrar Dados',self)
        momento_hu_action.triggered.connect(self.momento_Hu_signal.emit)
        momento_hu_menu.addAction(momento_hu_action)


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


 #Histograma---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class Histogram(QWidget):
    def __init__(self, pixmap):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.canvas = FigureCanvas(Figure())
        self.layout.addWidget(self.canvas)

        self.ax = self.canvas.figure.subplots()

        self.compute_histogram(pixmap)

    def compute_histogram(self, pixmap):
        image = self.qpixmap_to_numpy(pixmap)

        hist = cv2.calcHist([image], [0], None, [256], [0,255])

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
class ImageViewer(QGraphicsView):
    cropped = pyqtSignal(QPixmap, int, int, int, int)

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setDragMode(QGraphicsView.NoDrag)

        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)

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

    def display_image(self, pixmap, name):
        self.pacient_n, self.image_n = map(str, name.split("-"))
        self.enable_cropping = True
        self.scene.clear()
        self.resetTransform()
        self.pix_map = pixmap
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(pixmap_item)

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
        # else:
        #     utility.MessageBox.show_alert("Selecao da ROI muito pequena.")
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


        self.folder_hierarchy.itemClicked.connect(self.display_image)
        self.folder_hierarchy.setHeaderHidden(True)

        self.cropped_imgs_node = QTreeWidgetItem(self.folder_hierarchy)
        self.cropped_imgs_node.setText(0, f"Coleção de Cortes")

        # ------------------------------------------------------------------------------------------- #

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
        self.display.emit(self.pixmap_dictionary[f"{item.text(1)}-{item.text(2)}"], f"{item.text(1)}-{item.text(2)}")
        self.has_selected_liver = False
        self.has_selected_cortex = False
        self.has_selected_kidney = False

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

    def create_image_from_cropped(self, crop_qpixmap, pacient_n, image_n, coord_x, coord_y):
        if pacient_n != self.pacient_id and image_n != self.image_id:
            self.organ_images = {}
            self.pacient_id = pacient_n
            self.image_id = image_n

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
            self.save_img(self.crop_window.get_new_liver_pix_map(), f"ROI_{pacient_n}_{image_n}", coords_liver, coords_kidney, pacient_n, self.crop_window.get_hi())
            # nao precisa das ROIs do rim
            # self.save_img(self.organ_images["rim"]["pixmap"], f"RIM_{pacient_n}_{image_n}", coord_x, coord_y, pacient_n)

    def save_img(self, crop_qpixmap, file_name, coords_liver, coords_kidney, pacient_n, hi):
        child_item = QTreeWidgetItem(self.cropped_imgs_node)
        child_item.setText(0, file_name)
        child_item.setText(1, f"C")
        child_item.setText(2, str(self.crop_id))
        child_item.setText(3, f"{coords_liver}")
        child_item.setText(4, f"{coords_kidney}")
        if pacient_n <= 16:
            child_item.setText(5, "saudável")
        else:
            child_item.setText(5, "esteatose")
        child_item.setText(6, f"{hi}")


        self.pixmap_dictionary[f"C-{self.crop_id}"] = crop_qpixmap
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
                print("-" * 30)

                writer.writerow([
                node.text(0),
                node.text(5),
                node.text(3),
                node.text(4),
                height,
                width,
                node.text(6),
                ])

def preparate_data_rois(path, images_liver):
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

def test_xgboost_cross_val(X, Y):
    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='mlogloss')
    print("Treinando o modelo com validação cruzada...")
    pacientes_indices = np.arange(55)
    grupos = np.repeat(pacientes_indices, 10)
    logo = LeaveOneGroupOut()
    
    scores = []
    for train_index, test_index in logo.split(X, Y, grupos):
        print(test_index)
        X_train, X_test = X[train_index], X[test_index]
        Y_train, Y_test = Y[train_index], Y[test_index]

        model.fit(X_train, Y_train)

        accuracy = model.score(X_test, Y_test)
        scores.append(accuracy)
        print(accuracy)

    print(f"Acurácia média (cross-validation): {np.mean(scores):.2f}")
    print(f"Desvio padrão (cross-validation): {np.std(scores):.2f}")

def test_inception_cross_val(X, Y):
    pacientes_indices = np.arange(55)
    grupos = np.repeat(pacientes_indices, 10)
    logo = LeaveOneGroupOut()

    model = InceptionV3(weights='imagenet')

    logo = LeaveOneGroupOut()
    accuracies = []

    X = resize_images(X)

    for train_idx, test_idx in logo.split(X, Y, grupos):
        # Dividir os dados em treino e teste
        X_train, X_test = X[train_idx], X[test_idx]
        Y_train, Y_test = Y[train_idx], Y[test_idx]

        # Pré-processamento das imagens
        train_datagen = ImageDataGenerator(preprocessing_function=preprocess_input)
        test_datagen = ImageDataGenerator(preprocessing_function=preprocess_input)

        train_generator = train_datagen.flow(X_train, Y_train, batch_size=32)
        test_generator = test_datagen.flow(X_test, Y_test, batch_size=32)

        # Treinar o modelo
        model.fit(train_generator, epochs=5, verbose=0)  # Ajuste o número de épocas

        # Avaliar o modelo
        accuracy = model.evaluate(test_generator, verbose=0)[1]
        accuracies.append(accuracy)

        print(f"Iteração concluída. Acurácia: {accuracy:.2f}")

    print(f"Acurácia média (cross-validation): {np.mean(scores):.2f}")
    print(f"Desvio padrão (cross-validation): {np.std(scores):.2f}")

#Obter Conjunto ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def obtain_steatosis_images():
    # Colocar a localização da pasta "liver" para ajudar na procura da pasta
    path_input_dir = Path("liver")
    path_data = path_input_dir / "dataset_liver_bmodes_steatosis_assessment_IJCARS.mat"
    data = scipy.io.loadmat(path_data)
    data.keys()
    data_array = data['data']
    return data_array['images'][0]

def resize_images(X):
    resized_images = []
    for image in X:
        # Reconstruir a imagem original (28x28)
        image = image.reshape(28, 28)
        # Redimensionar para 299x299
        image_resized = cv2.resize(image, (299, 299), interpolation=cv2.INTER_LINEAR)
        # Converter para 3 canais (repetir os valores para RGB)
        image_resized_rgb = np.stack([image_resized] * 3, axis=-1)
        resized_images.append(image_resized_rgb)
    return np.array(resized_images)

if __name__ == '__main__':
    imagens_liver = obtain_steatosis_images()

    X, Y = preparate_data_rois("./data_real.csv", imagens_liver)
    # test_results = test_xgboost_cross_val(X, Y)
    test_inception_cross_val(X, Y)
    app = QApplication(sys.argv)
    ex = ProcessadorDeImagens(imagens_liver)

    sys.exit(app.exec_())