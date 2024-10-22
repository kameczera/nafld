# Integrante 01: André Fellipe Carvalho Silveira
# Integrante 02: Leonardo Kamei Yukio

import sys
from pathlib import Path
from skimage.feature import graycomatrix, graycoprops
from scipy.stats import entropy
from PyQt5.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QVBoxLayout, QRubberBand, QApplication, QMainWindow,QAction, QFileDialog, QMenuBar,QToolBar, QTreeWidget, QTreeWidgetItem, QMessageBox
from PyQt5.QtGui import QPixmap, QColor,QPainter,QImage,QWheelEvent,QMouseEvent
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QRect, QSize
import scipy.io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import cv2

class ProcessadorDeImagens(QMainWindow):
    def __init__(self, imagens=None):
        super().__init__()
        self.visualizador_imagem = ImageViewer()
        self.toolbar_imagens = ToolBarImages(imagens)
        self.menubar = MenuBar()
        self.addToolBar(Qt.LeftToolBarArea, self.toolbar_imagens)

        self.visualizador_imagem.cropped.connect(self.toolbar_imagens.create_image_from_cropped)  # Comunicação ImageViewer -> ToolBarImage

        self.toolbar_imagens.display.connect(self.visualizador_imagem.display_image)  # Comunicação ToolBarImage -> ImageViewer
        #self.toolbar_imagens.display.connect(self.mostrar_histograma)  # Comunicação ToolBarImage -> ImageViewer
        #self.toolbar_imagens.display.connect(self.calcular_coocorenciaRadiais)

        self.menubar.add_image.connect(self.toolbar_imagens.display_image)  # Comunicação ImageViewer -> ToolBarImages
        self.menubar.crop_signal.connect(self.abrir_janela_crop)  # Comunicação MenuBar -> QMainWindow
        self.menubar.glcm_signal.connect(self.calcular_coocorenciaRadiais)
        self.menubar.histograma_signal.connect(self.mostrar_histograma)
        self.menubar.save_signal.connect(self.toolbar_imagens.save_all_crops)

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
            self.histograma = Histogram(pixmap_atual)
            self.histograma.show()

    # Interface GLCM Raízes -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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

#Corte das Imagens
class CropWindow(QWidget):
    cropped = pyqtSignal(int, QPixmap)
    
    def __init__(self, pixmap):
        super().__init__()
        self.view = QGraphicsView()
        self.scene = QGraphicsScene(self.view)
        self.view.setScene(self.scene)
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(pixmap_item)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self.view)  # Corrigido para usar self.view
        self.current_rect = QRect()
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
            self.origin = self.view.mapToScene(event.pos()).toPoint()
            self.rubber_band.setGeometry(self.current_rect)
            self.rubber_band.show()

    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            current_pos = self.view.mapToScene(event.pos()).toPoint()
            self.current_rect = QRect(self.origin, current_pos)
            self.current_rect = self.current_rect.normalized()  # Ajusta para evitar retângulos invertidos
            self.rubber_band.setGeometry(self.current_rect)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rubber_band.hide()
            rubber_band_rect = self.rubber_band.geometry()

            if rubber_band_rect.width() > 1 and rubber_band_rect.height() > 1:
                # Mapeia a área selecionada para a cena
                scene_rect = self.view.mapToScene(rubber_band_rect).boundingRect()
                pixmap_item = self.scene.items()[0]
                original_pixmap = pixmap_item.pixmap()

                # Recorta a imagem com base na área selecionada
                cropped_pixmap = original_pixmap.copy(scene_rect.toRect())
                self.cropped.emit(self.count_cropped, cropped_pixmap)
                self.count_cropped += 1
         
#Menu Bar -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class MenuBar(QMenuBar):
    add_image = pyqtSignal(str, QPixmap)
    crop_signal = pyqtSignal()
    glcm_signal = pyqtSignal() 
    histograma_signal = pyqtSignal()
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
    cropped = pyqtSignal(int, QPixmap, int, int, int, int)

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
        self.crop_n = 0

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
            self.cropped.emit(self.crop_n, cropped_pixmap, int(self.pacient_n), int(self.image_n), int(rubber_band_rect.x()), int(rubber_band_rect.y()))
            self.crop_n += 1
    # ------------------------------------------------------------------------------------------- #

    def click_near_border(self, pos):
        band_rect = self.rubber_band.geometry()

        margin = 5 # Margem de detecção de proximidade de borda (Mudar caso necessário)

        # Rosa dos ventos (Leste, Norte, Oeste, Sul - 1, 2, 3, 4) simplesmente para deixar o código mais eficiente, se tiver muito ilegível mudar
        if (abs(pos.x() - band_rect.right()) < margin): return 1 
        elif (abs(pos.y() - band_rect.top()) < margin): return 2
        elif (abs(pos.x() - band_rect.left()) < margin): return 3
        elif (abs(pos.y() - band_rect.bottom()) < margin): return 4
        
        return -1
    


# Classe ToolBarImages: Classe que mostra as imagens adicionadas pelo botao load, "croppadas" e do dataset Liver -----------------------------------------------------------------------------------------------------------
class ToolBarImages(QToolBar):
    display = pyqtSignal(QPixmap, str)
    

    def __init__(self, images = None):
        super().__init__("All Images")
        self.images = images

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
    
    def create_image_from_cropped(self, id_crop, crop_qpixmap, pacient_n, image_n, coord_x, coord_y):
        child_item = QTreeWidgetItem(self.cropped_imgs_node)
        child_item.setText(0, f"ROI_{pacient_n}_{image_n}")
        child_item.setText(1, f"C")
        child_item.setText(2, str(id_crop))
        child_item.setText(3, f"{coord_x},{coord_y}")

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText("Informe o órgao dessa imagem")
        msg.setWindowTitle("Recorte")
        
        button_liver = msg.addButton("Fígado", QMessageBox.liver)
        button_cortex = msg.addButton("Cortex Renal", QMessageBox.cortex)
        button_kidney = msg.addButton("Rim", QMessageBox.kidney)

        msg.exec_()

        if msg.clickedButton() == button_liver:
            child_item.setText(4, f"liver")
        elif msg.clickedButton() == button_cortex:
            child_item.setText(4, f"cortex")
        elif msg.clickedButton() == button_kidney:
            child_item.setText(4, f"kidney")

        self.pixmap_dictionary[f"C-{id_crop}"] = crop_qpixmap
    
    def save_all_crops(self):
        for i in range(self.cropped_imgs_node):
            node = self.cropped_imgs_node.child(i)
            pixmap = self.pixmap_dictionary[f"{node.text(1)}-{node.text(2)}"]
            
            pixmap_item = QGraphicsPixmapItem(pixmap)
    
            bounding_rect = pixmap_item.boundingRect()
            
            height = pixmap.height()
            width = pixmap.width()
            
            print(f"Imagem: {key}")
            print(f"Canto superior esquerdo: ({coord_x},{coord_y})")
            print(f"Altura: {height}, Comprimento: {width}")
            print("-" * 30)

#Obter Conjunto ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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
