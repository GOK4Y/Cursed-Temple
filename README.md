# Cursed-Temple
Verilen proje senaryolarından 10. senaryo yapılmıştır.

# Kütüphanelerin-Kurulumları
Aşağıda verilen kütüphanelerin kurulumu için terminalde "pip install ...." ya da "pip3 install ...." yazılması gerekir.
import sys
import time
import random
import math
from PIL import Image
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import pygame
from pygame import mixer


# Oynanış
- Oyundaki karakter W,A,S,D tuşları ve mouse hareketi ile kontrol edilmektedir.
- Oyun açık bir alanda bulunan bir portalın önünde başlamaktadır. Portala girince tapınağa ışınlanılır.
- Tapınaktayken ekranın sol üst köşesinde skor ve kalan süre yazmaktadır.
- Tapınağın içinde toplanabilir objeler bulunmaktadır. Her bir obje toplandığında skora 10 puan eklenir.
- Kalan süre boyunca tapınağın tavanı çökmektedir. Süre bitene kadar obje toplanması istenir.
- 40.saniyede kaçış portalı açılır. Portala girildiğinde oyuna başlanılan alana geri dönülür.
- İsteğe bağlı olarak oyundan çıkmadan istediğiniz kere skor denemesi yapabilirsiniz.
