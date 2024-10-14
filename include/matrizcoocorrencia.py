import matplotlib.pyplot as plt
from skimage import io, color
from skimage.feature import graycomatrix
from include import utility, toolbar, image_viewer, menubar, crop_window, histogram
import numpy as np

class MatrizCoocorrencia:
     
   def __init__(self, pixmap):
      super().__init__()
      self.calculate_matrizCoocorencia(pixmap)
      self.calculate_coocorenciaRadiais(pixmap)
      
      


   def calculate_matrizCoocorencia(self,pixmap):
    image = histogram.Histogram.qpixmap_to_numpy(pixmap) #Utilizando a função para converter a imagem em matriz
    #imagem,distancia de pixel adjacente,angulo(n me lembro de termos mexido com angulo),levels = quantização da imagem,symmetric(se é simetrico a matriz),normed(normalizar a matriz, no qual a soma da probabilidade tem que ser = 1)
    glcm = graycomatrix(image,distances=[1],angles=[0],levels=4,symmetric=False,normed=True)

   def calculate_coocorenciaRadiais (self,pixmap):
 
    image = histogram.Histogram.qpixmap_to_numpy(pixmap) #Utilizando a função para converter a imagem em matriz
    glcm = graycomatrix(image,distances=[1],angles=[0,np.pi/4, np.pi/2, 3*np.pi/4])
    plt.imshow(glcm[:, :, 0, 0], cmap='gray')
    plt.title('GLCM para ângulo 0 radianos')
    plt.colorbar()
    plt.show()

  
    