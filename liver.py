import sys
from pathlib import Path
from skimage.feature import graycomatrix
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt
import scipy.io
from include import utility, toolbar, image_viewer, menubar, crop_window, histogram
import matplotlib.pyplot as plt
import numpy as np

class ImageProcessor(QMainWindow):
    def __init__(self, images = None):
        super().__init__()
        self.image_viewer = image_viewer.ImageViewer()
        self.toolbar_images = toolbar.ToolBarImages(images)
        self.menubar = menubar.MenuBar()
        self.addToolBar(Qt.LeftToolBarArea, self.toolbar_images)
        self.image_viewer.cropped.connect(self.toolbar_images.create_image_from_cropped) # Comunicacao ImageViewer -> ToolbarImage

        self.toolbar_images.display.connect(self.image_viewer.display_image) # Comunicacao ToolbarImage -> ImageViewer
        self.toolbar_images.display.connect(self.show_histogram) # Comunicacao ToolbarImage -> ImageViewer
        self.toolbar_images.display.connect(self.calculate_coocorenciaRadiais)

        self.menubar.add_image.connect(self.toolbar_images.display_image) # Comunicacao ImageViewer -> ToolbarImages
        self.menubar.crop_signal.connect(self.open_crop_window) # Comunicacao MenuBar -> QMainWindow

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Processing Application (IPA)')
        # Tamanho minimo da tela != Tamanho maximo da image_viewer
        self.setMenuBar(self.menubar)
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)
        self.setCentralWidget(self.image_viewer)
        self.show()
    
    def show_histogram(self):
        current_pixmap = self.image_viewer.get_pixmap()
        if current_pixmap:
            self.histogram = histogram.Histogram(current_pixmap)
            self.histogram.show()

   
    #Interface GLCM Radios
    def GLCMVisualizer(self, image):
        self.image = image
        self.distances = [1, 2, 4, 8]
        self.angles = [0, np.pi/4, np.pi/2, 3*np.pi/4]
        self.angle_labels = ['0°', '45°', '90°', '135°']
        self.current_page = 0

        self.total_pages = len(self.distances)

        self.fig, self.axs = plt.subplots(2, 2, figsize=(10, 8))
        self.update_plots()
          
        plt.subplots_adjust(bottom=0.2)
        self.prev_button = plt.Button(plt.axes([0.1, 0.05, 0.1, 0.075]), 'Anterior')
        self.next_button = plt.Button(plt.axes([0.3, 0.05, 0.1, 0.075]), 'Próximo')

        self.prev_button.on_clicked(self.previous_page)
        self.next_button.on_clicked(self.next_page)
        plt.show()

    def update_plots(self):
        for ax in self.axs.flatten():
            ax.clear() 

        # Obtém a distância atual
        distance = self.distances[self.current_page]

        for a_idx, angle in enumerate(self.angles):
            glcm = graycomatrix(self.image, distances=[distance], angles=[angle], normed=True)
            ax = self.axs.flatten()[a_idx]
            ax.imshow(glcm[:, :, 0, 0], cmap='gray')
            ax.set_title(f'Distância {distance}, Ângulo {self.angle_labels[a_idx]}')
            ax.axis('off')

        plt.suptitle(f'GLCM para Distância {distance}')
        plt.draw()

    def next_page(self, event):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_plots()

    def previous_page(self, event):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_plots()       
    
    def calculate_coocorenciaRadiais(self):
     current_pixmap = self.image_viewer.get_pixmap()
     image = self.histogram.qpixmap_to_numpy(current_pixmap)
     visualizer = self.GLCMVisualizer(image)

    #FIM Interface GLCM Radios


    def open_crop_window(self):
        current_pixmap = self.image_viewer.get_pixmap()
        if current_pixmap:
            self.crop_window = crop_window.CropWindow(current_pixmap)
            self.crop_window.show()

def get_images_dataset():
    #Colocar a localização da pasta "liver" para ajudar na procura da pasta
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