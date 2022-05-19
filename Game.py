import sys

import pygame as pg
import numpy as np
from numba import njit
from button import Button

pg.init()

def main(): # Organizando a estrutura do jogo em Main para melhor manutenção!
    pg.display.set_caption("Labirinto da UNIP!")
    font = pg.font.SysFont("Lucida Sans", 70)

    stepdelay = pg.time.get_ticks() / 200 #O metodo é chamado uma vez por frame designado como 60, então essa variavel irá criar um delay entre passos para reprodução do som.
    click, clickdelay = 0, stepdelay

    screen = pg.display.set_mode((800, 600))
    running = True # Vai fazer o jogo ficar rodando até o while acabar.

    clock = pg.time.Clock() # É usado para fazer o movimento independente do tempo

    pg.mouse.set_visible(False)

    #Resolução
    hres = 200  # Horizontal
    halfvres = 150  # Vertical

    mod = hres / 60  # Campo de visão

    size = 25 #Tamanho da matriz do mapa
    posx, posy, rot, maph, mapc, exitx, exity = gen_map(size) # Criando um mapa aleatório com um implemento de escape

    frame = np.random.uniform(0, 1, (hres, halfvres * 2, 3)) # É oque vai renderizar a resolução e a iluminação com o RayCasting

    # Dando textura
    ceu = pg.image.load('Assets/ceu.jpg') # Arquivos das imagens divididos pelo RGB de cores, 255.
    ceu = pg.surfarray.array3d(pg.transform.scale(ceu, (360, halfvres * 2))) / 255
    chao = pg.surfarray.array3d(pg.image.load('Assets/chao.jpg')) / 255 #Imagens
    parede = pg.surfarray.array3d(pg.image.load('Assets/parede.jpg')) / 255 #Imagens

    stepcounts = posx + posy #Mostrando onde ele tá para fazer a contagem de passos

    # Loop enquanto o jogo roda
    while running:
        ticks = pg.time.get_ticks() / 200
        if int(posx) == exitx and int(posy) == exity: #Isso faz o jogo fechar caso você consiga escapar
            print("Saiu do Labirinto!")
            running = False
            screen = pg.display.set_mode((1280, 720))

            pg.mouse.set_visible(True) #Mouse volta a aparecer

            winnerSound = pg.mixer.Sound('Assets/Sounds/win.wav') #Som de vitória
            winnerSound.play()
            options() #Joga pra tela das opções que seria um fim também

        for event in pg.event.get():
            if event.type == pg.QUIT or event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                running = False

                screen = pg.display.set_mode((1280, 720))


        frame = new_frame(posx, posy, rot, frame, ceu, chao, hres, halfvres, mod, maph, size,
                          parede, mapc, exitx, exity) # Chamando o Numba, biblioteca que tem melhor perfomance sobre o Python e o PyGame.

        surf = pg.surfarray.make_surface(frame * 255)
        surf = pg.transform.scale(surf, (800, 600))

        step = pg.mixer.Sound('Assets/Sounds/playerstep.mp3')
        if ticks - stepdelay > 2 and stepcounts != posx + posy: #Função para ele tocar um som a cada passo definido pela pos da variavel
            step.play()
            stepdelay = ticks
        stepcounts = posx + posy #Isso aqui precisa para o som não quebrar e ficar tocando sem parar e vários ao mesmo tempo

        # Exibindo a taxa de Quadros
        fps = int(clock.get_fps())
        pg.display.set_caption("Labirinto da UNIP em PyGame - FPS: " + str(fps))

        screen.blit(surf, (0, 0))
        pg.display.update()

        posx, posy, rot = movimentacao(pg.key.get_pressed(), posx, posy, rot, maph, clock.tick() / 500)
        pg.mouse.set_pos(400, 300)

def movimentacao(pressed_keys, posx, posy, rot, maph, et): #Função do movimento e viro de tela

    x, y, rot0, diag = posx, posy, rot, 0


    #Virar a câmera pros lados
    if pressed_keys[pg.K_LEFT]:
        et = et / (diag + 1)
        rot = rot + np.clip((0.001 - 400) / 200, -0.065, 0.3)
    if pressed_keys[pg.K_RIGHT]:
        et = et / (diag + 1)
        rot = rot - np.clip((0.001 - 400) / 200, -0.065, 0.3)


    # Tentiva de implementar o mouse, mas não tem Offset e está mt travado
    if pg.mouse.get_focused():
        p_mouse = pg.mouse.get_pos()
        rot = rot + np.clip((p_mouse[0] - 400) / 200, -0.2, 0.3)


    # Para a Frente e para Trás
    if pressed_keys[pg.K_UP] or pressed_keys[ord('w')]:
        x, y, diag = x + et * np.cos(rot), y + et * np.sin(rot), 1

    elif pressed_keys[pg.K_DOWN] or pressed_keys[ord('s')]:
        x, y, diag = x - et * np.cos(rot), y - et * np.sin(rot), 1

    # Para Esquerda e Para Direita
    if pressed_keys[ord('a')]:
        et = et / (diag + 1)
        x, y = x + et * np.sin(rot), y - et * np.cos(rot)

    elif pressed_keys[ord('d')]:
        et = et / (diag + 1)
        x, y = x - et * np.sin(rot), y + et * np.cos(rot)

    if not (maph[int(x - 0.2)][int(y)] or maph[int(x + 0.2)][int(y)] or
            maph[int(x)][int(y - 0.2)] or maph[int(x)][int(y + 0.2)]):
        posx, posy = x, y

    elif not (maph[int(posx - 0.2)][int(y)] or maph[int(posx + 0.2)][int(y)] or
              maph[int(posx)][int(y - 0.2)] or maph[int(posx)][int(y + 0.2)]):
        posy = y

    elif not (maph[int(x - 0.2)][int(posy)] or maph[int(x + 0.2)][int(posy)] or
              maph[int(x)][int(posy - 0.2)] or maph[int(x)][int(posy + 0.2)]):
        posx = x

    return posx, posy, rot


def gen_map(size):  # Algoritmo que vai gerar um mapa diferente cada vez que abre, usando matrizes e as texturas criadas.
    mapc = np.random.uniform(0, 1, (size, size, 3))
    maph = np.random.choice([0, 0, 0, 0, 1, 1], (size, size))
    maph[0, :], maph[size - 1, :], maph[:, 0], maph[:, size - 1] = (1, 1, 1, 1)

    posx, posy, rot = 1.5, np.random.randint(1, size - 1) + .5, np.pi / 4
    x, y = int(posx), int(posy)
    maph[x][y] = 0
    count = 0

    while True:                     # Algoritmo de teste pra ver quando o Jogador vai ganhar chegando no objetivo.
        testx, testy = (x, y)
        if np.random.uniform() > 0.5:
            testx = testx + np.random.choice([-1, 1])
        else:
            testy = testy + np.random.choice([-1, 1])
        if testx > 0 and testx < size - 1 and testy > 0 and testy < size - 1:
            if maph[testx][testy] == 0 or count > 5:
                count = 0
                x, y = (testx, testy)
                maph[x][y] = 0
                if x == size - 2:
                    exitx, exity = (x, y)
                    break
            else:
                count = count + 1
    return posx, posy, rot, maph, mapc, exitx, exity


@njit() # Função da biblioteca do Numba
def new_frame(posx, posy, rot, frame, sky, floor, hres, halfvres, mod, maph, size, wall, mapc, exitx, exity): #Essa função serve pra melhorar a performance com Numba
    for i in range(hres): # Loop da Visão
        rot_i = rot + np.deg2rad(i / mod - 30) # Calculando o Seno e Cosseno dos Angulos da visão
        sin, cos, cos2 = np.sin(rot_i), np.cos(rot_i), np.cos(np.deg2rad(i / mod - 30)) # Calculo de Distância até o Jogador pra mostrar os objetos e correção do Olho de Peixe
        frame[i][:] = sky[int(np.rad2deg(rot_i) % 359)][:]

        x, y = posx, posy
        while maph[int(x) % (size - 1)][int(y) % (size - 1)] == 0: # Raycasting que vai seguindo até encontrar uma parede
            x, y = x + 0.01 * cos, y + 0.01 * sin

        n = abs((x - posx) / cos) #Quanto o raio andou na direção X pelo cosseno
        h = int(halfvres / (n * cos2 + 0.001))  # Calcular a altura & Correção do olho de peixe e não ter divisão por 0

        xx = int(x * 3 % 1 * 99) # Calculando as coords da textura

        if x % 1 < 0.02 or x % 1 > 0.98: # Se o valor de X ficar proximo do inteiro, ele usa o Y para textura horizontal
            xx = int(y * 3 % 1 * 99) # Calculando as coords da textura
        yy = np.linspace(0, 3, h * 2) * 99 % 99

        shade = 0.3 + 0.7 * (h / halfvres) #Valor do sombreamento, sem ficar muito distante.

        if shade > 1: # Arrumar o rompimento do limite da altura com a quebra de cores com o sombreamento
            shade = 1 # Limite de valor no sombreamento

        ash = 0
        if maph[int(x - 0.33) % (size - 1)][int(y - 0.33) % (size - 1)]:
            ash = 1

        if maph[int(x - 0.01) % (size - 1)][int(y - 0.01) % (size - 1)]: # Testando a iluminação para ver se entra na parede
            shade, ash = shade * 0.5, 0 # Caso ocorra vai escurer o efeito de Shading naquela área

        c = shade * mapc[int(x) % (size - 1)][int(y) % (size - 1)]

        for k in range(h * 2): # Preenche os pixels com a cor da parede, mas fica cinza
            if halfvres - h + k >= 0 and halfvres - h + k < 2 * halfvres:
                if ash and 1 - k / (2 * h) < 1 - xx / 99: # Comparação da altura do Pixel com a coordenada X da textura
                    c, ash = 0.5 * c, 0
                frame[i][halfvres - h + k] = c * wall[xx][int(yy[k])]
                if halfvres + 3 * h - k < halfvres * 2: # Validando a coordenada do reflexo pra não sair pra fora do frame
                    frame[i][halfvres + 3 * h - k] = c * wall[xx][int(yy[k])]

        for j in range(halfvres - h): # Distâncias inversamente proporcionais
            n = (halfvres / (halfvres - j)) / cos2
            x, y = posx + cos * n, posy + sin * n
            xx, yy = int(x * 2 % 1 * 99), int(y * 2 % 1 * 99)

            shade = 0.2 + 0.8 * (1 - j / halfvres)

            if maph[int(x - 0.33) % (size - 1)][int(y - 0.33) % (size - 1)]: # Testando pro chão, vendo suas coordenadas perto da parede com offset maior.
                shade = shade * 0.5
            elif ((maph[int(x - 0.33) % (size - 1)][int(y) % (size - 1)] and y % 1 > x % 1) or # Teste do Offset de X, vê se ela é maior que Y
                  (maph[int(x) % (size - 1)][int(y - 0.33) % (size - 1)] and x % 1 > y % 1)): # Teste do Offset de Y, vice versa
                shade = shade * 0.5

            frame[i][halfvres * 2 - j - 1] = shade * (floor[xx][yy] + frame[i][halfvres * 2 - j - 1]) / 2 #Algoritmo da saída
            if int(x) == exitx and int(y) == exity and (x % 1 - 0.5) ** 2 + (y % 1 - 0.5) ** 2 < 0.2:
                ee = j / (10 * halfvres)
                frame[i][j:2 * halfvres - j] = (ee * np.ones(3) + frame[i][j:2 * halfvres - j]) / (1 + ee)

    return frame

SCREEN = pg.display.set_mode((1280, 720))
pg.display.set_caption("Menu do Jogo")

BG = pg.image.load("assets/Background.png")
ABOUT = pg.image.load("assets/Sobre.png")

def get_font(size):  # Tamanho da fonte para os offsets de botões
    return pg.font.Font("assets/font.ttf", size)


def play():
    while True:
        PLAY_MOUSE_POS = pg.mouse.get_pos()

        SCREEN.fill("black")

        PLAY_TEXT = get_font(25).render("Tela de Jogo.", True, "White")
        PLAY_RECT = PLAY_TEXT.get_rect(center=(640, 260))
        SCREEN.blit(PLAY_TEXT, PLAY_RECT)

        PLAY_BACK = Button(image=None, pos=(640, 460),
                           text_input="BACK", font=get_font(75), base_color="White", hovering_color="Green")

        PLAY_BACK.changeColor(PLAY_MOUSE_POS)
        PLAY_BACK.update(SCREEN)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEBUTTONDOWN:
                click = pg.mixer.Sound('Assets/Sounds/click.wav')
                click.play()
                if PLAY_BACK.checkForInput(PLAY_MOUSE_POS):
                    main_menu()

        pg.display.update()


def options():
    while True:
        OPTIONS_MOUSE_POS = pg.mouse.get_pos()

        SCREEN.fill("white")
        SCREEN.blit(ABOUT, (0, 0))

        OPTIONS_TEXT = get_font(25).render("", True, "Black")
        OPTIONS_RECT = OPTIONS_TEXT.get_rect(center=(640, 260))
        SCREEN.blit(OPTIONS_TEXT, OPTIONS_RECT)

        OPTIONS_BACK = Button(image=None, pos=(640, 460),
                              text_input="BACK", font=get_font(75), base_color="Black", hovering_color="Red")

        OPTIONS_BACK.changeColor(OPTIONS_MOUSE_POS)
        OPTIONS_BACK.update(SCREEN)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEBUTTONDOWN:
                click = pg.mixer.Sound('Assets/Sounds/click.wav')
                click.play()
                if OPTIONS_BACK.checkForInput(OPTIONS_MOUSE_POS):
                    main_menu()

        pg.display.update()


def main_menu():
    while True:
        SCREEN.blit(BG, (0, 0))

        #menuMusic = pg.mixer.Sound('Assets/Sounds/menuMusic.wav')
        #menuMusic.play()
        #menuMusic.set_volume(0.1)

        pg.mouse.set_visible(True)

        MENU_MOUSE_POS = pg.mouse.get_pos()

        MENU_TEXT = get_font(80).render("", True, "#b68f40")
        MENU_RECT = MENU_TEXT.get_rect(center=(640, 100))

        PLAY_BUTTON = Button(image=pg.image.load("assets/buttonBg.png"), pos=(640, 250),
                             text_input="JOGAR", font=get_font(55), base_color="#FFFFFF", hovering_color="Red")
        OPTIONS_BUTTON = Button(image=pg.image.load("assets/buttonBg.png"), pos=(640, 400),
                                text_input="SOBRE", font=get_font(60), base_color="#FFFFFF", hovering_color="Red")
        QUIT_BUTTON = Button(image=pg.image.load("assets/buttonBg.png"), pos=(640, 550),
                             text_input="SAIR", font=get_font(55), base_color="#FFFFFF", hovering_color="Red")

        SCREEN.blit(MENU_TEXT, MENU_RECT)

        for button in [PLAY_BUTTON, OPTIONS_BUTTON, QUIT_BUTTON]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(SCREEN)

        for event in pg.event.get():

            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEBUTTONDOWN:
                click = pg.mixer.Sound('Assets/Sounds/click.wav')
                click.play()
                if PLAY_BUTTON.checkForInput(MENU_MOUSE_POS):
                    main()
                if OPTIONS_BUTTON.checkForInput(MENU_MOUSE_POS):
                    options()
                if QUIT_BUTTON.checkForInput(MENU_MOUSE_POS):
                    pg.quit()
                    sys.exit()

        pg.display.update()

if __name__ == '__main__':
    main_menu()
    pg.quit()
