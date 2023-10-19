import contextlib
import os
from typing import Callable

with contextlib.redirect_stdout(None):
    import pygame

pygame.mixer.pre_init(22050, -16, 0, 16384)
pygame.init()
pygame.mixer.init()

is_opened = False
is_closed = True
displayed_object = None

muted = False

INFO = pygame.display.Info()


class Player:
    def __init__(self, screen_width, screen_height):
        self.screen_width, self.screen_height = screen_width, screen_height

        player = pygame.image.load(os.path.join('assets', 'gallery', 'player.png')).convert_alpha()
        player = pygame.transform.scale(player, (40, 62))
        self.gravity = 1
        self.image = player
        self.map_ground = init_platform(self.screen_width, 160, 0, INFO.current_h - 160, '#394521')
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(midbottom=(50, self.map_ground[2].y))
        self.direction = pygame.math.Vector2()
        self.speed = 5
        self.jump_speed = 20
        self.is_on_floor = False

    def apply_gravity(self):
        self.direction.y += self.gravity
        self.rect.y += self.direction.y

    def platform_collision(self, platforms):
        for _, mask, rect in platforms:
            offset_x, offset_y = rect.x - self.rect.x, rect.y - self.rect.y
            intersection_point = self.mask.overlap(mask, (offset_x, offset_y))
            if intersection_point:
                if self.direction.y > 0:
                    self.rect.bottom = rect.top
                    if (self.rect.bottom != intersection_point[1] + self.rect.y + 1) and (
                            self.mask.overlap_area(mask, (offset_x, offset_y)) in (12, 16, 25)):
                        self.rect.x += 15
                    self.direction.y = 0
                    self.is_on_floor = True
                elif self.direction.y < 0:
                    self.rect.top = rect.bottom
                    self.direction.y = 1

        if self.is_on_floor and self.direction.y != 0:
            self.is_on_floor = False

    def user_left_right(self, pressed_keys):
        move_left = pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_a]
        move_right = pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d]

        if move_right and self.rect.right <= self.screen_width:
            self.direction.x = 1
        elif move_left and self.rect.left >= 0:
            self.direction.x = -1
        else:
            self.direction.x = 0

    def user_jumping(self, pressed_keys):
        move_left = pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_a]
        move_right = pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d]
        jump = pressed_keys[pygame.K_SPACE] or pressed_keys[pygame.K_w] or pressed_keys[pygame.K_UP]

        if move_right and self.rect.right <= self.screen_width:
            self.direction.x = 1
        elif move_left and self.rect.left >= 0:
            self.direction.x = -1
        else:
            self.direction.x = 0

        if jump and self.is_on_floor:
            self.direction.y = -self.jump_speed

    def room_update(self, platforms):
        self.user_jumping(pygame.key.get_pressed())
        self.rect.x += self.direction.x * self.speed
        self.apply_gravity()
        self.platform_collision(platforms)

    def map_update(self):
        self.user_left_right(pygame.key.get_pressed())
        self.rect.x += self.direction.x * self.speed


class Levels:
    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int, player: Player):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.door_surf, self.door_rect = init_room_objects((67, 97), 100, player.map_ground[2].y, 'door')
        self.victory_door_surf, self.victory_door_rect = init_room_objects((67, 97), screen_width - 100,
                                                                           player.map_ground[2].y, 'victory_door')
        self.level_1_build(screen, screen_width, screen_height, player)
        self.level_2_build(screen, screen_width, screen_height, player)
        self.level_3_build(screen, screen_width, screen_height, player)

    def level_1(self, screen: pygame.Surface, screen_width: int, screen_height: int, player: Player, mode: str,
                colliding: bool, first_time: bool, uprising_house_rect: pygame.Rect):
        if not colliding:
            player.room_update(self.uprising_platforms)

        if not muted:
            self.uprising_music.play(loops=-1)
            self.uprising_music.set_volume(0.05)
        self.level_1_draw(screen, player)
        if enter_room(player.rect, self.door_rect):
            self.uprising_music.fadeout(2700)
            fade(screen, screen_width, screen_height, lambda: self.level_1_draw(screen, player))
            first_time = True
            player.rect.x, player.rect.y = uprising_house_rect.center[0], player.map_ground[2].y - player.rect.height
            player.rect.y = player.map_ground[2].y - player.rect.height
            mode = 'map'
        colliding = (interact(screen, player.rect, self.uprising_coat_of_arms_rect_1, self.uprising_infoboxes,
                              'coat_of_arms_1')
                     or interact(screen, player.rect, self.uprising_coat_of_arms_rect_2, self.uprising_infoboxes,
                                 'coat_of_arms_2')
                     or interact(screen, player.rect, self.uprising_flag_rect_1, self.uprising_infoboxes, 'flag_1')
                     or interact(screen, player.rect, self.uprising_flag_rect_2, self.uprising_infoboxes, 'flag_2')
                     or interact(screen, player.rect, self.uprising_flag_rect_3, self.uprising_infoboxes, 'flag_3')
                     or interact(screen, player.rect, self.uprising_question_rect_1, self.uprising_infoboxes,
                                 'question_1')
                     or interact(screen, player.rect, self.uprising_question_rect_2, self.uprising_infoboxes,
                                 'question_2')
                     or interact(screen, player.rect, self.uprising_question_rect_3, self.uprising_infoboxes,
                                 'question_3'))
        return mode, colliding, first_time

    def level_1_build(self, screen: pygame.Surface, screen_width: int, screen_height: int, player: Player):
        self.uprising_music = pygame.mixer.Sound(os.path.join('assets', 'music', 'uprising_music.mp3'))
        self.uprising_info = None
        with open('assets/info/uprising_info.txt', encoding="utf8") as info:
            self.uprising_info = info.readlines()
        self.uprising_platforms = [init_platform(80, 10, self.screen_width - 1240, self.screen_height - 270),
                                   init_platform(100, 10, self.screen_width - 1430, self.screen_height - 675),
                                   init_platform(100, 10, self.screen_width - 1795, self.screen_height - 380),
                                   init_platform(100, 10, self.screen_width - 1695, self.screen_height - 570),
                                   init_platform(100, 10, self.screen_width - 575, self.screen_height - 600),
                                   init_platform(100, 10, self.screen_width - 780, self.screen_height - 410),
                                   init_platform(100, 10, self.screen_width - 1170, self.screen_height - 505),
                                   init_platform(100, 10, self.screen_width - 1470, self.screen_height - 405),
                                   init_platform(100, 10, self.screen_width - 970, self.screen_height - 705),
                                   init_platform(screen_width, 160, 0, INFO.current_h - 160, '#043619'),
                                   init_platform(screen_width, 1, 0, -2)]
        self.uprising_coat_of_arms_surf_1, self.uprising_coat_of_arms_rect_1 = init_symbol('coat_of_arms',
                                                                                           'uprising_icon', (42, 54),
                                                                                           self.screen_width - 1670,
                                                                                           self.screen_height - 630)
        self.uprising_coat_of_arms_surf_2, self.uprising_coat_of_arms_rect_2 = init_symbol('coat_of_arms',
                                                                                           'uprising_icon', (42, 54),
                                                                                           self.screen_width - 540,
                                                                                           self.screen_height - 660)
        self.uprising_flag_surf_1, self.uprising_flag_rect_1 = init_symbol('flag', 'uprising_icon', (54, 61),
                                                                           self.screen_width - 1770,
                                                                           self.screen_height - 445)
        self.uprising_flag_surf_2, self.uprising_flag_rect_2 = init_symbol('flag', 'uprising_icon', (54, 61),
                                                                           self.screen_width - 1390,
                                                                           self.screen_height - 740)
        self.uprising_flag_surf_3, self.uprising_flag_rect_3 = init_symbol('flag', 'uprising_icon', (54, 61),
                                                                           self.screen_width - 745,
                                                                           self.screen_height - 480)
        self.uprising_question_surf_1, self.uprising_question_rect_1 = init_symbol('question', 'icon', (48, 87),
                                                                                   self.screen_width - 1145,
                                                                                   self.screen_height - 595)
        self.uprising_question_surf_2, self.uprising_question_rect_2 = init_symbol('question', 'icon', (48, 87),
                                                                                   self.screen_width - 1445,
                                                                                   self.screen_height - 495)
        self.uprising_question_surf_3, self.uprising_question_rect_3 = init_symbol('question', 'icon', (48, 87),
                                                                                   self.screen_width - 945,
                                                                                   self.screen_height - 795)
        self.uprising_infoboxes = {
            'coat_of_arms_1': InfoBox(screen, screen_width, screen_height, player, self.uprising_coat_of_arms_rect_1,
                                      thing=init_symbol(symbol='coat_of_arms', variety='vitezovic', size=(194, 289),
                                                        x=15, y=15), message=self.uprising_info[0].strip('\n')),
            'coat_of_arms_2': InfoBox(screen, screen_width, screen_height, player, self.uprising_coat_of_arms_rect_2,
                                      thing=init_symbol(symbol='coat_of_arms', variety='zefarovic', size=(277, 357),
                                                        x=15, y=15), message=self.uprising_info[1].strip('\n')),
            'flag_1': InfoBox(screen, screen_width, screen_height, player, self.uprising_flag_rect_1,
                              thing=init_symbol(symbol='flag', variety='green_uprising', size=(320, 192), x=15, y=15),
                              message=self.uprising_info[2].strip('\n')),
            'flag_2': InfoBox(screen, screen_width, screen_height, player, self.uprising_flag_rect_2,
                              thing=init_symbol(symbol='flag', variety='red_uprising', size=(310, 297), x=15, y=15),
                              message=self.uprising_info[3].strip('\n')),
            'flag_3': InfoBox(screen, screen_width, screen_height, player, self.uprising_flag_rect_3,
                              thing=init_symbol(symbol='flag', variety='tricolour_uprising', size=(319, 251),
                                                x=15, y=15),
                              message=self.uprising_info[4].strip('\n')),
            'question_1': InfoBox(screen, screen_width, screen_height, player, self.uprising_question_rect_1,
                                  thing=init_symbol(symbol='coat_of_arms', variety='zefarovic', size=(185, 238),
                                                    x=15, y=15),
                                  category='question', message=self.uprising_info[5].strip('\n'),
                                  answers=['A) Павел Ритер-Витезович', 'Б) Христофор Жефарович',
                                           'В) Паисий Хилендарски'], correct_answer=2),
            'question_2': InfoBox(screen, screen_width, screen_height, player, self.uprising_question_rect_2,
                                  thing=init_symbol(symbol='flag', variety='levski', size=(279, 169), x=15, y=15),
                                  category='question', message=self.uprising_info[6].strip('\n'),
                                  answers=['А) Христо Ботев', 'Б) Георги С. Раковски', 'В) Васил Левски'],
                                  correct_answer=3),
            'question_3': InfoBox(screen, screen_width, screen_height, player, self.uprising_question_rect_2,
                                  thing=init_symbol(symbol='flag', variety='rakovski', size=(359, 274), x=15, y=15),
                                  category='question', message=self.uprising_info[7].strip('\n'),
                                  answers=['А) Одески', 'Б) Белградски', 'В) Букурещки'], correct_answer=1)}

    def level_1_draw(self, screen: pygame.Surface, player: Player):
        screen.fill('#BAAB98')
        screen.blit(self.uprising_coat_of_arms_surf_1, self.uprising_coat_of_arms_rect_1)
        screen.blit(self.uprising_coat_of_arms_surf_2, self.uprising_coat_of_arms_rect_2)
        screen.blit(self.uprising_flag_surf_1, self.uprising_flag_rect_1)
        screen.blit(self.uprising_flag_surf_2, self.uprising_flag_rect_2)
        screen.blit(self.uprising_flag_surf_3, self.uprising_flag_rect_3)
        screen.blit(self.uprising_question_surf_1, self.uprising_question_rect_1)
        screen.blit(self.uprising_question_surf_2, self.uprising_question_rect_2)
        screen.blit(self.uprising_question_surf_3, self.uprising_question_rect_3)
        for platform in self.uprising_platforms:
            screen.blit(platform[0], platform[2])
        screen.blit(self.door_surf, self.door_rect)
        screen.blit(player.image, player.rect)

    def level_2(self, screen: pygame.Surface, screen_width: int, screen_height: int, player: Player, mode: str,
                colliding: bool, first_time: bool, tsar_house_rect: pygame.Rect):
        if not colliding:
            player.room_update(self.tsar_platforms)
        if not muted:
            self.tsar_music.play(loops=-1)
            self.tsar_music.set_volume(0.05)
        self.level_2_draw(screen, player)
        if enter_room(player.rect, self.door_rect):
            self.tsar_music.fadeout(2700)
            fade(screen, screen_width, screen_height, lambda: self.level_2_draw(screen, player))
            first_time = True
            player.rect.x, player.rect.y = tsar_house_rect.center[0], player.map_ground[2].y - player.rect.height
            mode = 'map'
        colliding = (interact(screen, player.rect, self.tsar_coat_of_arms_rect_1, self.tsar_infoboxes, 'coat_of_arms_1')
                     or interact(screen, player.rect, self.tsar_coat_of_arms_rect_2, self.tsar_infoboxes,
                                 'coat_of_arms_2')
                     or interact(screen, player.rect, self.tsar_coat_of_arms_rect_3, self.tsar_infoboxes,
                                 'coat_of_arms_3')
                     or interact(screen, player.rect, self.tsar_coat_of_arms_rect_4, self.tsar_infoboxes,
                                 'coat_of_arms_4')
                     or interact(screen, player.rect, self.tsar_flag_rect_1, self.tsar_infoboxes, 'flag_1')
                     or interact(screen, player.rect, self.tsar_anthem_rect_1, self.tsar_infoboxes, 'anthem_1')
                     or interact(screen, player.rect, self.tsar_anthem_rect_2, self.tsar_infoboxes, 'anthem_2')
                     or interact(screen, player.rect, self.tsar_question_rect_1, self.tsar_infoboxes, 'question_1')
                     or interact(screen, player.rect, self.tsar_question_rect_2, self.tsar_infoboxes, 'question_2')
                     or interact(screen, player.rect, self.tsar_question_rect_3, self.tsar_infoboxes, 'question_3'))
        return mode, colliding, first_time

    def level_2_build(self, screen: pygame.Surface, screen_width: int, screen_height: int, player: Player):
        self.tsar_music = pygame.mixer.Sound(os.path.join('assets', 'music', 'tsar_music.mp3'))
        self.tsar_info = None
        with open('assets/info/tsar_info.txt', encoding="utf8") as info:
            self.tsar_info = info.readlines()
        self.tsar_platforms = [init_platform(100, 10, self.screen_width - 1160, self.screen_height - 270),
                               init_platform(100, 10, self.screen_width - 1585, self.screen_height - 510),
                               init_platform(70, 10, self.screen_width - 1370, self.screen_height - 380),
                               init_platform(100, 10, self.screen_width - 690, self.screen_height - 510),
                               init_platform(70, 10, self.screen_width - 870, self.screen_height - 380),
                               init_platform(100, 10, self.screen_width - 1800, self.screen_height - 670),
                               init_platform(100, 10, self.screen_width - 1400, self.screen_height - 670),
                               init_platform(100, 10, self.screen_width - 900, self.screen_height - 670),
                               init_platform(100, 10, self.screen_width - 500, self.screen_height - 670),
                               init_platform(100, 10, self.screen_width - 1595, self.screen_height - 730),
                               init_platform(100, 10, self.screen_width - 695, self.screen_height - 730),
                               init_platform(100, 10, self.screen_width - 1160, self.screen_height - 580),
                               init_platform(screen_width, 160, 0, INFO.current_h - 160, '#947E01'),
                               init_platform(screen_width, 1, 0, -2)]
        self.tsar_coat_of_arms_surf_1, self.tsar_coat_of_arms_rect_1 = init_symbol('coat_of_arms', 'tsar_icon',
                                                                                   (42, 54), self.screen_width - 1770,
                                                                                   self.screen_height - 730)
        self.tsar_coat_of_arms_surf_2, self.tsar_coat_of_arms_rect_2 = init_symbol('coat_of_arms', 'tsar_icon',
                                                                                   (42, 54), self.screen_width - 1370,
                                                                                   self.screen_height - 730)
        self.tsar_coat_of_arms_surf_3, self.tsar_coat_of_arms_rect_3 = init_symbol('coat_of_arms', 'tsar_icon',
                                                                                   (42, 54), self.screen_width - 870,
                                                                                   self.screen_height - 730)
        self.tsar_coat_of_arms_surf_4, self.tsar_coat_of_arms_rect_4 = init_symbol('coat_of_arms', 'tsar_icon',
                                                                                   (42, 54), self.screen_width - 470,
                                                                                   self.screen_height - 730)
        self.tsar_flag_surf_1, self.tsar_flag_rect_1 = init_symbol('flag', 'tsar_icon', (54, 61),
                                                                   self.screen_width - 1120, self.screen_height - 335)
        self.tsar_anthem_surf_1, self.tsar_anthem_rect_1 = init_symbol('anthem', 'anthem_icon', (64, 60),
                                                                       self.screen_width - 1570,
                                                                       self.screen_height - 580)
        self.tsar_anthem_surf_2, self.tsar_anthem_rect_2 = init_symbol('anthem', 'anthem_icon', (64, 60),
                                                                       self.screen_width - 670,
                                                                       self.screen_height - 580)
        self.tsar_question_surf_1, self.tsar_question_rect_1 = init_symbol('question', 'icon', (48, 87),
                                                                           self.screen_width - 1570,
                                                                           self.screen_height - 820)
        self.tsar_question_surf_2, self.tsar_question_rect_2 = init_symbol('question', 'icon', (48, 87),
                                                                           self.screen_width - 670,
                                                                           self.screen_height - 820)
        self.tsar_question_surf_3, self.tsar_question_rect_3 = init_symbol('question', 'icon', (48, 87),
                                                                           self.screen_width - 1135,
                                                                           self.screen_height - 670)
        self.tsar_infoboxes = {
            'coat_of_arms_1': InfoBox(screen, screen_width, screen_height, player, self.tsar_coat_of_arms_rect_1,
                                      thing=init_symbol(symbol='coat_of_arms', variety='1879-1881', size=(),
                                                        x=15, y=15),
                                      message=self.tsar_info[0].strip('\n')),
            'coat_of_arms_2': InfoBox(screen, screen_width, screen_height, player, self.tsar_coat_of_arms_rect_2,
                                      thing=init_symbol(symbol='coat_of_arms', variety='alexander', size=(),
                                                        x=15, y=15),
                                      message=self.tsar_info[1].strip('\n')),
            'coat_of_arms_3': InfoBox(screen, screen_width, screen_height, player, self.tsar_coat_of_arms_rect_3,
                                      thing=init_symbol(symbol='coat_of_arms', variety='ferdinant', size=(),
                                                        x=15, y=15),
                                      message=self.tsar_info[2].strip('\n')),
            'coat_of_arms_4': InfoBox(screen, screen_width, screen_height, player, self.tsar_coat_of_arms_rect_4,
                                      thing=init_symbol(symbol='coat_of_arms', variety='boris3', size=(), x=15, y=15),
                                      message=self.tsar_info[3].strip('\n')),
            'flag_1': InfoBox(screen, screen_width, screen_height, player, self.tsar_flag_rect_1,
                              thing=init_symbol(symbol='flag', variety='base_tricolour', size=(384, 231), x=15, y=15),
                              message=self.tsar_info[4].strip('\n')),
            'anthem_1': InfoBox(screen, screen_width, screen_height, player, self.tsar_anthem_rect_1,
                                thing=init_symbol(symbol='portrait', variety='petko_slaveikov', size=(263, 364), x=15,
                                                  y=15), message=self.tsar_info[5].strip('\n')),
            'anthem_2': InfoBox(screen, screen_width, screen_height, player, self.tsar_anthem_rect_2,
                                thing=init_symbol(symbol='portrait', variety='ivan_vazov', size=(263, 397), x=15, y=15),
                                message=self.tsar_info[6].strip('\n')),
            'question_1': InfoBox(screen, screen_width, screen_height, player, self.tsar_question_rect_1,
                                  thing=init_symbol(symbol='coat_of_arms', variety='ferdinant', size=(), x=15, y=15),
                                  category='question', message=self.tsar_info[7].strip('\n'),
                                  answers=['A) Александър I Български', 'Б) Борис III', 'В) Фердинанд I Български'],
                                  correct_answer=3),
            'question_2': InfoBox(screen, screen_width, screen_height, player, self.tsar_question_rect_2,
                                  thing=init_symbol(symbol='coat_of_arms', variety='alexander', size=(), x=15, y=15),
                                  category='question', message=self.tsar_info[8].strip('\n'),
                                  answers=['А) Борис III', 'Б) Александър I Български', 'В) Фердинанд I Български'],
                                  correct_answer=2),
            'question_3': InfoBox(screen, screen_width, screen_height, player, self.tsar_question_rect_3,
                                  category='question_with_button',
                                  tune=pygame.mixer.Sound(os.path.join('assets', 'anthems',
                                                                       'shumi_marica_ivan_vazov.mp3')),
                                  current_bg_music=self.tsar_music,
                                  button_text='Шуми Марица', message=self.tsar_info[9].strip('\n'),
                                  answers=['А) Иван Вазов', 'Б) Гео Милев', 'В) Петко Славейков'], correct_answer=1)}

    def level_2_draw(self, screen: pygame.Surface, player: Player):
        screen.fill('#BAAB98')
        screen.blit(self.tsar_coat_of_arms_surf_1, self.tsar_coat_of_arms_rect_1)
        screen.blit(self.tsar_coat_of_arms_surf_2, self.tsar_coat_of_arms_rect_2)
        screen.blit(self.tsar_coat_of_arms_surf_3, self.tsar_coat_of_arms_rect_3)
        screen.blit(self.tsar_coat_of_arms_surf_4, self.tsar_coat_of_arms_rect_4)
        screen.blit(self.tsar_flag_surf_1, self.tsar_flag_rect_1)
        screen.blit(self.tsar_anthem_surf_1, self.tsar_anthem_rect_1)
        screen.blit(self.tsar_anthem_surf_2, self.tsar_anthem_rect_2)
        screen.blit(self.tsar_question_surf_1, self.tsar_question_rect_1)
        screen.blit(self.tsar_question_surf_2, self.tsar_question_rect_2)
        screen.blit(self.tsar_question_surf_3, self.tsar_question_rect_3)
        for platform in self.tsar_platforms:
            screen.blit(platform[0], platform[2])
        screen.blit(self.door_surf, self.door_rect)
        screen.blit(player.image, player.rect)

    def level_3(self, screen: pygame.Surface, screen_width: int, screen_height: int, player: Player, mode: str,
                colliding: bool, first_time: bool, communist_house_rect: pygame.Rect, victory: bool):
        if not colliding:
            player.room_update(self.communist_platforms)
        if not muted:
            self.communist_music.play(loops=-1)
            self.communist_music.set_volume(0.03)
        self.level_3_draw(screen, player, victory)
        if enter_room(player.rect, self.door_rect):
            self.communist_music.fadeout(2700)
            fade(screen, screen_width, screen_height, lambda: self.level_3_draw(screen, player, victory))
            first_time = True
            player.rect.x, player.rect.y = communist_house_rect.center[0], player.map_ground[2].y - player.rect.height
            mode = 'map'
        if enter_room(player.rect, self.victory_door_rect):
            self.communist_music.fadeout(2700)
            fade(screen, screen_width, screen_height, lambda: self.level_3_draw(screen, player, victory))
            first_time = True
            player.rect.x, player.rect.y = communist_house_rect.center[0], player.map_ground[2].y - player.rect.height
            mode = 'victory_screen'

        colliding = (interact(screen, player.rect, self.communist_coat_of_arms_rect_1, self.communist_infoboxes,
                              'coat_of_arms_1')
                     or interact(screen, player.rect, self.communist_coat_of_arms_rect_2, self.communist_infoboxes,
                                 'coat_of_arms_2')
                     or interact(screen, player.rect, self.communist_flag_rect_1, self.communist_infoboxes, 'flag_1')
                     or interact(screen, player.rect, self.communist_anthem_rect_1, self.communist_infoboxes,
                                 'anthem_1')
                     or interact(screen, player.rect, self.communist_anthem_rect_2, self.communist_infoboxes,
                                 'anthem_2')
                     or interact(screen, player.rect, self.communist_anthem_rect_3, self.communist_infoboxes,
                                 'anthem_3')
                     or interact(screen, player.rect, self.communist_anthem_rect_4, self.communist_infoboxes,
                                 'anthem_4')
                     or interact(screen, player.rect, self.communist_question_rect_1, self.communist_infoboxes,
                                 'question_1')
                     or interact(screen, player.rect, self.communist_question_rect_2, self.communist_infoboxes,
                                 'question_2')
                     or interact(screen, player.rect, self.communist_question_rect_3, self.communist_infoboxes,
                                 'question_3'))
        return mode, colliding, first_time

    def level_3_build(self, screen: pygame.Surface, screen_width: int, screen_height: int, player: Player):
        self.communist_music = pygame.mixer.Sound(os.path.join('assets', 'music', 'communist_music.mp3'))
        self.communist_info = None
        with open('assets/info/communist_info.txt', encoding="utf8") as info:
            self.communist_info = info.readlines()
        self.communist_platforms = [init_platform(100, 10, self.screen_width - 1160, self.screen_height - 310),
                                    init_platform(100, 10, self.screen_width - 1585, self.screen_height - 510),
                                    init_platform(70, 10, self.screen_width - 1370, self.screen_height - 380),
                                    init_platform(100, 10, self.screen_width - 690, self.screen_height - 510),
                                    init_platform(70, 10, self.screen_width - 870, self.screen_height - 380),
                                    init_platform(100, 10, self.screen_width - 1250, self.screen_height - 470),
                                    init_platform(100, 10, self.screen_width - 1400, self.screen_height - 670),
                                    init_platform(100, 10, self.screen_width - 900, self.screen_height - 670),
                                    init_platform(100, 10, self.screen_width - 1050, self.screen_height - 470),
                                    init_platform(100, 10, self.screen_width - 1820, self.screen_height - 630),
                                    init_platform(100, 10, self.screen_width - 470, self.screen_height - 680),
                                    init_platform(100, 10, self.screen_width - 1145, self.screen_height - 730),
                                    init_platform(50, 10, self.screen_width - 1245, self.screen_height - 710),
                                    init_platform(50, 10, self.screen_width - 995, self.screen_height - 710),
                                    init_platform(screen_width, 160, 0, INFO.current_h - 160, 'darkred'),
                                    init_platform(screen_width, 1, 0, -2)]
        self.communist_coat_of_arms_surf_1, self.communist_coat_of_arms_rect_1 = init_symbol('coat_of_arms',
                                                                                             'communist_icon',
                                                                                             (42, 54),
                                                                                             self.screen_width - 1220,
                                                                                             self.screen_height - 530)
        self.communist_coat_of_arms_surf_2, self.communist_coat_of_arms_rect_2 = init_symbol('coat_of_arms',
                                                                                             'communist_icon',
                                                                                             (42, 54),
                                                                                             self.screen_width - 1020,
                                                                                             self.screen_height - 530)
        self.communist_flag_surf_1, self.communist_flag_rect_1 = init_symbol('flag', 'communist_icon', (54, 61),
                                                                             self.screen_width - 1120,
                                                                             self.screen_height - 375)
        self.communist_anthem_surf_1, self.communist_anthem_rect_1 = init_symbol('anthem', 'anthem_icon', (64, 60),
                                                                                 self.screen_width - 1570,
                                                                                 self.screen_height - 580)
        self.communist_anthem_surf_2, self.communist_anthem_rect_2 = init_symbol('anthem', 'anthem_icon', (64, 60),
                                                                                 self.screen_width - 1380,
                                                                                 self.screen_height - 740)
        self.communist_anthem_surf_3, self.communist_anthem_rect_3 = init_symbol('anthem', 'anthem_icon', (64, 60),
                                                                                 self.screen_width - 880,
                                                                                 self.screen_height - 740)
        self.communist_anthem_surf_4, self.communist_anthem_rect_4 = init_symbol('anthem', 'anthem_icon', (64, 60),
                                                                                 self.screen_width - 670,
                                                                                 self.screen_height - 580)
        self.communist_question_surf_1, self.communist_question_rect_1 = init_symbol('question', 'icon', (48, 87),
                                                                                     self.screen_width - 1795,
                                                                                     self.screen_height - 720)
        self.communist_question_surf_2, self.communist_question_rect_2 = init_symbol('question', 'icon', (48, 87),
                                                                                     self.screen_width - 445,
                                                                                     self.screen_height - 770)
        self.communist_question_surf_3, self.communist_question_rect_3 = init_symbol('question', 'icon', (48, 87),
                                                                                     self.screen_width - 1120,
                                                                                     self.screen_height - 820)
        self.communist_infoboxes = {
            'coat_of_arms_1': InfoBox(screen, screen_width, screen_height, player, self.communist_coat_of_arms_rect_1,
                                      thing=init_symbol(symbol='coat_of_arms', variety='dimitrov', size=(), x=15, y=15),
                                      message=self.communist_info[0].strip('\n')),
            'coat_of_arms_2': InfoBox(screen, screen_width, screen_height, player, self.communist_coat_of_arms_rect_2,
                                      thing=init_symbol(symbol='coat_of_arms', variety='zhivkov', size=(), x=15, y=15),
                                      message=self.communist_info[1].strip('\n')),
            'flag_1': InfoBox(screen, screen_width, screen_height, player, self.communist_flag_rect_1,
                              thing=init_symbol(symbol='flag', variety='dimitrov', size=(384, 231), x=15, y=15),
                              message=self.communist_info[2].strip('\n')),
            'anthem_1': InfoBox(screen, screen_width, screen_height, player, self.communist_anthem_rect_1,
                                category='with_button', button_text='Републико наша здравей', tune=pygame.mixer.Sound(
                    os.path.join('assets', 'anthems', 'republico_nasha_zdravei.mp3')),
                                current_bg_music=self.communist_music, message=self.communist_info[3].strip('\n')),
            'anthem_2': InfoBox(screen, screen_width, screen_height, player, self.communist_anthem_rect_2,
                                category='with_button', button_text='Земя на герои',
                                tune=pygame.mixer.Sound(os.path.join('assets', 'anthems', 'zemia_na_geroi.mp3')),
                                current_bg_music=self.communist_music, message=self.communist_info[4].strip('\n')),
            'anthem_3': InfoBox(screen, screen_width, screen_height, player, self.communist_anthem_rect_3,
                                category='with_button', button_text='Мила родино(1964-1989)',
                                tune=pygame.mixer.Sound(os.path.join('assets', 'anthems', 'mila_rodino_zhivkov.mp3')),
                                current_bg_music=self.communist_music, message=self.communist_info[5].strip('\n')),
            'anthem_4': InfoBox(screen, screen_width, screen_height, player, self.communist_anthem_rect_4,
                                category='with_button', button_text='Мила родино',
                                tune=pygame.mixer.Sound(os.path.join('assets', 'anthems', 'mila_rodino.mp3')),
                                current_bg_music=self.communist_music, message=self.communist_info[6].strip('\n')),
            'question_1': InfoBox(screen, screen_width, screen_height, player, self.communist_question_rect_1,
                                  thing=init_symbol(symbol='portrait', variety='georgi_jagarov', size=(195, 296),
                                                    x=15, y=15),
                                  category='question', message=self.communist_info[7].strip('\n'),
                                  answers=['А) Георги Димитров', 'Б) Тодор Живков', 'В) Вълко Червенков'],
                                  correct_answer=2),
            'question_2': InfoBox(screen, screen_width, screen_height, player, self.communist_question_rect_2,
                                  thing=init_symbol(symbol='coat_of_arms', variety='dimitrov', size=(), x=15, y=15),
                                  category='question', message=self.communist_info[8].strip('\n'),
                                  answers=['А) Живковската', 'Б) Търновската', 'В) Димитровската'], correct_answer=3),
            'question_3': InfoBox(screen, screen_width, screen_height, player, self.communist_question_rect_3,
                                  thing=init_symbol(symbol='flag', variety='zhivkov', size=(384, 231), x=15, y=15),
                                  category='question', message=self.communist_info[9].strip('\n'),
                                  answers=['А) 12 юни 1967г', 'Б) 4 декември 1947г', 'В) 9 септември 1944г'],
                                  correct_answer=1)}

    def level_3_draw(self, screen: pygame.Surface, player: Player, victory: bool):
        screen.fill('#BAAB98')
        screen.blit(self.communist_coat_of_arms_surf_1, self.communist_coat_of_arms_rect_1)
        screen.blit(self.communist_coat_of_arms_surf_2, self.communist_coat_of_arms_rect_2)
        screen.blit(self.communist_flag_surf_1, self.communist_flag_rect_1)
        screen.blit(self.communist_anthem_surf_1, self.communist_anthem_rect_1)
        screen.blit(self.communist_anthem_surf_2, self.communist_anthem_rect_2)
        screen.blit(self.communist_anthem_surf_3, self.communist_anthem_rect_3)
        screen.blit(self.communist_anthem_surf_4, self.communist_anthem_rect_4)
        screen.blit(self.communist_question_surf_1, self.communist_question_rect_1)
        screen.blit(self.communist_question_surf_2, self.communist_question_rect_2)
        screen.blit(self.communist_question_surf_3, self.communist_question_rect_3)
        for platform in self.communist_platforms:
            screen.blit(platform[0], platform[2])
        screen.blit(self.door_surf, self.door_rect)
        if victory:
            screen.blit(self.victory_door_surf, self.victory_door_rect)
        screen.blit(player.image, player.rect)


class InfoBox:
    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int, player: Player,
                 main_object_rect: pygame.rect, thing: tuple = '', category: str = '', tune: pygame.mixer.Sound = '',
                 current_bg_music: pygame.mixer.Sound = '', button_text: str = 'play', message: str = '',
                 answers: list[str, str, str] = (), correct_answer=1):
        self.type = category
        if self.type == 'with_button':
            self.is_pressed = False
            self.is_playing = False
            self.is_not_playing = True
            self.tune = tune
            self.current_bg_music = current_bg_music
        elif self.type == 'question_with_button':
            self.is_pressed = False
            self.is_playing = False
            self.is_not_playing = True
            self.tune = tune
            self.current_bg_music = current_bg_music
            self.correct = pygame.transform.rotozoom(
                pygame.image.load(os.path.join('assets', 'gallery', 'true.png')).convert_alpha(), 0, 1)
            self.incorrect = pygame.transform.rotozoom(
                pygame.image.load(os.path.join('assets', 'gallery', 'false.png')).convert_alpha(), 0, 1)
            self.is_correct = None
        else:
            if self.type == 'question':
                self.correct = pygame.transform.rotozoom(
                    pygame.image.load(os.path.join('assets', 'gallery', 'true.png')).convert_alpha(), 0, 1)
                self.incorrect = pygame.transform.rotozoom(
                    pygame.image.load(os.path.join('assets', 'gallery', 'false.png')).convert_alpha(), 0, 1)
                self.is_correct = None
            self.image_surf, self.image_rect = thing
        font = pygame.font.Font(os.path.join('assets', 'fonts', 'NotoSerif-Bold.ttf'), 20)

        # transform text
        self.message = message.split(r'\n')
        self.message = [font.render(mess, True, '#704F27', '#BAAC9B') for mess in self.message]
        self.message_rect = []
        self.longest_text_index = 0
        self.h = 5
        if self.type == 'with_button':
            self.text_position((len(button_text) * 16) + 30, 5)
            self.info_surf = pygame.Surface(
                (self.message_rect[self.longest_text_index].width + (len(button_text) * 16) + 30, max(50, self.h) + 20))
        elif self.type == 'question_with_button':
            self.text_position((len(button_text) * 17) + 40, 5)
            self.info_surf = pygame.Surface((self.message_rect[self.longest_text_index].width + (
                    len(button_text) * 17) + 20, max(50, self.h) + 300))
        else:
            self.text_position(self.image_rect.width + 25, 5)
            if self.type == 'question':
                self.info_surf = pygame.Surface((self.message_rect[
                                                     self.longest_text_index].width + self.image_rect.width + 60,
                                                 max(self.image_rect.height, self.h) + 300))
            else:
                self.info_surf = pygame.Surface((self.message_rect[
                                                     self.longest_text_index].width + self.image_rect.width + 60,
                                                 max(self.image_rect.height, self.h) + 20))

        # create and blit to info_surf
        self.info_surf.fill('#BAAC9B')
        self.info_rect = self.info_surf.get_rect(
            topleft=(main_object_rect.right, main_object_rect.bottom - (main_object_rect.height // 2)))
        while self.info_rect.bottom > screen_height - player.map_ground[2].height:
            self.info_rect.bottom -= 100

        while self.info_rect.right > screen_width:
            self.info_rect.right -= 100

        while self.info_rect.left < 0:
            self.info_rect.left += 100

        while self.info_rect.top < 0:
            self.info_rect.top += 100

        match self.type:
            case 'with_button':
                button_x, button_y = self.info_rect.x + 15, self.info_rect.y + 15
                self.button = Button(master=screen, text=button_text, main_color='#DEBA96', hover_color='#CCA678',
                                     b_main_color='#C29763', b_hover_color='#A17D52', button_text_color='#9C6E36',
                                     button_font_size=25, width=120, height=50, position=(button_x, button_y),
                                     elevation=4)
            case 'question_with_button':
                button_x, button_y = self.info_rect.x + 15, self.info_rect.y + 15
                question_x, question_y = self.info_rect.x + 15, self.h + 220
                self.button = Button(master=screen, text=button_text, main_color='#DEBA96', hover_color='#CCA678',
                                     b_main_color='#C29763', b_hover_color='#A17D52', button_text_color='#9C6E36',
                                     button_font_size=25, width=120, height=50, position=(button_x, button_y),
                                     elevation=4)
                self.question = []
                for answer in answers:
                    question_y += 80
                    self.question.append(Button(master=screen, text=answer, main_color='#DEBA96', hover_color='#CCA678',
                                                b_main_color='#C29763', b_hover_color='#A17D52',
                                                button_text_color='#9C6E36', button_font_size=25, width=120, height=50,
                                                position=(question_x, question_y), elevation=4))
                self.correct_answer = correct_answer
            case 'question':
                question_x, question_y = self.info_rect.x + 15, self.info_rect.bottom - 20
                self.info_surf.blit(self.image_surf, self.image_rect)
                self.question = []
                answers.reverse()
                for answer in answers:
                    question_y -= 80
                    self.question.append(Button(master=screen, text=answer, main_color='#DEBA96', hover_color='#CCA678',
                                                b_main_color='#C29763', b_hover_color='#A17D52',
                                                button_text_color='#9C6E36', button_font_size=25, width=120, height=50,
                                                position=(question_x, question_y), elevation=4))
                self.correct_answer = correct_answer
                self.question.reverse()
            case '':
                self.info_surf.blit(self.image_surf, self.image_rect)

        [self.info_surf.blit(text_surf, text_rect) for text_surf, text_rect in zip(self.message, self.message_rect)]

    def text_position(self, x: int, y: int):
        for i, mess in enumerate(self.message):
            if self.type == 'with_button' or self.type == 'question_with_button':
                if self.h >= 50:
                    mess_rect = mess.get_rect(topleft=(20, y + self.h))
                else:
                    mess_rect = mess.get_rect(topleft=(x, y + self.h))
            else:
                if self.h >= self.image_rect.bottom:
                    mess_rect = mess.get_rect(topleft=(20, y + self.h))
                else:
                    mess_rect = mess.get_rect(topleft=(x, y + self.h))
            if self.message_rect and mess_rect.width > self.message_rect[self.longest_text_index].width:
                self.longest_text_index = i
            self.message_rect.append(mess_rect)
            self.h += 30

    def display_infobox(self, screen: pygame.Surface):
        screen.blit(self.info_surf, self.info_rect)
        pygame.draw.rect(screen, '#704F27', self.info_rect, 5, 10)
        if self.type == 'with_button' or self.type == 'question_with_button':
            self.button.draw()
            self.play_anthem()
        if self.type == 'question' or self.type == 'question_with_button':
            self.question_draw()
            if type(self.is_correct) is not bool:
                self.question_check()
            if self.type == 'question':
                if self.is_correct:
                    correct_rect = self.correct.get_rect(
                        center=(self.info_rect.width - 200, max(self.image_rect.height, self.h) + 150))
                    self.info_surf.blit(self.correct, correct_rect)
                elif self.is_correct is False:
                    incorrect_rect = self.incorrect.get_rect(
                        center=(self.info_rect.width - 200, max(self.image_rect.height, self.h) + 150))
                    self.info_surf.blit(self.incorrect, incorrect_rect)
            elif self.type == 'question_with_button':
                if self.is_correct:
                    correct_rect = self.correct.get_rect(center=(self.info_rect.width - 200, self.h + 150))
                    self.info_surf.blit(self.correct, correct_rect)
                elif self.is_correct is False:
                    incorrect_rect = self.incorrect.get_rect(center=(self.info_rect.width - 200, self.h + 150))
                    self.info_surf.blit(self.incorrect, incorrect_rect)

    def play_anthem(self):
        self.is_pressed = self.button.is_clicked()
        if self.is_pressed and self.is_not_playing:
            self.is_playing = True
        elif self.is_playing:
            self.current_bg_music.stop()
            self.tune.play(loops=-1)
            self.tune.set_volume(0.1)
            self.is_not_playing = False
            if self.is_pressed or (pygame.key.get_pressed()[pygame.K_e] or pygame.key.get_pressed()[pygame.K_RCTRL]):
                pygame.mixer.stop()
                self.is_playing = False
        elif not self.is_pressed:
            self.is_not_playing = True

    def question_check(self):
        correct_index = self.correct_answer - 1
        for i, button in enumerate(self.question):
            if button.is_clicked():
                if i == correct_index:
                    self.is_correct = True
                else:
                    self.is_correct = False

    def question_draw(self):
        for button in self.question:
            button.draw()


class Button:
    def __init__(self, master: pygame.Surface, text: str, width: int, height: int, position: tuple[int, int],
                 elevation: int, main_color='#045927', hover_color='#02401B', b_main_color='#03401C',
                 b_hover_color='#001F0D', button_text_color='#B69945', button_font_size=30):
        self.is_pressed = False
        self.elevation = elevation
        self.dynamic_elevation = elevation
        self.start_y_position = position[1]
        self.master = master
        self.x_position = position[0]

        self.main_color = main_color
        self.hover_color = hover_color
        self.b_main_color = b_main_color
        self.b_hover_color = b_hover_color

        self.width, self.height = width, height

        self.top_rect = pygame.Rect(position, (self.width, self.height))
        self.top_color = main_color

        button_font = pygame.font.Font(os.path.join('assets', 'fonts', 'NotoSerif-BoldItalic.ttf'), button_font_size)
        self.text_surf = button_font.render(text, True, button_text_color)
        self.text_rect = self.text_surf.get_rect(center=self.top_rect.center)
        self.top_rect.width = max(self.text_rect.width + 10, self.top_rect.width)

        self.bottom_rect = pygame.Rect(position, (self.top_rect.width, elevation))
        self.bottom_color = self.b_main_color

    def draw(self):
        self.top_rect.y = self.start_y_position - self.dynamic_elevation
        self.text_rect.center = self.top_rect.center

        self.bottom_rect.top = self.top_rect.top
        self.bottom_rect.height = self.top_rect.height + self.dynamic_elevation

        pygame.draw.rect(self.master, self.bottom_color, self.bottom_rect, border_radius=12)
        pygame.draw.rect(self.master, self.top_color, self.top_rect, border_radius=12)
        self.master.blit(self.text_surf, self.text_rect)

    def is_clicked(self):
        mouse_position = pygame.mouse.get_pos()
        left_mouse_button_is_clicked = pygame.mouse.get_pressed()[0]
        if self.top_rect.collidepoint(mouse_position):
            self.top_color = self.hover_color
            self.bottom_color = self.b_hover_color
            if left_mouse_button_is_clicked:
                self.dynamic_elevation = 0
                self.is_pressed = True

            elif self.is_pressed:
                self.dynamic_elevation = self.elevation
                self.is_pressed = False
                return True
        else:
            self.dynamic_elevation = self.elevation
            self.top_color = self.main_color
            self.bottom_color = self.b_main_color

        return False


def init_symbol(symbol: str, variety: str, size: tuple, x: int, y: int):
    if variety and symbol:
        if symbol == 'anthem' or symbol == 'portrait':
            image = pygame.image.load(os.path.join('assets', 'gallery', f'{variety}.png')).convert_alpha()
            if size:
                image = pygame.transform.scale(image, size)
            rect = image.get_rect(topleft=(x, y))
        elif symbol == 'question':
            image = pygame.image.load(os.path.join('assets', 'gallery', f'{symbol}_{variety}.png')).convert_alpha()
            if size:
                image = pygame.transform.scale(image, size)
            rect = image.get_rect(topleft=(x, y))
        else:
            image = pygame.image.load(os.path.join('assets', 'gallery', f'{variety}_{symbol}.png')).convert_alpha()
            if size:
                image = pygame.transform.scale(image, size)
            rect = image.get_rect(topleft=(x, y))
        return image, rect


def interact(screen: pygame.Surface, player: pygame.Rect, object_rect: pygame.Rect, info_boxes: dict,
             current_object: str):
    global is_opened, is_closed, displayed_object

    interaction = pygame.key.get_pressed()[pygame.K_e] or pygame.key.get_pressed()[pygame.K_RCTRL]
    if interaction and object_rect.colliderect(player) and is_closed:
        displayed_object = current_object
        is_opened = True
        return True
    elif is_opened and current_object == displayed_object:
        info_boxes[current_object].display_infobox(screen)
        is_closed = False
        if interaction:
            is_opened = False
        return True
    elif not interaction:
        is_closed = True
    return False


def init_platform(width: int, height: int, x: int, y: int, color='#4A360E'):
    platform = pygame.Surface((width, height))
    platform.fill(color)
    mask = pygame.mask.from_surface(platform)
    rect = platform.get_rect(topleft=(x, y))
    return platform, mask, rect


def enter_room(player: pygame.Rect, room_rect: pygame.Rect):
    interaction = pygame.key.get_pressed()[pygame.K_e] or pygame.key.get_pressed()[pygame.K_RCTRL]
    if interaction and room_rect.colliderect(player):
        return True
    return False


def init_room_objects(new_size: tuple[int, int], x: int, y: int, thing: str, category: str = None):
    surf, rect = None, None
    match thing:
        case 'house':
            surf = pygame.image.load(os.path.join('assets', 'gallery', f'{category}_{thing}.png')).convert_alpha()
            surf = pygame.transform.scale(surf, new_size)
            rect = surf.get_rect(midbottom=(x, y))
        case 'door':
            surf = pygame.image.load(os.path.join('assets', 'gallery', f'{thing}.png')).convert_alpha()
            surf = pygame.transform.scale(surf, new_size)
            rect = surf.get_rect(midbottom=(x, y))
        case 'victory_door':
            surf = pygame.image.load(os.path.join('assets', 'gallery', f'{thing}.png')).convert_alpha()
            surf = pygame.transform.scale(surf, new_size)
            rect = surf.get_rect(midbottom=(x, y))
    return surf, rect


def title_screen_build(screen: pygame.Surface, screen_width: int, screen_height: int):
    font = pygame.font.Font(os.path.join('assets', 'fonts', 'NotoSerif-BoldItalic.ttf'), 80)
    title = font.render('Български държавни символи', True, '#B69945')
    start_button = Button(screen, text='НАЧАЛО', width=400, height=100,
                          position=(screen_width - 600, screen_height - 700), button_font_size=40, elevation=4)
    credit_button = Button(screen, text='КРЕДИТИ', width=400, height=100,
                           position=(screen_width - 600, screen_height - 550), button_font_size=40, elevation=4)
    exit_button = Button(screen, text='ИЗХОД', width=400, height=100,
                         position=(screen_width - 600, screen_height - 400), button_font_size=40, elevation=4)
    title_screen_image = pygame.image.load(os.path.join('assets', 'gallery', 'title_screen_logo.png')).convert_alpha()
    title_screen_image = pygame.transform.rotozoom(title_screen_image, 0, screen_height * 0.0008)
    title_screen_music = pygame.mixer.Sound(os.path.join('assets', 'music', 'title_screen_music.mp3'))
    title_screen_music.set_volume(0.05)

    return title, start_button, credit_button, exit_button, title_screen_image, title_screen_music


def title_screen_update(screen: pygame.Surface, screen_width: int, screen_height: int, title: pygame.Surface,
                        start_button: Button, credit_button: Button, exit_button: Button,
                        title_screen_image: pygame.Surface, title_screen_music: pygame.mixer.Sound, first_time: bool):
    title_screen_draw(screen, title, start_button, credit_button, exit_button, title_screen_image)
    if not muted:
        title_screen_music.play()
    if start_button.is_clicked():
        first_time = True
        return 'map', first_time
    elif credit_button.is_clicked():
        return 'credit_screen', first_time
    elif exit_button.is_clicked():
        title_screen_music.fadeout(6000)
        fade(screen, screen_width, screen_height,
             lambda: title_screen_draw(screen, title, start_button, credit_button, exit_button, title_screen_image))
        return 'exit', first_time
    return 'title_screen', first_time


def title_screen_draw(screen: pygame.Surface, title: pygame.Surface, start_button: Button, credit_button: Button,
                      exit_button: Button, title_screen_image: pygame.Surface):
    screen.fill('#056E30')
    screen.blit(title, (INFO.current_w // 2 - 600, 50))
    screen.blit(title_screen_image, (350, 180))
    start_button.draw()
    credit_button.draw()
    exit_button.draw()


def credit_screen_build(screen: pygame.Surface, screen_width: int, screen_height: int):
    def coding_resources():
        h = 90
        coding_surf = pygame.Surface((screen_width, 470), pygame.SRCALPHA, 32)
        for used_resource in used_resources[:2]:
            coding_surf.blit(used_resource, (50, h))
            h += 50

        coding_surf.blit(python_logo, (500, h))
        h += 20
        coding_surf.blit(pygame_logo, (800, h))
        h -= 200
        coding_surf.blit(vscode_logo, (screen_width - 350, h))

        coding_rect = coding_surf.get_rect(bottomleft=(0, screen_height - 150))

        return coding_surf, coding_rect

    def info_resources():
        h = 0
        info_surf = pygame.Surface((screen_width, 380), pygame.SRCALPHA, 32)
        for used_resource in used_resources[2:4]:
            info_surf.blit(used_resource, (50, h))
            h += 50

        h += 20
        info_surf.blit(bgherald_logo, (500, h))
        h -= 60
        info_surf.blit(book, (screen_width - 300, h))

        info_rect = info_surf.get_rect(bottomleft=(0, screen_height - 150))

        return info_surf, info_rect

    def art_resources():
        h = 200
        art_surf = pygame.Surface((screen_width, 580), pygame.SRCALPHA, 32)
        for used_resource in used_resources[4:]:
            art_surf.blit(used_resource, (50, h))
            h += 50

        art_surf.blit(pixilart_logo, (700, h))
        h -= 350
        art_surf.blit(gimp_logo, (940, h))
        h += 200
        art_surf.blit(fl_studio_logo, (screen_width - 250, h))

        art_rect = art_surf.get_rect(bottomleft=(0, screen_height - 150))

        return art_surf, art_rect

    credit_font = pygame.font.Font(os.path.join('assets', 'fonts', 'NotoSerif-BoldItalic.ttf'), 70)
    big_font = pygame.font.Font(os.path.join('assets', 'fonts', 'NotoSerif-BoldItalic.ttf'), 50)
    font = pygame.font.Font(os.path.join('assets', 'fonts', 'NotoSerif-BoldItalic.ttf'), 40)

    credit_title = credit_font.render('КРЕДИТИ', True, '#B69945')
    authors_title = big_font.render('Автори, ученици от СПГЕ "Джон Атанасов" София-град:', True, '#B69945')
    authors = [font.render(name, True, '#B69945') for name in
               '    ● Виктор Лъчезаров Георгиев (0897675825) – Програмист, извличане\nи обработване на текстов, снимков и аудио материал\n'
               '    ● Росен Георгиев Райков (0888500846) – Музикант\n'
               '    ● Андреа Пламен Паламудова (0898604771) – Художник\n'
               '    ● Магдаленa Андреева Стаменова (0889339048) - Научен ръководител'.split('\n')]
    used_resources_title = big_font.render('Използвани ресурси:', True, '#B69945')
    used_resources = [font.render(used_resource, True, '#B69945') for used_resource in
                      '    ● Програмен език Python и библиотеката Pygame\n    ● Текстов редактор Visual Studio Code\n'
                      '    ● „История на българските държавни символи” на И. Войников\n    ● Снимков материал – '
                      'heraldika-bg.org\n    ● Създаване и обработване на sprit-ове\nи снимков материал – Pixilart и '
                      'GIMP\n    ● Създаване и обработване на музика – Fl studio'.split('\n')]
    back_button = Button(screen, text='НАЗАД', width=400, height=100, position=(50, screen_height - 200),
                         button_font_size=40, elevation=4)

    python_logo = pygame.image.load(os.path.join('assets', 'gallery', 'python_logo.png')).convert_alpha()
    python_logo = pygame.transform.rotozoom(python_logo, 0, 0.14)
    pygame_logo = pygame.image.load(os.path.join('assets', 'gallery', 'pygame_logo.png')).convert_alpha()
    pygame_logo = pygame.transform.rotozoom(pygame_logo, 0, 0.7)
    vscode_logo = pygame.image.load(os.path.join('assets', 'gallery', 'vscode_logo.png')).convert_alpha()
    vscode_logo = pygame.transform.rotozoom(vscode_logo, 0, 0.11)
    bgherald_logo = pygame.image.load(os.path.join('assets', 'gallery', 'bgherald_logo.png')).convert_alpha()
    bgherald_logo = pygame.transform.rotozoom(bgherald_logo, 0, 1)
    book = pygame.image.load(os.path.join('assets', 'gallery', 'book.png')).convert_alpha()
    book = pygame.transform.rotozoom(book, 0, 0.27)
    pixilart_logo = pygame.image.load(os.path.join('assets', 'gallery', 'pixilart_logo.png')).convert_alpha()
    pixilart_logo = pygame.transform.rotozoom(pixilart_logo, 0, 0.7)
    gimp_logo = pygame.image.load(os.path.join('assets', 'gallery', 'gimp_logo.png')).convert_alpha()
    gimp_logo = pygame.transform.rotozoom(gimp_logo, 0, 0.35)
    fl_studio_logo = pygame.image.load(os.path.join('assets', 'gallery', 'fl_studio_logo.png')).convert_alpha()
    fl_studio_logo = pygame.transform.rotozoom(fl_studio_logo, 0, 0.75)

    used_resources = [coding_resources(), info_resources(), art_resources()]

    return credit_title, authors_title, authors, used_resources_title, back_button, used_resources


def credit_screen_update(screen: pygame.Surface, screen_width: int, credit_title: pygame.Surface,
                         authors_title: pygame.Surface, authors: list, used_resources_title: pygame.Surface,
                         used_resources: list, used_resources_mode: int, back_button: Button, previous_mode: str,
                         transit=False):
    credit_screen_surf = pygame.Surface((screen_width, 600), pygame.SRCALPHA, 32)
    credit_title_rect = credit_title.get_rect(center=(screen_width / 2, 50))
    credit_screen_surf.blit(credit_title, credit_title_rect)
    h = 100
    credit_screen_surf.blit(authors_title, (50, h))
    h += 60
    for author in authors:
        credit_screen_surf.blit(author, (50, h))
        h += 50
    h += 70

    credit_screen_surf.blit(used_resources_title, (50, h))

    if transit:
        clock = pygame.time.Clock()
        while used_resources[used_resources_mode][1].x < screen_width:
            clock.tick(60)
            screen.fill('#056E30')
            used_resources[used_resources_mode][1].x += 20
            screen.blit(used_resources[used_resources_mode][0], used_resources[used_resources_mode][1])
            screen.blit(credit_screen_surf, (0, 0))
            back_button.draw()

            pygame.display.flip()
        next_mode = used_resources_mode + 1 if used_resources_mode + 1 < len(used_resources) else 0
        used_resources[next_mode][1].x = used_resources[used_resources_mode][1].x
        while used_resources[next_mode][1].x > 0:
            clock.tick(60)
            screen.fill('#056E30')
            used_resources[next_mode][1].x -= 20
            screen.blit(used_resources[next_mode][0], used_resources[next_mode][1])
            screen.blit(credit_screen_surf, (0, 0))
            back_button.draw()

            pygame.display.flip()
        used_resources[used_resources_mode][1].x = 0
    else:
        screen.blit(used_resources[used_resources_mode][0], used_resources[used_resources_mode][1])

    screen.blit(credit_screen_surf, (0, 0))

    back_button.draw()
    if back_button.is_clicked():
        return previous_mode, used_resources_mode
    return 'credit_screen', used_resources_mode


def game_menu_build(screen: pygame.Surface, screen_width: int, screen_height: int):
    main_font = pygame.font.Font(os.path.join('assets', 'fonts', 'NotoSerif-BoldItalic.ttf'), 100)
    sub_font = pygame.font.Font(os.path.join('assets', 'fonts', 'NotoSerif-Italic.ttf'), 80)
    menu_title = main_font.render('ПАУЗА', True, '#B69945')
    menu_sub_title = sub_font.render('Български държавни символи', True, '#B69945')
    menu_continue_button = Button(screen, text='ПРОДЪЛЖИ', width=400, height=100,
                                  position=(screen_width // 2 - 200, screen_height - 750), button_font_size=40,
                                  elevation=4)
    menu_back_to_start_button = Button(screen, text='КЪМ НАЧАЛОТО', width=400, height=100,
                                       position=(screen_width // 2 - 200, screen_height - 600), button_font_size=40,
                                       elevation=4)
    menu_exit_button = Button(screen, text='ИЗХОД', width=400, height=100,
                              position=(screen_width // 2 - 200, screen_height - 450), button_font_size=40, elevation=4)
    menu_images_left = [
        pygame.transform.rotozoom(pygame.image.load(os.path.join('assets', 'gallery', f'{path}.png')).convert_alpha(),
                                  0, screen_height * 0.0013) for path in
        'dimitrov_coat_of_arms\n1879-1881_coat_of_arms\nferdinant_coat_of_arms'.split('\n')]
    menu_images_right = [
        pygame.transform.rotozoom(pygame.image.load(os.path.join('assets', 'gallery', f'{path}.png')).convert_alpha(),
                                  0, screen_height * 0.0013) for path in
        'boris3_coat_of_arms\nalexander_coat_of_arms\nzhivkov_coat_of_arms'.split('\n')]

    return menu_title, menu_sub_title, menu_continue_button, menu_back_to_start_button, menu_exit_button, \
        menu_images_left, menu_images_right


def game_menu_update(screen: pygame.Surface, screen_width: int, screen_height: int,
                     menu_title: pygame.Surface, menu_sub_title: pygame.Surface, menu_continue_button: Button,
                     menu_back_to_start_button: Button, menu_exit_button: Button, menu_images_left: list,
                     menu_images_right: list, previous_mode: str):
    draw_game_menu(screen, screen_width, screen_height, menu_title, menu_sub_title, menu_continue_button,
                   menu_back_to_start_button, menu_exit_button, menu_images_left, menu_images_right)
    if menu_continue_button.is_clicked():
        return previous_mode
    elif menu_back_to_start_button.is_clicked():
        pygame.mixer.stop()
        fade(screen, screen_width, screen_height,
             lambda: draw_game_menu(screen, screen_width, screen_height, menu_title, menu_sub_title,
                                    menu_continue_button, menu_back_to_start_button, menu_exit_button, menu_images_left,
                                    menu_images_right))
        player = Player(screen_width, screen_height)
        levels = Levels(screen, screen_width, screen_height, player)
        return 'title_screen', player, levels
    elif menu_exit_button.is_clicked():
        fade(screen, screen_width, screen_height,
             lambda: draw_game_menu(screen, screen_width, screen_height, menu_title, menu_sub_title,
                                    menu_continue_button, menu_back_to_start_button, menu_exit_button, menu_images_left,
                                    menu_images_right))
        return 'exit'
    return 'game_menu'


def draw_game_menu(screen: pygame.Surface, screen_width: int, screen_height: int, menu_title: pygame.Surface,
                   menu_sub_title: pygame.Surface, menu_continue_button: Button, menu_back_to_start_button: Button,
                   menu_exit_button: Button, menu_images_left: list, menu_images_right: list):
    screen.fill('#056E30')
    screen.blit(menu_title, (screen_width // 2 - 180, 50))
    screen.blit(menu_sub_title, (screen_width // 2 - 600, screen_height - 200))
    h = 10
    for i, (image_left, image_right) in enumerate(zip(menu_images_left, menu_images_right)):
        if i == 1:
            screen.blit(image_left, (screen_width // 2 - 600, h))
            screen.blit(image_right, (screen_width // 2 + 300, h))
        else:
            screen.blit(image_left, (30, h))
            screen.blit(image_right, (screen_width - 400, h)) if i == 0 else (
                screen.blit(image_right, (screen_width - 300, h)))

        h += screen_height / 3.5

    menu_continue_button.draw()
    menu_back_to_start_button.draw()
    menu_exit_button.draw()


def victory_screen_build(screen: pygame.Surface, screen_width: int, screen_height: int):
    main_font = pygame.font.Font(os.path.join('assets', 'fonts', 'NotoSerif-BoldItalic.ttf'), 100)
    sub_font = pygame.font.Font(os.path.join('assets', 'fonts', 'NotoSerif-Italic.ttf'), 80)
    victory_title = main_font.render('ТИ ПОБЕДИ', True, '#B69945')
    victory_sub_title = sub_font.render('Български държавни символи', True, '#B69945')
    victory_continue_button = Button(screen, text='ПРОДЪЛЖИ', width=400, height=100,
                                     position=(screen_width // 2 - 200, screen_height - 750), button_font_size=40,
                                     elevation=4)
    victory_credit_button = Button(screen, text='КРЕДИТИ', width=400, height=100,
                                   position=(screen_width // 2 - 200, screen_height - 600), button_font_size=40,
                                   elevation=4)
    victory_back_to_start_button = Button(screen, text='КЪМ НАЧАЛОТО', width=400, height=100,
                                          position=(screen_width // 2 - 200, screen_height - 450), button_font_size=40,
                                          elevation=4)
    flag_cup = pygame.transform.scale(pygame.image.load(os.path.join('assets', 'gallery', 'f_cup.png')).convert_alpha(),
                                      (screen_width // 328 * 100, screen_height // 460 * 300))
    coat_of_arms_cup = pygame.transform.scale(
        pygame.image.load(os.path.join('assets', 'gallery', 's_cup.png')).convert_alpha(),
        (screen_width // 323 * 100, screen_height // 452 * 300))
    victory_screen_music = pygame.mixer.Sound(os.path.join('assets', 'music', 'shumi_marica.mp3'))
    victory_screen_music.set_volume(0.05)

    return victory_title, victory_sub_title, victory_continue_button, victory_back_to_start_button, \
        victory_credit_button, flag_cup, coat_of_arms_cup, victory_screen_music


def victory_screen_update(screen: pygame.Surface, screen_width: int, screen_height: int, player: Player,
                          victory_title: pygame.Surface, victory_sub_title: pygame.Surface,
                          victory_continue_button: Button, victory_back_to_start_button: Button,
                          victory_credit_button: Button, flag_cup: pygame.Surface, coat_of_arms_cup: pygame.Surface,
                          victory_screen_music: pygame.mixer.Sound):
    draw_victory_screen(screen, screen_width, screen_height, victory_title, victory_sub_title, victory_continue_button,
                        victory_back_to_start_button, victory_credit_button, flag_cup, coat_of_arms_cup)
    if not muted:
        victory_screen_music.play()

    if victory_continue_button.is_clicked():
        player.x = 10
        victory_screen_music.fadeout(3000)
        fade(screen, screen_width, screen_height,
             lambda: draw_victory_screen(screen, screen_width, screen_height, victory_title, victory_sub_title,
                                         victory_continue_button, victory_back_to_start_button, victory_credit_button,
                                         flag_cup, coat_of_arms_cup))
        return 'map'
    elif victory_back_to_start_button.is_clicked():
        victory_screen_music.fadeout(3000)
        fade(screen, screen_width, screen_height,
             lambda: draw_victory_screen(screen, screen_width, screen_height, victory_title, victory_sub_title,
                                         victory_continue_button, victory_back_to_start_button, victory_credit_button,
                                         flag_cup, coat_of_arms_cup))
        player = Player(screen_width, screen_height)
        levels = Levels(screen, screen_width, screen_height, player)
        return 'title_screen', player, levels
    elif victory_credit_button.is_clicked():
        return 'credit_screen'
    return 'victory_screen'


def draw_victory_screen(screen: pygame.Surface, screen_width: int, screen_height: int, victory_title: pygame.Surface,
                        victory_sub_title: pygame.Surface, victory_continue_button: Button,
                        victory_back_to_start_button: Button, victory_credit_button: Button, flag_cup: pygame.Surface,
                        coat_of_arms_cup: pygame.Surface):
    screen.fill('#056E30')
    screen.blit(victory_title, (screen_width // 2 - 300, 50))
    screen.blit(victory_sub_title, (screen_width // 2 - 600, screen_height - 200))
    screen.blit(flag_cup, (screen_width // 2 - 700, 200))
    screen.blit(coat_of_arms_cup, (screen_width // 2 + 300, 200))

    victory_continue_button.draw()
    victory_credit_button.draw()
    victory_back_to_start_button.draw()


def draw_map(screen: pygame.Surface, player: Player, uprising_house_surf: pygame.Surface,
             uprising_house_rect: pygame.Rect, tsar_house_surf: pygame.Surface, tsar_house_rect: pygame.Rect,
             communist_house_surf: pygame.Surface, communist_house_rect: pygame.Rect):
    screen.fill('#A3E5F0')
    screen.blit(uprising_house_surf, uprising_house_rect)
    screen.blit(tsar_house_surf, tsar_house_rect)
    screen.blit(communist_house_surf, communist_house_rect)
    screen.blit(player.image, player.rect)
    screen.blit(player.map_ground[0], player.map_ground[2])


def fade(screen: pygame.Surface, width: int, height: int, func: Callable, start=0, end=270, step=1, color='#000000'):
    fading = pygame.Surface((width, height))
    fading.fill(color)
    for alpha in range(start, end, step):
        fading.set_alpha(alpha)
        func()
        screen.blit(fading, (0, 0))
        pygame.display.update()
        if alpha % 2 == 0:
            pygame.time.delay(1)


def main():
    global muted

    screen_width, screen_height = INFO.current_w, INFO.current_h
    SCREEN_WIDTH, SCREEN_HEIGHT = screen_width, screen_height

    mode = 'title_screen'

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
    pygame.display.set_caption('Български държавни символи')
    pygame.display.set_icon(pygame.image.load(os.path.join('assets', 'gallery', 'title_screen_logo.png')))
    clock = pygame.time.Clock()

    player = Player(SCREEN_WIDTH, SCREEN_HEIGHT)

    uprising_house_surf, uprising_house_rect = init_room_objects((255, 171), 250, player.map_ground[2].y, 'house',
                                                                 'uprising')
    tsar_house_surf, tsar_house_rect = init_room_objects((528, 281), 700, player.map_ground[2].y, 'house', 'tsar')
    communist_house_surf, communist_house_rect = init_room_objects((473, 286), 1270, player.map_ground[2].y, 'house',
                                                                   'communist')

    title, start_button, credit_button, exit_button, title_screen_image, title_screen_music = \
        title_screen_build(screen, SCREEN_WIDTH, SCREEN_HEIGHT)
    credit_title, authors_title, authors, used_resources_title, back_button, used_resources = \
        credit_screen_build(screen, SCREEN_WIDTH, SCREEN_HEIGHT)
    used_resources_mode, used_resources_timer = 0, 0
    menu_title, menu_sub_title, menu_continue_button, menu_back_to_start_button, menu_exit_button, menu_images_left, \
        menu_images_right = game_menu_build(screen, SCREEN_WIDTH, SCREEN_HEIGHT)
    victory_title, victory_sub_title, victory_continue_button, victory_back_to_start_button, victory_credit_button, \
        flag_cup, coat_of_arms_cup, victory_screen_music = victory_screen_build(screen, SCREEN_WIDTH, SCREEN_HEIGHT)

    user_answers = []
    threshold = 7
    victory = False

    colliding = False
    previous_mode = None
    first_time = True

    levels = Levels(screen, SCREEN_WIDTH, SCREEN_HEIGHT, player)

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key == pygame.K_m:
                    pygame.mixer.stop()
                    muted = True

        match mode:
            case 'title_screen':
                mode = title_screen_update(screen, SCREEN_WIDTH, SCREEN_HEIGHT, title, start_button, credit_button,
                                           exit_button, title_screen_image, title_screen_music, first_time)
                if mode[0] == 'credit_screen':
                    previous_mode = 'title_screen'
                mode, first_time = mode

            case 'credit_screen':
                screen.fill('#056E30')
                used_resources_timer += 1
                if used_resources_timer == 420:
                    mode, used_resources_mode = credit_screen_update(screen, SCREEN_WIDTH, credit_title, authors_title,
                                                                     authors, used_resources_title, used_resources,
                                                                     used_resources_mode, back_button, previous_mode,
                                                                     True)
                    used_resources_mode += 1
                    if used_resources_mode == 3:
                        used_resources_mode = 0
                    used_resources_timer = 0
                    continue
                mode, used_resources_mode = credit_screen_update(screen, SCREEN_WIDTH, credit_title, authors_title,
                                                                 authors, used_resources_title, used_resources,
                                                                 used_resources_mode, back_button, previous_mode)

            case 'game_menu':
                if muted:
                    pygame.mixer.stop()

                mode = game_menu_update(screen, SCREEN_WIDTH, SCREEN_HEIGHT, menu_title, menu_sub_title,
                                        menu_continue_button, menu_back_to_start_button, menu_exit_button,
                                        menu_images_left, menu_images_right, previous_mode)
                if type(mode) is tuple:
                    mode, player, level = mode

            case 'victory_screen':
                mode = victory_screen_update(screen, SCREEN_WIDTH, SCREEN_HEIGHT, player, victory_title,
                                             victory_sub_title, victory_continue_button, victory_back_to_start_button,
                                             victory_credit_button, flag_cup, coat_of_arms_cup, victory_screen_music)
                if type(mode) is tuple:
                    mode, player, level = mode
                if mode == 'credit_screen':
                    previous_mode = 'victory_screen'

            case 'map':
                if first_time:
                    fade(screen, SCREEN_WIDTH, SCREEN_HEIGHT,
                         lambda: draw_map(screen, player, uprising_house_surf, uprising_house_rect, tsar_house_surf,
                                          tsar_house_rect, communist_house_surf, communist_house_rect), start=270,
                         end=0,
                         step=-1)
                    first_time = False

                if not muted:
                    title_screen_music.play(loops=-1)

                draw_map(screen, player, uprising_house_surf, uprising_house_rect, tsar_house_surf, tsar_house_rect,
                         communist_house_surf, communist_house_rect)
                player.map_update()
                results = [enter_room(player, rect) for rect in
                           (uprising_house_rect, tsar_house_rect, communist_house_rect)]
                for level, result in enumerate(results, 1):
                    if result:
                        title_screen_music.fadeout(2700)
                        fade(screen, SCREEN_WIDTH, SCREEN_HEIGHT,
                             lambda: draw_map(screen, player, uprising_house_surf, uprising_house_rect, tsar_house_surf,
                                              tsar_house_rect, communist_house_surf, communist_house_rect))
                        first_time = True
                        mode = 'level_' + str(level)

                if pygame.key.get_pressed()[pygame.K_p]:
                    previous_mode = mode
                    mode = 'game_menu'

            # in room actions
            case 'level_1':
                if first_time:
                    player.rect.x, player.rect.y = 20, player.map_ground[2].y - player.rect.height
                    fade(screen, SCREEN_WIDTH, SCREEN_HEIGHT, lambda: levels.level_1_draw(screen, player), start=270,
                         end=0, step=-1)
                    first_time = False
                    pygame.mixer.stop()
                mode, colliding, first_time = levels.level_1(screen, SCREEN_WIDTH, SCREEN_HEIGHT, player, mode,
                                                             colliding, first_time, uprising_house_rect)
                if pygame.key.get_pressed()[pygame.K_p]:
                    previous_mode = mode
                    mode = 'game_menu'

            case 'level_2':
                if first_time:
                    player.rect.x, player.rect.y = 20, player.map_ground[2].y - player.rect.height
                    fade(screen, SCREEN_WIDTH, SCREEN_HEIGHT, lambda: levels.level_2_draw(screen, player), start=270,
                         end=0, step=-1)
                    first_time = False
                    pygame.mixer.stop()
                mode, colliding, first_time = levels.level_2(screen, SCREEN_WIDTH, SCREEN_HEIGHT, player, mode,
                                                             colliding, first_time, tsar_house_rect)
                if pygame.key.get_pressed()[pygame.K_p]:
                    previous_mode = mode
                    mode = 'game_menu'

            case 'level_3':
                if first_time:
                    player.rect.x, player.rect.y = 20, player.map_ground[2].y - player.rect.height
                    fade(screen, SCREEN_WIDTH, SCREEN_HEIGHT, lambda: levels.level_3_draw(screen, player, victory),
                         start=270, end=0, step=-1)
                    first_time = False
                    pygame.mixer.stop()
                mode, colliding, first_time = levels.level_3(screen, SCREEN_WIDTH, SCREEN_HEIGHT, player, mode,
                                                             colliding, first_time, communist_house_rect, victory)
                if pygame.key.get_pressed()[pygame.K_p]:
                    previous_mode = mode
                    mode = 'game_menu'

            case 'exit':
                running = False

        if not victory:
            for dictionary in [levels.uprising_infoboxes, levels.tsar_infoboxes, levels.communist_infoboxes]:
                for key, infobox in dictionary.items():
                    if 'question' in key:
                        user_answers.append(infobox.is_correct)
            if len([boolean for boolean in user_answers if boolean]) >= threshold and None not in user_answers:
                victory = True
        user_answers = []

        pygame.display.update()
    pygame.quit()


if __name__ == '__main__':
    print("Copyright (c) 2023 Victor L. Georgiev.\nAll Rights Reserved.")
    main()
