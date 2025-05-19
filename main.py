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

pygame.init()
mixer.init()

def play_intro_music():
    """Play bird sounds in the intro scene."""
    mixer.music.load('birds.wav')       # replace with your bird sound file
    mixer.music.set_volume(0.5)
    mixer.music.play(-1, 0.0)

def play_temple_music():
    mixer.music.load('temple.wav')
    mixer.music.set_volume(0.5)
    mixer.music.play(-1, 0.0)

collect_sound = mixer.Sound('pick.mp3')

def play_collect_sound():
    collect_sound.play()

def change_music():
    mixer.music.stop()
    mixer.music.load('portal.mp3')
    mixer.music.play(-1, 0.0)

play_intro_music()

GL_TEXTURE_MAX_ANISOTROPY_EXT = 0x84FE

WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
BOUNDS = 10.0
PLAYER_SPEED = 0.2
MOUSE_SENSITIVITY = 0.1
PORTAL_OPEN_TIME = 20.0
TOTAL_TIME = 60.0
INITIAL_CEILING = 5.0
SLAB_THICKNESS = 0.5
PORTAL_SCORE_THRESHOLD = 50

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
texture_ids = {}
portal_music_played = False
scene_state = "intro"

def check_anisotropic_support():
    try:
        max_aniso = glGetFloatv(GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT)
        return max_aniso
    except:
        return 1.0

def load_texture(name, path):
    try:
        img = Image.open(path).transpose(Image.FLIP_TOP_BOTTOM)
        img_data = img.convert("RGBA").tobytes()
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        glGenerateMipmap(GL_TEXTURE_2D)
        maxAniso = check_anisotropic_support()
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT, int(maxAniso))
        texture_ids[name] = tex_id
    except Exception as e:
        print(f"Error loading texture {name}: {e}")

def change_scene(new_state):
    global scene_state, player_pos, yaw, pitch, start_time, score, objects, portal_music_played, game_won, game_over
    scene_state = new_state
    if new_state == "temple":
        mixer.music.stop()
        play_temple_music()
        player_pos[:] = [0.0, 0.0]
        yaw = 90.0
        pitch = 0.0
        start_time = time.time()
        score = 0
        objects[:] = [
            {'pos': [random.uniform(-BOUNDS + 1, BOUNDS - 1), random.uniform(-BOUNDS + 1, BOUNDS - 1)], 'collected': False}
            for _ in range(3)
        ]
        portal_music_played = False
        game_won = False
        game_over = False
    elif new_state == "intro":
        # tüm müziği durdur ve KUŞ SESİ oynat
        mixer.music.stop()
        play_intro_music()
        player_pos[:] = [0.0, 0.0]
        yaw = 90.0
        pitch = 0.0
        start_time = time.time()
        portal_music_played = False
        game_won = False
        game_over = False

def draw_skybox():
    glDisable(GL_LIGHTING)
    glDepthMask(GL_FALSE)
    glBindTexture(GL_TEXTURE_2D, texture_ids['sky'])
    size = 50.0
    glBegin(GL_QUADS)
    # Ön yüz
    glTexCoord2f(0.0, 0.0); glVertex3f(-size, -size, -size)
    glTexCoord2f(1.0, 0.0); glVertex3f( size, -size, -size)
    glTexCoord2f(1.0, 1.0); glVertex3f( size,  size, -size)
    glTexCoord2f(0.0, 1.0); glVertex3f(-size,  size, -size)
    # Arka yüz
    glTexCoord2f(0.0, 0.0); glVertex3f( size, -size,  size)
    glTexCoord2f(1.0, 0.0); glVertex3f(-size, -size,  size)
    glTexCoord2f(1.0, 1.0); glVertex3f(-size,  size,  size)
    glTexCoord2f(0.0, 1.0); glVertex3f( size,  size,  size)
    # Sol yüz
    glTexCoord2f(0.0, 0.0); glVertex3f(-size, -size,  size)
    glTexCoord2f(1.0, 0.0); glVertex3f(-size, -size, -size)
    glTexCoord2f(1.0, 1.0); glVertex3f(-size,  size, -size)
    glTexCoord2f(0.0, 1.0); glVertex3f(-size,  size,  size)
    # Sağ yüz
    glTexCoord2f(0.0, 0.0); glVertex3f( size, -size, -size)
    glTexCoord2f(1.0, 0.0); glVertex3f( size, -size,  size)
    glTexCoord2f(1.0, 1.0); glVertex3f( size,  size,  size)
    glTexCoord2f(0.0, 1.0); glVertex3f( size,  size, -size)
    # Üst yüz
    glTexCoord2f(0.0, 0.0); glVertex3f(-size,  size, -size)
    glTexCoord2f(1.0, 0.0); glVertex3f( size,  size, -size)
    glTexCoord2f(1.0, 1.0); glVertex3f( size,  size,  size)
    glTexCoord2f(0.0, 1.0); glVertex3f(-size,  size,  size)
    # Alt yüz
    glTexCoord2f(0.0, 0.0); glVertex3f(-size, -size,  size)
    glTexCoord2f(1.0, 0.0); glVertex3f( size, -size,  size)
    glTexCoord2f(1.0, 1.0); glVertex3f( size, -size, -size)
    glTexCoord2f(0.0, 1.0); glVertex3f(-size, -size, -size)
    glEnd()
    glDepthMask(GL_TRUE)
    glEnable(GL_LIGHTING)

def draw_intro_scene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    front = get_front_vector()
    cam_x, cam_y, cam_z = player_pos[0], player_eye_height, player_pos[1]
    gluLookAt(cam_x, cam_y, cam_z, cam_x + front[0], cam_y + front[1], cam_z + front[2], 0, 1, 0)
    draw_skybox()

    # Draw elevated platform with stone texture
    glBindTexture(GL_TEXTURE_2D, texture_ids['floor'])
    platform_height = 0.2
    platform_size = 2.5
    glBegin(GL_QUADS)
    # Top face
    glNormal3f(0, 1, 0)
    glTexCoord2f(0, 0); glVertex3f(-platform_size, -1 + platform_height, -platform_size)
    glTexCoord2f(4, 0); glVertex3f( platform_size, -1 + platform_height, -platform_size)
    glTexCoord2f(4, 4); glVertex3f( platform_size, -1 + platform_height,  platform_size)
    glTexCoord2f(0, 4); glVertex3f(-platform_size, -1 + platform_height,  platform_size)
    # Sides
    glNormal3f(0, 0, -1)
    glTexCoord2f(0, 0); glVertex3f(-platform_size, -1, -platform_size)
    glTexCoord2f(4, 0); glVertex3f( platform_size, -1, -platform_size)
    glTexCoord2f(4, 0.2); glVertex3f( platform_size, -1 + platform_height, -platform_size)
    glTexCoord2f(0, 0.2); glVertex3f(-platform_size, -1 + platform_height, -platform_size)
    glNormal3f(0, 0, 1)
    glTexCoord2f(0, 0); glVertex3f(-platform_size, -1, platform_size)
    glTexCoord2f(4, 0); glVertex3f( platform_size, -1, platform_size)
    glTexCoord2f(4, 0.2); glVertex3f( platform_size, -1 + platform_height, platform_size)
    glTexCoord2f(0, 0.2); glVertex3f(-platform_size, -1 + platform_height, platform_size)
    glNormal3f(-1, 0, 0)
    glTexCoord2f(0, 0); glVertex3f(-platform_size, -1, -platform_size)
    glTexCoord2f(4, 0); glVertex3f(-platform_size, -1, platform_size)
    glTexCoord2f(4, 0.2); glVertex3f(-platform_size, -1 + platform_height, platform_size)
    glTexCoord2f(0, 0.2); glVertex3f(-platform_size, -1 + platform_height, -platform_size)
    glNormal3f(1, 0, 0)
    glTexCoord2f(0, 0); glVertex3f(platform_size, -1, -platform_size)
    glTexCoord2f(4, 0); glVertex3f(platform_size, -1, platform_size)
    glTexCoord2f(4, 0.2); glVertex3f(platform_size, -1 + platform_height, platform_size)
    glTexCoord2f(0, 0.2); glVertex3f(platform_size, -1 + platform_height, -platform_size)
    glEnd()

    # Draw glowing rune-like markers around the platform
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBindTexture(GL_TEXTURE_2D, texture_ids['portal'])
    rune_size = 0.3
    for angle in [0, 90, 180, 270]:
        rad = math.radians(angle)
        x = 2.0 * math.cos(rad)
        z = 2.0 * math.sin(rad)
        pulse = abs(math.sin(time.time() * 2 + angle)) * 0.3 + 0.7
        glColor4f(0.2, 0.4, 1.0, pulse)
        glPushMatrix()
        glTranslatef(x, -1 + platform_height + 0.01, z)
        glRotatef(90, 1, 0, 0)  # Make runes lie flat
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-rune_size, -rune_size, 0)
        glTexCoord2f(1, 0); glVertex3f( rune_size, -rune_size, 0)
        glTexCoord2f(1, 1); glVertex3f( rune_size,  rune_size, 0)
        glTexCoord2f(0, 1); glVertex3f(-rune_size,  rune_size, 0)
        glEnd()
        glPopMatrix()

    # Draw larger portal with pulsing glow
    glBindTexture(GL_TEXTURE_2D, texture_ids['portal'])
    pulse = abs(math.sin(time.time() * 2)) * 0.3 + 0.7
    glColor4f(0.2, 0.4, 1.0, pulse)
    glPushMatrix()
    glTranslatef(0.0, -0.3, -1.8)  # Adjusted position for larger portal
    glutSolidTorus(0.15, 1.0, 16, 48)  # Larger outer radius and higher detail
    glPopMatrix()
    glDisable(GL_BLEND)

    # Check for portal interaction (adjusted for larger portal)
    dx = player_pos[0]
    dz = player_pos[1] + 1.8
    if dx*dx + dz*dz < 1.0**2:
        change_scene("temple")

    glutSwapBuffers()

def draw_ground():
    glBindTexture(GL_TEXTURE_2D, texture_ids['floor'])
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glTexCoord2f(0.0, 0.0); glVertex3f(-BOUNDS, -1, -BOUNDS)
    glTexCoord2f(BOUNDS, 0.0); glVertex3f( BOUNDS, -1, -BOUNDS)
    glTexCoord2f(BOUNDS, BOUNDS); glVertex3f( BOUNDS, -1,  BOUNDS)
    glTexCoord2f(0.0, BOUNDS); glVertex3f(-BOUNDS, -1,  BOUNDS)
    glEnd()

def draw_walls():
    glBindTexture(GL_TEXTURE_2D, texture_ids['wall'])
    height = INITIAL_CEILING
    for x in (-BOUNDS, BOUNDS):
        glBegin(GL_QUADS)
        glNormal3f(-1 if x > 0 else 1, 0, 0)
        glTexCoord2f(0.0, 0.0); glVertex3f(x, -1, -BOUNDS)
        glTexCoord2f(BOUNDS, 0.0); glVertex3f(x, -1, BOUNDS)
        glTexCoord2f(BOUNDS, height); glVertex3f(x, height, BOUNDS)
        glTexCoord2f(0.0, height); glVertex3f(x, height, -BOUNDS)
        glEnd()
    for z in (-BOUNDS, BOUNDS):
        glBegin(GL_QUADS)
        glNormal3f(0, 0, -1 if z > 0 else 1)
        glTexCoord2f(0.0, 0.0); glVertex3f(-BOUNDS, -1, z)
        glTexCoord2f(BOUNDS, 0.0); glVertex3f(BOUNDS, -1, z)
        glTexCoord2f(BOUNDS, height); glVertex3f(BOUNDS, height, z)
        glTexCoord2f(0.0, height); glVertex3f(-BOUNDS, height, z)
        glEnd()

def draw_columns():
    glColor3f(0.8, 0.8, 0.8)
    num_columns = 4
    radius = 0.3
    height = INITIAL_CEILING - 1
    for i in range(num_columns):
        angle = math.radians(360 * i / num_columns)
        x = BOUNDS * math.cos(angle)
        z = BOUNDS * math.sin(angle)
        glPushMatrix()
        glTranslatef(x, -height / 2, z)
        glRotatef(90, 1, 0, 0)
        draw_column(radius, height)
        glPopMatrix()

def draw_column(radius, height):
    slices = 32
    glBegin(GL_QUAD_STRIP)
    for i in range(slices + 1):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        glVertex3f(x, -height / 2, z)
        glVertex3f(x, height / 2, z)
    glEnd()
    glBegin(GL_POLYGON)
    for i in range(slices):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        glVertex3f(x, -height / 2, z)
    glEnd()
    glBegin(GL_POLYGON)
    for i in range(slices):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        glVertex3f(x, height / 2, z)
    glEnd()

def draw_ceiling():
    elapsed = time.time() - start_time
    y_top = INITIAL_CEILING - (elapsed / TOTAL_TIME) * (INITIAL_CEILING + SLAB_THICKNESS) * 1.5
    bottom_y = y_top - SLAB_THICKNESS
    glBindTexture(GL_TEXTURE_2D, texture_ids['ceiling'])
    glColor3f(1,1,1)
    glBegin(GL_QUADS)
    glNormal3f(0, -1, 0)
    glTexCoord2f(0.0, 0.0); glVertex3f(-BOUNDS, bottom_y, -BOUNDS)
    glTexCoord2f(1.0, 0.0); glVertex3f( BOUNDS, bottom_y, -BOUNDS)
    glTexCoord2f(1.0, 1.0); glVertex3f( BOUNDS, bottom_y,  BOUNDS)
    glTexCoord2f(0.0, 1.0); glVertex3f(-BOUNDS, bottom_y,  BOUNDS)
    glEnd()
    return bottom_y

def draw_objects():
    glColor3f(1, 0.84, 0)
    for obj in objects:
        if not obj['collected']:
            glPushMatrix()
            glTranslatef(obj['pos'][0], -0.7, obj['pos'][1])
            glutSolidSphere(0.2, 16, 16)
            glPopMatrix()

def draw_portal():
    global portal_music_played
    elapsed = time.time() - start_time
    if elapsed >= PORTAL_OPEN_TIME and score >= PORTAL_SCORE_THRESHOLD:
        if not portal_music_played:
            change_music()
            portal_music_played = True
        pulse = abs(math.sin(elapsed * 2)) * 0.5 + 0.5
        glColor4f(0.2, 0.4, 1.0, pulse)
        glPushMatrix()
        glTranslatef(portal_pos[0], -0.5, portal_pos[1])
        glBindTexture(GL_TEXTURE_2D, texture_ids['portal'])
        glutSolidTorus(0.1, 1.0, 12, 36)
        glPopMatrix()
        return True
    return False

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

def draw_text(x, y, text):
    glWindowPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

def check_collisions():
    global score, game_won
    if scene_state != "temple":
        return
    for obj in objects:
        if not obj['collected']:
            dx = player_pos[0] - obj['pos'][0]
            dz = player_pos[1] - obj['pos'][1]
            if dx*dx + dz*dz < 0.5:
                obj['collected'] = True
                play_collect_sound()
                score += 10
                objects.append({
                    'pos': [random.uniform(-BOUNDS + 1, BOUNDS - 1),
                            random.uniform(-BOUNDS + 1, BOUNDS - 1)],
                    'collected': False
                })
    for i in range(4):
        angle = math.radians(360 * i / 4)
        x = BOUNDS * math.cos(angle)
        z = BOUNDS * math.sin(angle)
        if (player_pos[0] - x)**2 + (player_pos[1] - z)**2 < (0.3)**2:
            return
    elapsed = time.time() - start_time
    if elapsed >= PORTAL_OPEN_TIME and score >= PORTAL_SCORE_THRESHOLD:
        dx = player_pos[0] - portal_pos[0]
        dz = player_pos[1] - portal_pos[1]
        if dx*dx + dz*dz < 1.0:
            game_won = True

def keyboard(key, x, y):
    global game_won, game_over
    if game_won or game_over:
        sys.exit()
    if key in (b'\x1b', b'q'):
        sys.exit()
    step = PLAYER_SPEED
    front = get_front_vector()
    right = [front[2], 0, -front[0]]
    if key == b'w':
        player_pos[0] += front[0]*step
        player_pos[1] += front[2]*step
    elif key == b's':
        player_pos[0] -= front[0]*step
        player_pos[1] -= front[2]*step
    elif key == b'd':
        player_pos[0] -= right[0]*step
        player_pos[1] -= right[2]*step
    elif key == b'a':
        player_pos[0] += right[0]*step
        player_pos[1] += right[2]*step
    if scene_state == "temple":
        limit = BOUNDS - 0.5
    else:
        limit = 2
    player_pos[0] = max(-limit, min(limit, player_pos[0]))
    player_pos[1] = max(-limit, min(limit, player_pos[1]))
    check_collisions()

def init():
    global start_time, objects
    glEnable(GL_DEPTH_TEST)
    glDisable(GL_CULL_FACE)
    glEnable(GL_TEXTURE_2D)
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
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    load_texture('portal', 'portal.png')
    load_texture('floor',  'floor.png')
    load_texture('wall',   'wall.png')
    load_texture('ceiling','ceil.png')
    load_texture('sky',    'sky.png')
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glutSetCursor(GLUT_CURSOR_NONE)
    start_time = time.time()
    objects[:] = [
        {'pos': [random.uniform(-BOUNDS + 1, BOUNDS - 1),
                 random.uniform(-BOUNDS + 1, BOUNDS - 1)],
         'collected': False}
        for _ in range(3)
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

def get_front_vector():
    fx = math.cos(math.radians(yaw)) * math.cos(math.radians(pitch))
    fy = math.sin(math.radians(pitch))
    fz = math.sin(math.radians(yaw)) * math.cos(math.radians(pitch))
    length = math.sqrt(fx*fx + fy*fy + fz*fz)
    return [fx/length, fy/length, fz/length]

def mouse_motion(x, y):
    global yaw, pitch, lastX, lastY, first_mouse
    if first_mouse:
        lastX, lastY = x, y
        first_mouse = False
    xoffset = (x - lastX) * MOUSE_SENSITIVITY
    yoffset = (lastY - y) * MOUSE_SENSITIVITY
    lastX, lastY = WINDOW_WIDTH/2, WINDOW_HEIGHT/2
    yaw += xoffset
    pitch += yoffset
    pitch = max(-89, min(89, pitch))
    glutWarpPointer(int(lastX), int(lastY))

def idle():
    glutPostRedisplay()

def display():
    global game_won, game_over
    if scene_state == "intro":
        draw_intro_scene()
        return
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
        game_over = True
        draw_game_over()
        return
    draw_ground()
    draw_walls()
    draw_columns()
    y_ceiling = draw_ceiling()
    draw_objects()
    portal_active = draw_portal()
    if y_ceiling <= player_eye_height + 0.2:
        game_over = True
        draw_game_over()
        return
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
    if game_won:
        change_scene("intro")
    elif game_over:
        draw_game_over()

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
