import pygame
import random
import sys
import os
import datetime


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    return image


white = (255, 255, 255)
very_light_gray = (192, 192, 192)
black = (0, 0, 0)

light_gray = (144, 144, 144)
aqua = (0, 92, 180)

cell_size = 30
left_m = 40
upper_m = 50

size = (left_m + 30 * cell_size, upper_m + 15 * cell_size)

pygame.init()

screen = pygame.display.set_mode(size)
pygame.display.set_caption('Морской бой')

pygame.mixer.music.load('data/music.mp3')
pygame.mixer.music.set_volume(0.05)
pygame.mixer.music.play(-1)

font_size = int(cell_size / 1.25)
font = pygame.font.SysFont('arial', font_size)

# Переменная, которая следит за порядком игры. False - ходит человек, True - ПК
turn = False


class Board:
    def __init__(self, width, height, left, top, playername):
        self.name = playername

        self.cell_size = cell_size
        self.height = height
        self.width = width
        self.left = left
        self.top = top

        self.letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']

        # Сет с координатами кораблей
        self.ships = set()

        # Списки клеток, в которые мы уже стреляли(разные, в зависимости от того был ли корабль в этой клетке)
        self.shooted_cells = []
        self.shooted_ships = []

        # Матрица поля. 0 - пустая клетка, 1 - клетка с кораблем,
        # 2 - клетка, подстреленная клетка без корабля, 3 - подстреленная с кораблем
        self.field = [[0 for i in range(self.width)][:] for j in range(self.height)]

        # Доступные клетки для расстановки кораблей
        self.avalible_cells = set((i, j) for i in range(1, 11) for j in range(1, 11))

        # Доступные клетки для выстрела ПК
        self.avalible_cells_for_shoot = list((i, j) for i in range(1, 11) for j in range(1, 11))
        self.around_last_shoot = []

    def create_random_ship(self, length):
        # Генерируем случайное направление (положение корабля) 0 - горизонатльное, 1 - вертикальное
        location = random.randint(0, 1)

        # Так же нужно сгенерировать, в какую сторону дальше расширять корабль.
        # (1 - вправо или вниз, -1 - влево или вверх) в зависимости от направления
        direction = random.choice((-1, 1))

        # Генерируем случайную клетку из свободных, в которой будет расположен корабль
        pos = list(random.choice(tuple(self.avalible_cells)))
        # Далее генерация самого корабля.
        ship_coords = [pos[:]]

        for i in range(length - 1):
            if location:
                pos[0] += direction
                if pos[0] < 1:
                    ship_coords.append([ship_coords[0][0] - pos[0] + 1, pos[1]])
                elif pos[0] > 10:
                    ship_coords.append([ship_coords[0][0] - pos[0] % 10, pos[1]])
                else:
                    ship_coords.append([pos[0], pos[1]])
            else:
                pos[1] += direction
                if pos[1] < 1:
                    ship_coords.append([pos[0], ship_coords[0][1] - pos[1] + 1])
                elif pos[1] > 10:
                    ship_coords.append([pos[0], ship_coords[0][1] - pos[1] % 10])
                else:
                    ship_coords.append([pos[0], pos[1]])
        ship_coords = [tuple(i) for i in ship_coords]
        if all([i in self.avalible_cells for i in ship_coords]):
            return sorted(ship_coords)
        else:
            return self.create_random_ship(length)

    def add_ship(self, ship_coords):
        self.ships.add(tuple(ship_coords))
        for i in ship_coords:
            self.field[i[1] - 1][i[0] - 1] = 1
        for i in range(ship_coords[0][0] - 1, ship_coords[-1][0] + 2):
            for j in range(ship_coords[0][1] - 1, ship_coords[-1][1] + 2):
                if (i, j) in self.avalible_cells:
                    self.avalible_cells.remove((i, j))

    def generate_pc_field(self):
        for i in range(4):
            self.add_ship(self.create_random_ship(1))
        for i in range(3):
            self.add_ship(self.create_random_ship(2))
        for i in range(2):
            self.add_ship(self.create_random_ship(3))
        for i in range(1):
            self.add_ship(self.create_random_ship(4))
        # for i in range(10):
        #     print(self.field[i])
        # print(self.ships)
        # print(self.avalible_cells)

    # Прорисовка поля
    def render(self, screen):
        all_sprites = pygame.sprite.Group()
        sprite = pygame.sprite.Sprite()
        sprite.image = load_image("sea.jpg")
        sprite.rect = sprite.image.get_rect()
        sprite.rect.x = self.left
        sprite.rect.y = upper_m
        all_sprites.add(sprite)
        all_sprites.draw(screen)
        for y in range(self.height):
            for x in range(self.width):
                pygame.draw.rect(screen, pygame.Color(black), (
                    x * self.cell_size + self.left, y * self.cell_size + self.top, self.cell_size,
                    self.cell_size), 1)
                number = font.render(str(y + 1), True, black)

                # Отрисовка цифр
                number_width = number.get_width()
                number_height = number.get_height()

                screen.blit(number, (self.left - (cell_size + number_width) // 2,
                                     upper_m + y * self.cell_size + (self.cell_size - number_height) // 2))

        # Отрисовка букв
        for x in range(self.width):
            letter = font.render(self.letters[x], True, black)

            letters_width = letter.get_width()
            letters_height = letter.get_height()

            screen.blit(letter, (self.left + cell_size * x + (cell_size - letters_width) // 2,
                                  upper_m + self.height * self.cell_size + (self.cell_size - letters_height) // 2))

        # Подпись поля
        text = font.render(self.name, True, black)
        text_width = text.get_width()
        screen.blit(text, (self.left + self.cell_size * self.width // 2 - text_width // 2,
                           self.top - self.cell_size // 2 - text.get_height() // 2))

        # Рисуем подстреленные корабли
        for elem in self.shooted_ships:
            pygame.draw.line(screen, pygame.Color(black), ((elem[0] - 1) * self.cell_size + self.left,
                                                           (elem[1] - 1) * self.cell_size + self.top),
                             (elem[0] * self.cell_size + self.left,
                              elem[1] * self.cell_size + self.top), 3)
            pygame.draw.line(screen, pygame.Color(black), (elem[0] * self.cell_size + self.left,
                                                           (elem[1] - 1) * self.cell_size + self.top),
                             ((elem[0] - 1) * self.cell_size + self.left,
                              elem[1] * self.cell_size + self.top), 3)

        # Рисуем подстреленные клетки
        for elem in self.shooted_cells:
            pygame.draw.ellipse(screen, pygame.Color(black), ((elem[0] - 1) * self.cell_size + self.left + self.cell_size / 3,
                                                          (elem[1] - 1) * self.cell_size + self.top + self.cell_size / 3,
                                                          self.cell_size / 3, self.cell_size / 3), 5)

    def set_view(self, left, top, cell_size):
        self.left = left
        self.top = top
        self.cell_size = cell_size

    def on_click(self, cell):
        if self.field[cell[1] - 1][cell[0] - 1] == 0:
            if cell in self.avalible_cells_for_shoot:
                self.avalible_cells_for_shoot.remove(cell)
            if cell in self.around_last_shoot:
                self.around_last_shoot.remove(cell)
            global turn
            turn = not turn
            self.field[cell[1] - 1][cell[0] - 1] = 2
            self.shooted_cells.append(cell)
        elif self.field[cell[1] - 1][cell[0] - 1] == 1:
            if cell in self.avalible_cells_for_shoot:
                self.avalible_cells_for_shoot.remove(cell)
            if cell in self.around_last_shoot:
                self.around_last_shoot.remove(cell)
            self.field[cell[1] - 1][cell[0] - 1] = 3
            self.shooted_ships.append(cell)
        for i in self.ships:
            for j in i:
                if j == cell:
                    f = True
                    ship = sorted(i)
                    for el in ship:
                        if el not in self.shooted_ships:
                            f = False
                            break
                    if f:
                        for x in range(ship[0][0] - 1, ship[-1][0] + 2):
                            for y in range(ship[0][1] - 1, ship[-1][1] + 2):
                                if (x, y) in self.avalible_cells_for_shoot:
                                    self.shooted_cells.append((x, y))
                                    self.avalible_cells_for_shoot.remove((x, y))
                        self.around_last_shoot.clear()
                    break

    def get_cell(self, mouse_pos):
        cell_x = (mouse_pos[0] - self.left) // self.cell_size + 1
        cell_y = (mouse_pos[1] - self.top) // self.cell_size + 1
        if cell_x <= 0 or cell_x > self.width or cell_y <= 0 or cell_y > self.height:
            return None
        return cell_x, cell_y

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        if cell:
            self.on_click(cell)
        else:
            pass

    def draw_ships(self, screen):
        for i in self.ships:
            i = list(i)
            flg = True
            for elem in i:
                if elem not in self.shooted_ships:
                    flg = False
            if flg or self.name == 'Вы:':
                pygame.draw.rect(screen, pygame.Color(black), (
                    (i[0][0] - 1) * self.cell_size + self.left,
                    (i[0][1] - 1) * self.cell_size + self.top,
                    self.cell_size * (i[-1][0] - i[0][0] + 1),
                    self.cell_size * (i[-1][1] - i[0][1] + 1)), 3)

    def shoot_choice(self):
        pygame.time.delay(random.randint(1000, 1500))
        aval = self.avalible_cells_for_shoot
        if not self.around_last_shoot:
            cell = random.choice(aval)
        else:
            cell = random.choice(self.around_last_shoot)
        for i in cell:
            if i < 1 or i > 10:
                if cell in self.avalible_cells_for_shoot:
                    self.avalible_cells_for_shoot.remove(cell)
                if cell in self.around_last_shoot:
                    self.around_last_shoot.remove(cell)
                self.shoot_choice()
        self.on_click(cell)
        if self.field[cell[1] - 1][cell[0] - 1] == 3:
            if not self.around_last_shoot:
                if (cell[0] - 1, cell[1]) not in self.shooted_ships and (
                        cell[0] - 1, cell[1]) not in self.shooted_cells\
                        and 0 < cell[1] - 1 < 11:
                    self.around_last_shoot.append((cell[0] - 1, cell[1]))
                if (cell[0] + 1, cell[1]) not in self.shooted_ships and (
                        cell[0] + 1, cell[1]) not in self.shooted_cells\
                        and 0 < cell[0] + 1 < 11:
                    self.around_last_shoot.append((cell[0] + 1, cell[1]))
                if (cell[0], cell[1] - 1) not in self.shooted_ships and (
                        cell[0], cell[1] - 1) not in self.shooted_cells\
                        and 0 < cell[1] - 1 < 11:
                    self.around_last_shoot.append((cell[0], cell[1] - 1))
                if (cell[0], cell[1] + 1) not in self.shooted_ships and (
                        cell[0], cell[1] + 1) not in self.shooted_cells\
                        and 0 < cell[1] + 1 < 11:
                    self.around_last_shoot.append((cell[0], cell[1] + 1))
            else:
                if (cell[0] - 1, cell[1]) not in self.shooted_ships and (
                        cell[0] - 1, cell[1]) not in self.shooted_cells\
                        and 0 < cell[1] - 1 < 11:
                    self.around_last_shoot.append((cell[0] - 1, cell[1]))
                if (cell[0] + 1, cell[1]) not in self.shooted_ships and (
                        cell[0] + 1, cell[1]) not in self.shooted_cells\
                        and 0 < cell[0] + 1 < 11:
                    self.around_last_shoot.append((cell[0] + 1, cell[1]))
                if (cell[0], cell[1] - 1) not in self.shooted_ships and (
                        cell[0], cell[1] - 1) not in self.shooted_cells\
                        and 0 < cell[1] - 1 < 11:
                    self.around_last_shoot.append((cell[0], cell[1] - 1))
                if (cell[0], cell[1] + 1) not in self.shooted_ships and (
                        cell[0], cell[1] + 1) not in self.shooted_cells\
                        and 0 < cell[1] + 1 < 11:
                    self.around_last_shoot.append((cell[0], cell[1] + 1))
            hor_friends = []
            # False -> корабль расположен вертикально
            flg_hor = False
            if 0 < cell[0] + 1 < 11:
                hor_friends.append((cell[0] + 1, cell[1]))
            if 0 < cell[0] - 1 < 11:
                hor_friends.append((cell[0] - 1, cell[1]))
            for i in hor_friends:
                if self.field[i[1] - 1][i[0] - 1] == 3 or self.field[i[1] - 1][i[0] - 1] == 1:
                    flg_hor = True
            if flg_hor is True:
                copy = self.around_last_shoot[:]
                for elem in copy:
                    if elem[1] != cell[1]:
                        self.around_last_shoot.remove(elem)
            else:
                copy = self.around_last_shoot[:]
                for elem in copy:
                    if elem[0] != cell[0]:
                        self.around_last_shoot.remove(elem)


class Button:
    def __init__(self, left_margin, title, msg, scr):
        self.color = light_gray
        self.screen = scr
        self.title = title
        self.text_width, self.text_height = font.size(self.title)

        self.message = msg

        self.left_margin = left_margin
        self.upper_margin = self.text_height + cell_size * 11 + upper_m

        self.button_width = self.text_width + cell_size
        self.button_height = self.text_height + cell_size

        self.rect = pygame.Rect((self.left_margin, self.upper_margin, self.button_width, self.button_height))

        self.rect_for_text = self.left_margin + self.button_width / 2 - self.text_width / 2, \
                             self.upper_margin + self.button_height / 2 - self.text_height / 2

    def change_upper_m(self, upper_mar):
        self.upper_margin = upper_mar

    def draw_button(self, color=None):
        if color is None:
            color = self.color
        pygame.draw.rect(self.screen, color, (self.left_margin, self.upper_margin, self.button_width, self.button_height))
        self.screen.blit(font.render(self.title, True, white), self.rect_for_text)
        self.draw_text()

    def change_color(self, col=aqua):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            self.draw_button(color=col)

    def draw_text(self):
        if self.message:
            msg_width, msg_height = font.size(self.message)
            msg_rect = self.left_margin // 2 - msg_width // 2 ,\
                       self.upper_margin + self.button_height // 2 - msg_height // 2
            text = font.render(self.message, True, black)
            screen.blit(text, msg_rect)

    def clicked(self, pos):
        if self.rect.collidepoint(pos):
            return True
        return False


class Ball(pygame.sprite.Sprite):
    def __init__(self, radius, x, y):
        super().__init__(all_sprites)
        self.radius = radius
        self.radius = radius
        self.image = pygame.Surface((2 * radius, 2 * radius), pygame.SRCALPHA, 32)
        pygame.draw.circle(self.image, pygame.Color("red"), (radius, radius), radius)
        self.rect = pygame.Rect(x, y, 2 * radius, 2 * radius)
        self.vx = random.randint(-5, 5)
        self.vy = random.randrange(-5, 5)

    def update(self):
        self.rect = self.rect.move(self.vx, self.vy)
        if pygame.sprite.spritecollideany(self, horizontal_borders):
            self.vy = -self.vy
        if pygame.sprite.spritecollideany(self, vertical_borders):
            self.vx = -self.vx


class Border(pygame.sprite.Sprite):
    def __init__(self, x1, y1, x2, y2):
        super().__init__(all_sprites)
        if x1 == x2:
            self.add(vertical_borders)
            self.image = pygame.Surface([1, y2 - y1])
            self.rect = pygame.Rect(x1, y1, 1, y2 - y1)
        else:
            self.add(horizontal_borders)
            self.image = pygame.Surface([x2 - x1, 1])
            self.rect = pygame.Rect(x1, y1, x2 - x1, 1)


def draw_message(message, x, y):
    msg_width, msg_height = font.size(message)
    msg_rect = x, y
    text = font.render(message, True, black)
    screen.blit(text, msg_rect)


all_sprites = pygame.sprite.Group()
horizontal_borders = pygame.sprite.Group()
vertical_borders = pygame.sprite.Group()


def start():
    size_ = width, height = size
    screen_ = pygame.display.set_mode(size_)
    start_button = Button(50, 'Начать игру', '', screen_)

    Border(5, 5, width - 5, 5)
    Border(5, height - 5, width - 5, height - 5)
    Border(5, 5, 5, height - 5)
    Border(width - 5, 5, width - 5, height - 5)

    for i in range(20):
        Ball(20, 100, 100)
    clock = pygame.time.Clock()
    data = open('data.txt').readlines()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and start_button.clicked(event.pos):
                main()

        screen_.fill(pygame.Color("white"))
        start_button.draw_button()
        start_button.change_color()
        all_sprites.draw(screen)
        all_sprites.update()
        draw_message('Топ 10 лучших результатов(кол-во ходов, дата):', 400, 50)
        if len(data) == 0:
            draw_message('Еще не сыграно ни одной игры.', 450, 100)
        for i in range(min(len(data), 10)):
            draw_message(data[i].rstrip(), 450, 100 + 25 * i)
        clock.tick(50)
        pygame.display.flip()
    pygame.quit()


def main():
    game_over = False
    game_not_started = True
    mode = None
    draw = False

    screen.fill(very_light_gray)

    msg = "Выберите способ создания кораблей"
    auto_btn = Button(left_m + 12 * cell_size, 'Случайная генерация', msg, screen)
    select_btn = Button(left_m + 20 * cell_size, 'Ручной режим', '', screen)

    board1 = Board(10, 10, left_m, upper_m, "Компьютер:")
    board1.generate_pc_field()

    board2 = Board(10, 10, size[0] - left_m - 10 * cell_size, upper_m, "Вы:")

    while game_not_started:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if event.type == pygame.QUIT:
                    game_over = True
                    game_not_started = False
                    pygame.mixer.music.stop()
            elif turn is False and event.type == pygame.MOUSEBUTTONDOWN:
                if mode is None:
                    if auto_btn.clicked(event.pos):
                        mode = False
                        board2.generate_pc_field()
                        game_not_started = False
                    if select_btn.clicked(event.pos):
                        mode = True

                        game_not_started = False
        if mode is None:
            auto_btn.draw_button()
            auto_btn.change_color()
            select_btn.draw_button()
            select_btn.change_color()
        board1.render(screen)
        board2.render(screen)
        pygame.display.flip()

    screen.fill(very_light_gray)

    first_pos = (0, 0)

    d = {1: 0, 2: 0, 3: 0, 4: 0}
    st = []

    while mode:
        screen.fill(very_light_gray)

        board1.render(screen)
        board2.render(screen)
        # cancel_btn = Button(left_m + 10 * cell_size, "Удалить последний корабль", '', screen)
        # cancel_btn.draw_button()

        # if not board2.ships:
        #    cancel_btn.change_color()
        mouse_coords = pygame.mouse.get_pos()
        # if not board2.ships:
        #    cancel_btn.change_color(col=(50, 50, 50))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
                mode = False
                pygame.mixer.music.stop()
            if event.type == pygame.MOUSEBUTTONDOWN:
                #    if cancel_btn.clicked(event.pos):
                #        if board2.ships:
                #            board2.ships.discard(st[-1])
                #            d[max(abs(st[-1][0][0] - st[-1][1][0]), abs(st[-1][0][1] - st[-1][1][1])) + 1] -= 1
                #            st.pop()
                #    else:
                #        first_pos = pygame.mouse.get_pos()
                draw = True
                first_pos = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEMOTION and draw:
                x1, y1 = first_pos
                x2, y2 = pygame.mouse.get_pos()
                pygame.draw.rect(screen, black, (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1) ), 2)
            if event.type == pygame.MOUSEBUTTONUP:
                x1, y1 = first_pos
                x2, y2 = pygame.mouse.get_pos()
                start_ship = ((min(x1, x2) - board2.left) // cell_size + 1, (min(y1, y2) - upper_m) // cell_size + 1)
                end_ship = ((max(x1, x2) - board2.left) // cell_size + 1, (max(y1, y2) - upper_m) // cell_size + 1)
                if 0 < start_ship[0] < 11 and 0 < start_ship[1] < 11 and 0 < end_ship[0] < 11 and 0 < end_ship[1] < 11:
                    if (start_ship[0] == end_ship[0] and abs(start_ship[1] - end_ship[1]) < 4 and
                        d[1 + abs(start_ship[1] - end_ship[1])] < 4 - abs(start_ship[1] - end_ship[1])) or (
                            start_ship[1] == end_ship[1] and abs(start_ship[0] - end_ship[0]) < 4 and
                            d[1 + abs(start_ship[0] - end_ship[0])] < 4 - abs(start_ship[0] - end_ship[0])):
                        boat = []
                        for i in range(start_ship[0], end_ship[0] + 1):
                            for j in range(start_ship[1], end_ship[1] + 1):
                                boat.append((i, j))
                        if all([i in board2.avalible_cells for i in boat]):
                            d[max(end_ship[1] - start_ship[1], end_ship[0] - start_ship[0]) + 1] += 1
                            for i in range(start_ship[0] - 1, end_ship[0] + 2):
                                for j in range(start_ship[1] - 1, end_ship[1] + 2):
                                    if (i, j) in board2.avalible_cells:
                                        board2.avalible_cells.remove((i, j))
                                        boat = tuple(boat)
                                        st.append(boat)
                                        board2.add_ship(boat)
                draw = False
            if len(board2.ships) == 10:
                mode = False
            board2.draw_ships(screen)
            pygame.display.flip()
    screen.fill(very_light_gray)
    moves = 0
    while not game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
                pygame.mixer.music.stop()
            elif turn is False and event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                board1.get_click(event.pos)
                moves += 1
        board1.render(screen)
        board2.render(screen)
        board1.draw_ships(screen)
        board2.draw_ships(screen)
        pygame.display.flip()
        if turn:
            board2.shoot_choice()
        if len(board2.shooted_ships) == 20:
            message = 'ВЫ ПРОГИГРАЛИ :( НОВАЯ ИГРА АВТОМАТИЧЕСКИ НАЧНЕТСЯ ЧЕРЕЗ 5СЕК'
            msg_width, msg_height = font.size(message)
            msg_rect = 100, 400
            text = font.render(message, True, (255, 0, 0))
            screen.blit(text, msg_rect)
            pygame.display.flip()
            pygame.time.delay(5000)
            main()

        elif len(board1.shooted_ships) == 20:
            with open('data.txt') as base:
                file = base.readlines().split('\n')
                base.close()
            file.append(f'{moves} {datetime.now()}')
            with open('data.txt', 'w') as base:
                base.writelines(file)
                base.close()
            message = 'ВЫ ВЫИГРАЛИ! НОВАЯ ИГРА АВТОМАТИЧЕСКИ НАЧНЕТСЯ ЧЕРЕЗ 5СЕК'
            msg_width, msg_height = font.size(message)
            msg_rect = 100, 400
            text = font.render(message, True, (255, 0, 0))
            screen.blit(text, msg_rect)
            pygame.display.flip()
            pygame.time.delay(5000)
            main()

    pygame.quit()


if __name__ == '__main__':
    start()