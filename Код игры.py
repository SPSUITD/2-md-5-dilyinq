import pygame
import sys
import random

pygame.init()

WIDTH, HEIGHT = 322, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Звёздный спринт")

FPS = 60
COMBO_WINDOW = 500

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
RED = (255, 0, 0)

pygame.font.init()
TEXT_FONT = pygame.font.SysFont('impact', 20)

TRACK_IMGS = {
    "level1": pygame.transform.scale(pygame.image.load("1 уровень.png").convert_alpha(), (WIDTH, HEIGHT)),
    "level2": pygame.transform.scale(pygame.image.load("2 уровень.png").convert_alpha(), (WIDTH, HEIGHT)),
    "level3": pygame.transform.scale(pygame.image.load("3 уровень.png").convert_alpha(), (WIDTH, HEIGHT))
}

CAR_IMAGES = {
    "белая": pygame.image.load("белая ровно.png").convert_alpha(),
    "красная": pygame.image.load("красная ровно.png").convert_alpha(),
    "синяя": pygame.image.load("синяя ровно.png").convert_alpha()
}

STAR_IMG = pygame.image.load("звезда.png").convert_alpha()
PIT_IMG = pygame.image.load("лунка.png").convert_alpha()
ENEMY_CAR_IMG_ORIG = pygame.image.load("враг.png").convert_alpha()
EXPLOSION_IMG = pygame.image.load("взрыв.png").convert_alpha()

STAR_SCALE = 0.2
STAR_IMG = pygame.transform.scale(STAR_IMG,
                                  (int(STAR_IMG.get_width() * STAR_SCALE), int(STAR_IMG.get_height() * STAR_SCALE)))
PIT_IMG = pygame.transform.scale(PIT_IMG, (50, 50))
EXPLOSION_IMG = pygame.transform.scale(EXPLOSION_IMG, (80, 80))

CAR_WIDTH, CAR_HEIGHT = int(80 * 0.8), int(120 * 0.8)
ENEMY_CAR_IMG = pygame.transform.scale(ENEMY_CAR_IMG_ORIG, (CAR_WIDTH, CAR_HEIGHT))

LANE_X = [80, 161, 240]

pygame.mixer.init()
try:
    STAR_SOUND = pygame.mixer.Sound("звук звезд.mp3")
except FileNotFoundError:
    STAR_SOUND = None
try:
    GAME_OVER_SOUND = pygame.mixer.Sound("конец игры.mp3")
except FileNotFoundError:
    GAME_OVER_SOUND = None
try:
    CRASH_CAR_SOUND = pygame.mixer.Sound("авария.mp3")
except FileNotFoundError:
    CRASH_CAR_SOUND = None
try:
    CRASH_PIT_SOUND = pygame.mixer.Sound("взрыв.mp3")
except FileNotFoundError:
    CRASH_PIT_SOUND = None
try:
    ENGINE_SOUND = pygame.mixer.Sound("звук на фоне.mp3")
    ENGINE_SOUND.set_volume(0.3)
except FileNotFoundError:
    ENGINE_SOUND = None
try:
    ACCEL_SOUND = pygame.mixer.Sound("ускорение.mp3")
except FileNotFoundError:
    ACCEL_SOUND = None
try:
    DECEL_SOUND = pygame.mixer.Sound("торможение.mp3")
except FileNotFoundError:
    DECEL_SOUND = None


def car_menu():
    font = pygame.font.SysFont(None, 24)
    colors = ["Белый", "Красный", "Синий"]
    selected = 0
    while True:
        WIN.fill((30, 30, 30))
        title = font.render("Выберите цвет машины:", True, WHITE)
        WIN.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))  # Заголовок центруется по ширине окна
        for idx, color in enumerate(colors):
            color_text = font.render(color, True, WHITE if idx != selected else (255, 215, 0))
            WIN.blit(color_text,
                     (WIDTH // 2 - color_text.get_width() // 2, 100 + idx * 30))  # Опять центрирование пунктов
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and selected > 0:
                    selected -= 1
                elif event.key == pygame.K_DOWN and selected < len(colors) - 1:
                    selected += 1
                elif event.key == pygame.K_RETURN:
                    return pygame.transform.scale(CAR_IMAGES[list(CAR_IMAGES.keys())[selected]],
                                                  (CAR_WIDTH, CAR_HEIGHT))
        pygame.display.update()


def level_menu():
    font = pygame.font.SysFont(None, 24)
    levels = ["Первый уровень", "Второй уровень", "Третий уровень"]
    selected_level = 0  # Выбор текущего уровня
    while True:
        WIN.fill((30, 30, 30))
        title = font.render("Выберите уровень:", True, WHITE)
        WIN.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))  # Заголовок центруется по ширине окна
        for idx, level_name in enumerate(levels):
            level_text = font.render(level_name, True, WHITE if idx != selected_level else (255, 215, 0))
            WIN.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, 100 + idx * 30))  # Централизация пунктов
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and selected_level > 0:
                    selected_level -= 1
                elif event.key == pygame.K_DOWN and selected_level < len(levels) - 1:
                    selected_level += 1
                elif event.key == pygame.K_RETURN:
                    return selected_level + 1
        pygame.display.update()


class Game:
    def __init__(self, start_level=1):
        self.clock = pygame.time.Clock()
        self.car_img = car_menu()
        self.car_pos = [LANE_X[1] - CAR_WIDTH // 2, HEIGHT - CAR_HEIGHT - 30]
        self.current_lane = 1
        self.move_timer = 0
        self.stars = []
        self.pits = []
        self.enemy_cars = []
        self.explosions = []
        self.score = 0
        self.lives = 3
        self.speed = 4
        self.min_speed = 1
        self.max_speed = 10
        self.game_over = False
        self.last_star_time = 0
        self.combo_count = 0
        self.level = start_level
        self.track_y = 0
        self.engine_playing = False

    def get_occupied_lanes(self):
        occupied = set()
        for pit in self.pits:
            occupied.add(pit["lane"])
        for enemy_car in self.enemy_cars:
            occupied.add(enemy_car["lane"])
        return occupied

    def spawn_star(self):
        available_lanes = [0, 1, 2]
        if self.pits:
            available_lanes = [lane for lane in available_lanes if lane != self.pits[-1]["lane"]]
        lane = random.choice(available_lanes)
        self.stars.append({"lane": lane, "y": -STAR_IMG.get_height()})

    def spawn_pit(self):
        if len(self.pits) >= 1:
            return
        occupied = self.get_occupied_lanes()
        available_lanes = [lane for lane in [0, 1, 2] if lane not in occupied]
        if len(available_lanes) == 0:
            return
        lane = random.choice(available_lanes)
        self.pits.append({"lane": lane, "y": -PIT_IMG.get_height()})

    def spawn_enemy_car(self):
        if len(self.enemy_cars) >= 1:
            return
        occupied = self.get_occupied_lanes()
        available_lanes = [lane for lane in [0, 1, 2] if lane not in occupied]
        if len(available_lanes) == 0:
            return
        lane = random.choice(available_lanes)
        self.enemy_cars.append({"lane": lane, "y": -ENEMY_CAR_IMG.get_height()})

    def check_collision(self):
        for enemy_car in self.enemy_cars[
                         :]:
            if (
                    abs(enemy_car["lane"] - self.current_lane) < 1 and
                    enemy_car["y"] + ENEMY_CAR_IMG.get_height() > self.car_pos[1] and
                    enemy_car["y"] < self.car_pos[1] + CAR_HEIGHT
            ):
                self.lives -= 1
                if CRASH_CAR_SOUND:
                    CRASH_CAR_SOUND.play()

                self.explosions.append({
                    "x": self.car_pos[0] + CAR_WIDTH // 2,
                    "y": self.car_pos[1] + CAR_HEIGHT // 2,
                    "timer": 20
                })

                self.enemy_cars.remove(enemy_car)

                if self.lives <= 0:
                    self.game_over = True
                    if GAME_OVER_SOUND:
                        GAME_OVER_SOUND.play()

    def draw(self):
        WIN.fill(GRAY)
        track_img = TRACK_IMGS[f"level{self.level}"]

        # Прокручиваемый фон
        WIN.blit(track_img, (0, self.track_y))
        WIN.blit(track_img, (0, self.track_y - HEIGHT))

        WIN.blit(self.car_img, (self.car_pos[0], self.car_pos[1]))

        for star in self.stars:
            WIN.blit(STAR_IMG, (LANE_X[star["lane"]] - STAR_IMG.get_width() // 2, star["y"]))

        for pit in self.pits:
            WIN.blit(PIT_IMG, (LANE_X[pit["lane"]] - PIT_IMG.get_width() // 2, pit["y"]))

        for enemy_car in self.enemy_cars:
            WIN.blit(ENEMY_CAR_IMG, (LANE_X[enemy_car["lane"]] - ENEMY_CAR_IMG.get_width() // 2, enemy_car["y"]))

        for explosion in self.explosions[:]:
            WIN.blit(EXPLOSION_IMG, (explosion["x"] - EXPLOSION_IMG.get_width() // 2,
                                     explosion["y"] - EXPLOSION_IMG.get_height() // 2))
            explosion["timer"] -= 1
            if explosion["timer"] <= 0:
                self.explosions.remove(explosion)

        score_text = TEXT_FONT.render(f"Счёт: {self.score}", True, WHITE)
        WIN.blit(score_text, (10, 10))

        for i in range(self.lives):
            WIN.blit(STAR_IMG, (WIDTH - (STAR_IMG.get_width() + 5) * (i + 1), 10))

        if self.game_over:
            game_over_text = TEXT_FONT.render("Игра окончена!", True, RED)
            restart_text = TEXT_FONT.render("Нажмите 'R' для перезапуска", True, WHITE)
            WIN.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 20))
            WIN.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 20))

    def update(self):
        if self.game_over:
            if self.engine_playing and ENGINE_SOUND:
                ENGINE_SOUND.stop()
                self.engine_playing = False
            return

        if not self.engine_playing and ENGINE_SOUND:
            ENGINE_SOUND.play(-1)
            self.engine_playing = True

        if random.random() < 0.02: self.spawn_star()
        if random.random() < 0.01: self.spawn_pit()
        if random.random() < 0.008: self.spawn_enemy_car()

        self.track_y = (self.track_y + self.speed) % HEIGHT

        current_time = pygame.time.get_ticks()

        for star in self.stars[:]:
            star["y"] += self.speed
            if star["lane"] == self.current_lane and star["y"] + STAR_IMG.get_height() > self.car_pos[1]:
                self.stars.remove(star)
                if STAR_SOUND: STAR_SOUND.play()
                self.combo_count = self.combo_count + 1 if current_time - self.last_star_time < COMBO_WINDOW else 0
                self.score += 1 + self.combo_count
                self.last_star_time = current_time
            elif star["y"] > HEIGHT:
                self.stars.remove(star)

        for pit in self.pits[:]:
            pit["y"] += self.speed
            if pit["lane"] == self.current_lane and pit["y"] + PIT_IMG.get_height() > self.car_pos[1]:
                self.pits.remove(pit)
                self.lives -= 1
                if CRASH_PIT_SOUND: CRASH_PIT_SOUND.play()
                self.explosions.append({"x": self.car_pos[0] + CAR_WIDTH // 2,
                                        "y": self.car_pos[1] + CAR_HEIGHT // 2,
                                        "timer": 20})
                if self.lives <= 0:
                    self.game_over = True
                    if GAME_OVER_SOUND: GAME_OVER_SOUND.play()
            elif pit["y"] > HEIGHT:
                self.pits.remove(pit)

        for enemy_car in self.enemy_cars[:]:
            enemy_car["y"] += self.speed * 1.5
            if enemy_car["y"] > HEIGHT:
                self.enemy_cars.remove(enemy_car)

        self.check_collision()

    def run_game(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and self.game_over and event.key == pygame.K_r:
                    self.__init__(self.level)

            keys = pygame.key.get_pressed()
            if not self.game_over and self.move_timer == 0:
                if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.current_lane > 0:
                    new_lane = self.current_lane - 1
                    if not self.check_collision():
                        self.current_lane = new_lane
                        self.move_timer = 10
                    elif CRASH_CAR_SOUND:
                        CRASH_CAR_SOUND.play()
                elif (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.current_lane < 2:
                    new_lane = self.current_lane + 1
                    if not self.check_collision():
                        self.current_lane = new_lane
                        self.move_timer = 10
                    elif CRASH_CAR_SOUND:
                        CRASH_CAR_SOUND.play()
                elif keys[pygame.K_UP] and self.speed < self.max_speed:
                    self.speed = min(self.max_speed, self.speed + 0.1)
                    if ACCEL_SOUND: ACCEL_SOUND.play()
                elif keys[pygame.K_DOWN] and self.speed > self.min_speed:
                    self.speed = max(self.min_speed, self.speed - 0.1)
                    if DECEL_SOUND: DECEL_SOUND.play()

            if self.move_timer > 0:
                self.move_timer -= 1

            self.car_pos[0] = LANE_X[self.current_lane] - CAR_WIDTH // 2

            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

        if ENGINE_SOUND: ENGINE_SOUND.stop()
        pygame.quit()
        sys.exit()


def main():
    chosen_level = level_menu()
    game = Game(start_level=chosen_level)
    game.run_game()


if __name__ == "__main__":
    main()