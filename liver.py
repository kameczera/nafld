import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt
import scipy.io
from include import utility, toolbar, image_viewer, menubar, crop_window

class ImageProcessor(QMainWindow):
    def __init__(self, images = None):
        super().__init__()
        self.image_viewer = image_viewer.ImageViewer()
        self.toolbar_images = toolbar.ToolBarImages(images)
        self.menubar = menubar.MenuBar()
        self.addToolBar(Qt.LeftToolBarArea, self.toolbar_images)
        self.image_viewer.cropped.connect(self.toolbar_images.create_image_from_cropped) # Comunicacao ImageViewer -> ToolbarImage
        self.toolbar_images.display.connect(self.image_viewer.display_image) # Comunicacao ToolbarImage -> ImageViewer
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