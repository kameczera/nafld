import numpy as np
import mahotas
from skimage import io, color

# Carrega a imagem e converte para escala de cinza, caso necessário
image = io.imread('"C:/Users/andre/Desktop/a.png"')
gray_image = color.rgb2gray(image)

# Calcula a GLCM e os descritores de Haralick
haralick_features = mahotas.features.haralick(gray_image)

# As features retornadas estão em uma matriz, onde cada linha é uma direção da GLCM
# e cada coluna é um descritor diferente.
# Por exemplo, para pegar a média dos descritores em todas as direções:
mean_haralick = haralick_features.mean(axis=0)

print("Descritores de Haralick (média por direção):")
print(mean_haralick)