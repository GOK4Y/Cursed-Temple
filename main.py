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
import time

# Pygame'i başlatıyoruz
pygame.init()

# Ses mixer'ı başlatıyoruz
mixer.init()

# Müzik çalma fonksiyonu
def play_music():
    mixer.music.load('temple.wav')
    mixer.music.set_volume(0.5)  # Ses seviyesini ayarla
    mixer.music.play(-1, 0.0)  # Sonsuz döngüde çalsın

# Ses efekti çalma fonksiyonu
collect_sound = mixer.Sound('pick.mp3')

def play_collect_sound():
    collect_sound.play()  # Ses efektini çal

# Müzik değiştirme fonksiyonu
def change_music():
    mixer.music.stop()  # Eski müziği durdur
    mixer.music.load('portal.mp3')  # Yeni müziği yükle
    mixer.music.play(-1, 0.0)  # Yeni müziği çalmaya başla

# Oyun başladığında müziği başlat
play_music()

# Top toplama durumu için örnek kontrol

# Portal açıldığında müzik değiştirme örneği



# GL_TEXTURE_MAX_ANISOTROPY_EXT sabitini manuel olarak tanımlıyoruz
GL_TEXTURE_MAX_ANISOTROPY_EXT = 0x84FE  # Anizotropik filtreleme için kullanılan sabit

# Global ayarlar
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
BOUNDS = 10.0
PLAYER_SPEED = 0.2
MOUSE_SENSITIVITY = 0.1
PORTAL_OPEN_TIME = 20.0
TOTAL_TIME = 60.0
INITIAL_CEILING = 5.0
SLAB_THICKNESS = 0.5
PORTAL_SCORE_THRESHOLD = 50

# Oyuncu ve oyun durumu
player_pos = [0.0, 0.0]
player_eye_height = 0.0
yaw, pitch = 90.0, 0.0
lastX, lastY = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
first_mouse = True
score = 0
start_time = None
game_won = False
game_over = False
objects = []
portal_pos = [0.0, -3.0]

# Texture id'lerini tutacak dict
texture_ids = {}

# Anizotropik filtreleme destekleniyor mu kontrolü
def check_anisotropic_support():
    try:
        max_aniso = glGetFloatv(GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT)
        print(f"Anisotropic filtering is supported, max anisotropy: {max_aniso}")
        return max_aniso
    except:
        print("Anisotropic filtering not supported.")
        return 1.0  # Geriye düşülen bir varsayılan değeri

def load_texture(name, path):
    try:
        img = Image.open(path).transpose(Image.FLIP_TOP_BOTTOM)  # Görseli yükle
        img_data = img.convert("RGBA").tobytes()  # Görsel verisini al
        tex_id = glGenTextures(1)  # Yeni bir texture id'si oluştur
        glBindTexture(GL_TEXTURE_2D, tex_id)  # Texture'ı bağla
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)  # Mipmapping ve filtreleme
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)  # Texture'ı yükle

        # Mipmap oluştur
        glGenerateMipmap(GL_TEXTURE_2D)

        # Anizotropik filtreleme
        maxAniso = check_anisotropic_support()
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT, int(maxAniso))

        texture_ids[name] = tex_id  # Texture'ı kaydet
        print(f"Texture {name} loaded successfully.")
    except Exception as e:
        print(f"Error loading texture {name}: {e}")



def init():
    global start_time, objects
    glEnable(GL_DEPTH_TEST)
    glDisable(GL_CULL_FACE)
    glEnable(GL_TEXTURE_2D)

    # Işıklandırma ayarları
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    ambient = [0.4, 0.4, 0.4, 1.0]
    diffuse = [0.7, 0.7, 0.7, 1.0]
    specular = [0.2, 0.2, 0.2, 1.0]
    position = [0.0, 5.0, 0.0, 1.0]
    glLightfv(GL_LIGHT0, GL_AMBIENT, ambient)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse)
    glLightfv(GL_LIGHT0, GL_SPECULAR, specular)
    glLightfv(GL_LIGHT0, GL_POSITION, position)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)

    # Şeffaflık ayarları
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # Şeffaflık için doğru blend fonksiyonu

    # Dokuları yükle
    load_texture('portal', 'portal.png')
    load_texture('floor',  'floor.png')
    load_texture('wall',   'wall.png')
    load_texture('ceiling','ceil.png')

    glClearColor(0.1, 0.1, 0.1, 1.0)
    glutSetCursor(GLUT_CURSOR_NONE)
    start_time = time.time()

    # Başlangıçta 3 top spawn ediyoruz
    objects[:] = [
        {'pos': [random.uniform(-BOUNDS + 1, BOUNDS - 1),
                 random.uniform(-BOUNDS + 1, BOUNDS - 1)],
         'collected': False}
        for _ in range(3)  # 3 top spawn ediliyor
    ]


def reshape(w, h):
    global lastX, lastY
    glViewport(0, 0, w, h if h > 0 else 1)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, w / h, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    lastX, lastY = w / 2, h / 2
    glutWarpPointer(int(lastX), int(lastY))

def draw_ground():
    glBindTexture(GL_TEXTURE_2D, texture_ids['floor'])
    repeats = BOUNDS
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glTexCoord2f(0.0, 0.0);         glVertex3f(-BOUNDS, -1, -BOUNDS)
    glTexCoord2f(repeats, 0.0);     glVertex3f( BOUNDS, -1, -BOUNDS)
    glTexCoord2f(repeats, repeats); glVertex3f( BOUNDS, -1,  BOUNDS)
    glTexCoord2f(0.0, repeats);     glVertex3f(-BOUNDS, -1,  BOUNDS)
    glEnd()

def draw_columns():
    glColor3f(0.8, 0.8, 0.8)  # Kolon rengi (gri)
    num_columns = 4  # Kolon sayısı (örneğin 4 kolon)
    radius = 0.3  # Kolon çapı
    height = INITIAL_CEILING - 1  # Kolon yüksekliği (tavandan biraz aşağıda başlayacak)

    # Kolonları yerleştiriyoruz
    for i in range(num_columns):
        angle = math.radians(360 * i / num_columns)  # Kolonların yerleşim açısı
        x = BOUNDS * math.cos(angle)  # Kolonun X koordinatı
        z = BOUNDS * math.sin(angle)  # Kolonun Z koordinatı

        # Kolon çizimi (dikey olarak tavana doğru)
        glPushMatrix()
        glTranslatef(x, -height / 2, z)  # Kolonları yerleştirme (tavandan başlayacak)
        glRotatef(90, 1, 0, 0)  # Kolonları doğru açıda döndürme (dikey olacak)

        # Kolonu çizen fonksiyon
        draw_column(radius, height)  # Kolon çizimi fonksiyonunu çağırıyoruz

        glPopMatrix()

def draw_column(radius, height):
    # Silindirik şekli çizmek için GL_QUAD_STRIP kullanıyoruz
    slices = 32  # Silindirin kesirli dilim sayısı
    glBegin(GL_QUAD_STRIP)
    for i in range(slices + 1):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        # Alt ve üst dairesel kenarları çiz
        glVertex3f(x, -height / 2, z)  # Alt yüzey
        glVertex3f(x, height / 2, z)   # Üst yüzey
    glEnd()

    # Kolonun tabanını çizebiliriz (alt yüzey)
    glBegin(GL_POLYGON)
    for i in range(slices):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        glVertex3f(x, -height / 2, z)
    glEnd()

    # Kolonun üst yüzeyini çizebiliriz
    glBegin(GL_POLYGON)
    for i in range(slices):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        glVertex3f(x, height / 2, z)
    glEnd()




def draw_walls():
    glBindTexture(GL_TEXTURE_2D, texture_ids['wall'])
    glColor3f(1,1,1)
    height = INITIAL_CEILING
    repeats = BOUNDS
    # Sol & sağ
    for x in (-BOUNDS, BOUNDS):
        glBegin(GL_QUADS)
        glNormal3f(-1 if x>0 else 1,0,0)
        glTexCoord2f(0.0,        0.0);        glVertex3f(x,      -1,      -BOUNDS)
        glTexCoord2f(repeats,    0.0);        glVertex3f(x,       -1,       BOUNDS)
        glTexCoord2f(repeats,    height+1.0); glVertex3f(x,       height,   BOUNDS)
        glTexCoord2f(0.0,        height+1.0); glVertex3f(x,       height,  -BOUNDS)
        glEnd()
    # Ön & arka
    for z in (-BOUNDS, BOUNDS):
        glBegin(GL_QUADS)
        glNormal3f(0,0,-1 if z>0 else 1)
        glTexCoord2f(0.0,        0.0);        glVertex3f(-BOUNDS, -1,      z)
        glTexCoord2f(repeats,    0.0);        glVertex3f(BOUNDS,  -1,      z)
        glTexCoord2f(repeats,    height+1.0); glVertex3f(BOUNDS,   height,  z)
        glTexCoord2f(0.0,        height+1.0); glVertex3f(-BOUNDS,  height,  z)
        glEnd()

def draw_ceiling():
    elapsed = time.time() - start_time
    # y_top: tavandaki üst yüzey
    y_top = INITIAL_CEILING - (elapsed / TOTAL_TIME) * (INITIAL_CEILING + SLAB_THICKNESS) * 1.5
    bottom_y = y_top - SLAB_THICKNESS

    # Tek seferlik tavan dokusu
    glBindTexture(GL_TEXTURE_2D, texture_ids['ceiling'])
    glColor3f(1,1,1)
    glBegin(GL_QUADS)
    glNormal3f(0, -1, 0)  # tavandaki alt yüzey için normal
    glTexCoord2f(0.0, 0.0); glVertex3f(-BOUNDS, bottom_y, -BOUNDS)
    glTexCoord2f(1.0, 0.0); glVertex3f( BOUNDS, bottom_y, -BOUNDS)
    glTexCoord2f(1.0, 1.0); glVertex3f( BOUNDS, bottom_y,  BOUNDS)
    glTexCoord2f(0.0, 1.0); glVertex3f(-BOUNDS, bottom_y,  BOUNDS)
    glEnd()

    return bottom_y

def draw_objects():
    glColor3f(1, 0.84, 0)
    for obj in objects:
        if not obj['collected']:  # Eğer top toplanmamışsa
            glPushMatrix()
            glTranslatef(obj['pos'][0], -0.7, obj['pos'][1])
            glutSolidSphere(0.2, 16, 16)
            glPopMatrix()


# Müziğin yalnızca bir kez çalmasını sağlamak için bir flag ekliyoruz
portal_music_played = False

def draw_portal():
    global portal_music_played
    elapsed = time.time() - start_time

    # Portal açılma zamanı geldiğinde müziği çalmaya başlat
    if elapsed >= PORTAL_OPEN_TIME and score >= PORTAL_SCORE_THRESHOLD:
        if not portal_music_played:  # Eğer müzik daha önce çalmadıysa
            change_music()  # Müzik değişimini gerçekleştir
            portal_music_played = True  # Müzik çaldı, bir daha çalmasın

        # Portalın ışık efektini çizer
        pulse = abs(math.sin(elapsed * 2)) * 0.5 + 0.5
        glColor4f(0.2, 0.4, 1.0, pulse)  # Portalın ışık efekti
        glPushMatrix()
        glTranslatef(portal_pos[0], -0.5, portal_pos[1])  # Portalın konumlandırılması
        glBindTexture(GL_TEXTURE_2D, texture_ids['portal'])  # Portal görselini kullanıyoruz
        glutSolidTorus(0.1, 1.0, 12, 36)  # Portalın şeklini çizer
        glPopMatrix()
        return True

    return False




def draw_text(x, y, text):
    glWindowPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

def draw_win():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glClearColor(0.0, 1.0, 0.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1, 1, 1)
    msg = f"Tebrikler, tapınaktan kaçtın ! Skor: {score}"
    draw_text(WINDOW_WIDTH // 2 - len(msg) * 9 // 2, WINDOW_HEIGHT // 2, msg)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glutSwapBuffers()

def draw_game_over():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glClearColor(0.4, 0.0, 0.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1, 1, 1)
    msg = "Olamaz! Tavan çöktü, ezildin!"
    draw_text(WINDOW_WIDTH // 2 - len(msg) * 9 // 2, WINDOW_HEIGHT // 2, msg)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glutSwapBuffers()

def get_front_vector():
    fx = math.cos(math.radians(yaw)) * math.cos(math.radians(pitch))
    fy = math.sin(math.radians(pitch))
    fz = math.sin(math.radians(yaw)) * math.cos(math.radians(pitch))
    length = math.sqrt(fx*fx + fy*fy + fz*fz)
    return [fx/length, fy/length, fz/length]

def display():
    global game_won, game_over
    if game_won:
        draw_win(); return
    if game_over:
        draw_game_over(); return

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    front = get_front_vector()
    cam_x, cam_y, cam_z = player_pos[0], player_eye_height, player_pos[1]
    gluLookAt(cam_x, cam_y, cam_z,
              cam_x + front[0], cam_y + front[1], cam_z + front[2],
              0, 1, 0)

    elapsed = time.time() - start_time
    remaining = max(0, TOTAL_TIME - elapsed)
    if remaining <= 0:
        game_over = True; return

    draw_ground()
    draw_walls()
    draw_columns()  # Kolonları ekliyoruz
    y_ceiling = draw_ceiling()
    draw_objects()
    portal_active = draw_portal()

    if y_ceiling <= player_eye_height + (0.2) :
        game_over = True; return

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1,1,1)
    info = f"Score: {score}   Time: {int(remaining)}s   (Portal için {PORTAL_SCORE_THRESHOLD} puan)"
    draw_text(10, WINDOW_HEIGHT - 30, info)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glutSwapBuffers()



def keyboard(key, x, y):
    global game_won, game_over
    if game_won or game_over:
        sys.exit()
    step = PLAYER_SPEED
    front = get_front_vector()
    right = [front[2], 0, -front[0]]
    if key in (b'\x1b', b'q'):
        sys.exit()
    if key == b'w':
        player_pos[0] += front[0]*step; player_pos[1] += front[2]*step
    elif key == b's':
        player_pos[0] -= front[0]*step; player_pos[1] -= front[2]*step
    elif key == b'd':
        player_pos[0] -= right[0]*step; player_pos[1] -= right[2]*step
    elif key == b'a':
        player_pos[0] += right[0]*step; player_pos[1] += right[2]*step
    player_pos[0] = max(-BOUNDS+0.5, min(BOUNDS-0.5, player_pos[0]))
    player_pos[1] = max(-BOUNDS+0.5, min(BOUNDS-0.5, player_pos[1]))
    check_collisions()

def mouse_motion(x, y):
    global yaw, pitch, lastX, lastY, first_mouse
    if first_mouse:
        lastX, lastY = x, y
        first_mouse = False
    xoffset = (x - lastX) * MOUSE_SENSITIVITY
    yoffset = (lastY - y) * MOUSE_SENSITIVITY
    lastX, lastY = WINDOW_WIDTH/2, WINDOW_HEIGHT/2
    yaw += xoffset; pitch += yoffset
    pitch = max(-89, min(89, pitch))
    glutWarpPointer(int(lastX), int(lastY))

def check_collisions():
    global score, game_won
    for obj in objects:
        if not obj['collected']:
            dx = player_pos[0] - obj['pos'][0]
            dz = player_pos[1] - obj['pos'][1]
            if dx*dx + dz*dz < 0.5:  # Topu toplama mesafesi
                obj['collected'] = True
                play_collect_sound()

                score += 10
                # Yeni bir top spawn ediliyor
                objects.append({
                    'pos': [random.uniform(-BOUNDS + 1, BOUNDS - 1),
                            random.uniform(-BOUNDS + 1, BOUNDS - 1)],
                    'collected': False
                })

    # Kolonlarla çarpışma kontrolü
    for i in range(4):  # 4 kolon yerleştirildi
        angle = math.radians(360 * i / 4)  # Kolonların pozisyon açısı
        x = BOUNDS * math.cos(angle)
        z = BOUNDS * math.sin(angle)

        # Kolon etrafında çarpışma kontrolü
        if (player_pos[0] - x)**2 + (player_pos[1] - z)**2 < (0.3)**2:  # Kolonun etrafındaki mesafe
            print("Çarpışma: Kolona çarptınız!")
            # Eğer çarptıysa, oyuncunun hareketini kısıtlayabiliriz
            # Örneğin, hareket etmesini engelleyebiliriz
            return  # Çarpışma olduğunda işlem durduruluyor

    # Portal açma koşulunun kontrolü
    elapsed = time.time() - start_time
    if elapsed >= PORTAL_OPEN_TIME and score >= PORTAL_SCORE_THRESHOLD:
        dx = player_pos[0] - portal_pos[0]
        dz = player_pos[1] - portal_pos[1]
        if dx*dx + dz*dz < 1.0:
            game_won = True


def idle():
    glutPostRedisplay()

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"Cursed Temple FPV Crush")
    init()
    glutReshapeFunc(reshape)
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutPassiveMotionFunc(mouse_motion)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()