import pygame
import math
from abc import ABC, abstractmethod

# CONSTANTS + INITIALISATION ===================================================

WHITE = (255,255,255)
RED = (255,0,0)
GREEN = (0,255,0)
YELLOW = (255,255,0)
MENU_GREY = (145, 145, 145)
PAUSE_BLACK = (0, 0, 0, 175)
BLACK = (0,0,0)
PLAYER_BLUE = (0, 110, 255)

WIDTH = 960
HEIGHT = 540
ARENA_BOUNDARY_WIDTH = 680

GLOBAL_ENEMY_POS = {}

path = "src/assets/"

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
screen.fill(WHITE)
pygame.display.set_caption("Dieflow")

# CLASSES ===============================================================

# TODO: Make the enemy and enemy bullets rotate depending on direction.

# TODO: Determine level indicators, and enemy wave spawning system

class Entity():
    @abstractmethod
    def update():
        pass

    @abstractmethod
    def draw():
        pass


class Enemy(Entity):
    def __init__(self,player, pos, accel, friction, max_speed, player_knockback, health, damage, image):
        self.player = player

        self.vel = pygame.Vector2(0,0)
        self.pos = pos
        self.accel = accel
        self.friction = friction
        self.max_speed = max_speed
        
        self.player_knockback = player_knockback

        self.health = health
        self.damage = damage
        self.image = pygame.image.load(path+image).convert_alpha()
        self.image = pygame.transform.scale(self.image, (25,25))
        
    def collide(self):
        # Do knockback / offset on each other so they do not overlap
        for enemy in GLOBAL_ENEMY_POS:
            if self.hitbox != enemy.hitbox and self.hitbox.colliderect(enemy.hitbox):
                offset = self.pos - enemy.pos
                if offset.length() > 0:
                    offset = offset.normalize()
                self.vel += offset * 2

        if self.player.hitbox.colliderect(self.hitbox):
            self.player.health -= self.damage
            self.player.vel += self.player_knockback * self.vel   # This is genuinely the most beautiful knockback ever
            return True
    
    def movement_maintenance(self):
        self.vel *= self.friction
        self.pos += self.vel

        # Resize velocity vector so that it does not exceed max_speed when diagonal
        if self.vel.length() > self.max_speed:
            self.vel.scale_to_length(self.max_speed)
        
        self.hitbox.center = self.pos

        self.pos.x = max(12.5, min(ARENA_BOUNDARY_WIDTH - 12.5, self.pos.x))
        self.pos.y = max(12.5, min(HEIGHT - 12.5, self.pos.y))

    @abstractmethod
    def attack(self):
        pass    

    def take_damage(self,damage):
        self.health -= damage

    def check_death(self):
        if self.health <= 0:
            return True
    
    def draw(self,surface):
        rect = self.image.get_rect(center=self.pos)
        surface.blit(self.image, rect)


class Square(Enemy):
    # Inherit these parameters from Enemy
    def __init__(self, player, pos, accel=0.2, friction=0.9, max_speed=1.5, player_knockback=5, health=20, damage=5, image="square.png"):
        super().__init__(player, pos, accel, friction, max_speed, player_knockback, health, damage, image)
        self.hitbox = pygame.Rect(self.pos[0], self.pos[1], 25, 25)
          
    
    def update(self):
        # Get the direction aiming at the player
        direction = self.player.pos - self.pos
        direction = direction.normalize()     # Makes direction magnitude 1, this is for consistent velocity 
        
        # Similar movement processing like the Player class
        self.vel += direction * self.accel
        
        self.movement_maintenance()
 

class Dome(Enemy):
    # Inherit these parameters from Enemy
    def __init__(self, player, pos, accel=1, friction=0.9, max_speed=2, player_knockback=5, health=40, damage=5, image="dome.png"):
        super().__init__(player, pos, accel, friction, max_speed, player_knockback, health, damage, image)
        self.hitbox = pygame.Rect(self.pos[0], self.pos[1], 25, 25)
    
    def update(self):
        # Get the direction aiming at the player
        direction = self.player.pos - self.pos
        direction = direction.normalize()     # Makes direction magnitude 1, this is for consistent velocity 
        
        # Gets the perpendicular vector, this makes it spin around
        orbit = pygame.Vector2(-direction.y, direction.x)
        self.vel += orbit * self.accel
        
        self.movement_maintenance()


class PauseScreen():
    def __init__(self):
        self.colour = PAUSE_BLACK
        self.rect = pygame.Rect(0,0,ARENA_BOUNDARY_WIDTH, HEIGHT)

        # Temp surface is created so the screen can have a slight transparent opacity
        self.temp_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

    def draw(self,surface):
        pygame.draw.rect(self.temp_surface, self.colour, self.rect)
        surface.blit(self.temp_surface,self.rect)

        # Put "paused" text on top
        font = pygame.font.Font(None, 100)
        text_surface = font.render("PAUSED", True, (255,255,255))
        surface.blit(text_surface, (210,220))


class UpgradeScreen(Entity):
    def __init__(self, player, points=30):
        ARENA_WIDTH = WIDTH-ARENA_BOUNDARY_WIDTH
        self.arena_area = pygame.Rect(ARENA_BOUNDARY_WIDTH, 0, ARENA_WIDTH, HEIGHT)

        self.bg_colour = MENU_GREY
        self.upgrade_screen_image = pygame.image.load(path+"upgrade_screen.png").convert_alpha()
        self.upgrade_levels_image = pygame.image.load(path+"numbers.png").convert_alpha()
        self.points = points

        self.player = player
        self.shot_amount_pos = pygame.Rect(707,154,32,32)
        self.bullet_speed_pos = pygame.Rect(707,218,32,32)
        self.shot_delay_pos = pygame.Rect(707,282,32,32)
        self.shot_damage_pos = pygame.Rect(707,346,32,32)
        self.max_speed_pos = pygame.Rect(707,410,32,32)
        self.defence_pos = pygame.Rect(707,474,32,32)

        # Storing upgrades and skill properties in dictionary w/ tuple to reduce repeat of code
        # Buttons reference: "NAME": (skill_level, rect, limit, upgrade)
        self.buttons = {
            "SHOT AMOUNT": (0, self.shot_amount_pos, 2, self.upgrade_shot_amount),
            "BULLET SPEED": (0, self.bullet_speed_pos, 2, self.upgrade_bullet_speed),
            "SHOT DELAY": (0, self.shot_delay_pos, 3, self.upgrade_shot_delay),
            "SHOT DAMAGE": (0, self.shot_damage_pos, 3, self.upgrade_shot_damage),
            "MAX SPEED": (0, self.max_speed_pos, 3, self.upgrade_max_speed),
            "DEFENCE": (0, self.defence_pos, 3, self.upgrade_defence),
        }
    
    # Verify if upgrade a skill if can be afforded based on amount of points
    def upgradeVerify(self, skill_level, upgrade_limit):
        if self.points >= skill_level+1 and skill_level < upgrade_limit:
            self.points -= skill_level+1
            skill_level += 1
            return skill_level
        return None            

    # Will upgade skill if corresponding '+' button is clicked
    def click(self, pos):
        for name, (skill_level, rect, upgrade_limit, upgrade) in self.buttons.items():
            if rect.collidepoint(pos):
                print(name, "CLICKED")
                new_level = self.upgradeVerify(skill_level, upgrade_limit)

                # Update self.buttons dict with new level
                if new_level is not None:
                    self.buttons[name] = (new_level, rect, upgrade_limit, upgrade)
                    upgrade()

        # Print testing
        print(self.points) 
        for name, (skill_level, __, __, __) in self.buttons.items():
            print(name, skill_level)

    # Some arbitrary values for placeholder, not in use rn
    def upgrade_shot_amount(self):
        self.player.shot_amount = self.buttons["SHOT AMOUNT"][0]
    
    def upgrade_bullet_speed(self):
        self.player.bullet_speed += 2

    def upgrade_shot_delay(self):
        self.player.shot_delay -= 50

    def upgrade_shot_damage(self):
        self.player.shot_damage += 10
    
    def upgrade_max_speed(self):
        self.player.accel += 0.05
        self.player.max_speed += 2
        
    def upgrade_defence(self):
        self.player.defence += 5

    # Empty, since the upgrade screen doesn't really move and respond to inputs other than mouse
    def update(self):
        pass

    def draw(self, surface):
        # DRAWING BG AND BLANK UPGRADES ===============================================
        pygame.draw.rect(surface, self.bg_colour, (ARENA_BOUNDARY_WIDTH,0,WIDTH-ARENA_BOUNDARY_WIDTH, HEIGHT))
        surface.blit(self.upgrade_screen_image, (695, 20))

        # DRAWING POINTS AMOUNT ===============================================
        font = pygame.font.Font(None, 35)
        text_surface = font.render(str(self.points), True, (0, 0, 0))
        surface.blit(text_surface, (900, 90))
        
        # DRAWING COLOURED UPGRADE LEVELS ===============================================
        # Reference for SHOT AMOUNT = 1: 96x32 size image from (0, 0) of the source image to (739, 155) on screen
        if self.buttons["SHOT AMOUNT"][0] == 1:
            surface.blit(self.upgrade_levels_image, (740, 153), (0, 0, 94, 32))
        elif self.buttons["SHOT AMOUNT"][0]==2:
            surface.blit(self.upgrade_levels_image, (740, 153), (0, 0, 192, 32))
        
        if self.buttons["BULLET SPEED"][0] == 1:
            surface.blit(self.upgrade_levels_image, (740, 216), (0, 31, 94, 32))
        elif self.buttons["BULLET SPEED"][0]==2:
            surface.blit(self.upgrade_levels_image, (740, 216), (0, 31, 192, 32))
        
        if self.buttons["SHOT DELAY"][0] == 1:
            surface.blit(self.upgrade_levels_image, (739, 280), (0, 63, 64, 29))
        elif self.buttons["SHOT DELAY"][0]==2:
            surface.blit(self.upgrade_levels_image, (739, 280), (0, 63, 128, 29))
        elif self.buttons["SHOT DELAY"][0]==3:
            surface.blit(self.upgrade_levels_image, (739, 280), (0, 63, 192, 29))
        
        if self.buttons["SHOT DAMAGE"][0] == 1:
            surface.blit(self.upgrade_levels_image, (739, 342), (0, 94, 64, 31))
        elif self.buttons["SHOT DAMAGE"][0]==2:
            surface.blit(self.upgrade_levels_image, (739, 342), (0, 94, 128, 31))
        elif self.buttons["SHOT DAMAGE"][0]==3:
            surface.blit(self.upgrade_levels_image, (739, 342), (0, 94, 192, 31))
        
        if self.buttons["MAX SPEED"][0] == 1:
            surface.blit(self.upgrade_levels_image, (739, 407), (0, 126, 64, 31))
        elif self.buttons["MAX SPEED"][0] == 2:
            surface.blit(self.upgrade_levels_image, (739, 407), (0, 126, 128, 31))
        elif self.buttons["MAX SPEED"][0] == 3:
            surface.blit(self.upgrade_levels_image, (739, 407), (0, 126, 192, 31))

        if self.buttons["DEFENCE"][0] == 1:
            surface.blit(self.upgrade_levels_image, (739, 471), (0, 158, 64, 31))
        elif self.buttons["DEFENCE"][0] == 2:
            surface.blit(self.upgrade_levels_image, (739, 471), (0, 158, 128, 31))
        elif self.buttons["DEFENCE"][0] == 3:
            surface.blit(self.upgrade_levels_image, (739, 471), (0, 158, 192, 31))


class HealthBar():
    def __init__(self, pos, max_health, curr_health, frame_width=30, frame_height=7,health_width=28,health_height=5):
        self.pos = pos
        self.max_health = max_health
        self.curr_health = curr_health

        # Graphic properties of the health bar
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.max_content_width = health_width
        self.content_width = health_width
        self.content_height = health_height
        self.colour = GREEN

        # Making rect for health bar frame and actual content bar
        self.health_bar_frame = pygame.Rect(pos[0], pos[1], self.frame_width, self.frame_height)
        self.health_bar_content = pygame.Rect(pos[0], pos[1], self.content_width, self.content_height)

    def update(self, health, pos):
        self.curr_health = health
        health_percent = self.curr_health/self.max_health
        self.content_width = round(self.max_content_width * health_percent)

        # Update the health bar and shifting its content bar to be in the right place 
        self.health_bar_frame.center = pos
        self.health_bar_content.topleft = pos - pygame.Vector2(self.frame_width//2-1,self.frame_height//2-1)
        self.health_bar_content.width = self.content_width  # Change the content bar width as a percentage of its max width

        # Change colour of content bar depending on health percent
        if health_percent >= 0.67:
            self.colour = GREEN
        elif health_percent >= 0.34:
            self.colour = YELLOW
        else:
            self.colour = RED
    
    def draw(self, surface):
        pygame.draw.rect(surface, BLACK, self.health_bar_frame)
        pygame.draw.rect(surface, self.colour, self.health_bar_content)


class PlayerBullet(Entity):
    def __init__(self, pos, direction, speed, shot_damage, radius=5, colour=BLACK):
        self.pos = pygame.Vector2(pos)
        self.speed = speed
        self.vel = pygame.Vector2(direction) *speed
        self.radius = radius
        self.colour = colour
        self.shot_damage = shot_damage

    def update(self):
        self.pos += self.vel
    
    def collide(self):
        for enemy in GLOBAL_ENEMY_POS:
            if GLOBAL_ENEMY_POS[enemy].collidepoint(self.pos):
                enemy.health -= self.shot_damage
                return True
    
    def draw(self, surface):
        pygame.draw.circle(surface, self.colour, self.pos, self.radius)
    
    def off_screen(self):
        return (self.pos.x < 0 or self.pos.x > ARENA_BOUNDARY_WIDTH-self.speed or 
                self.pos.y < 0 or self.pos.y > HEIGHT)

class EnemyBullet(PlayerBullet):
    def __init__(self, pos, direction, speed, shot_damage, image_path="arrow.png"):
        super().__init__(pos, direction, speed, shot_damage)
        self.image = pygame.image.load(path+image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (15, 15))

        self.rect = self.image.get_rect(center=self.pos)

    def update(self):
        super().update()    # Keep PlayerBullet movement
        self.rect.center = (self.pos.x, self.pos.y)   # Update rect position to follow pos
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)

class Player(Entity):
    def __init__(self, radius=10, thickness=1, accel=0.5, friction=0.9, level=1, health=50, heal_delay=2000, heal_per_sec=10,
                 shot_amount=0, bullet_speed=7, shot_delay=400, shot_damage=10, max_speed=6,defence=5):
        self.radius = radius
        self.fill = PLAYER_BLUE
        self.outline = BLACK
        self.thickness = thickness
        self.level = level   # Determine what this is used for

        # Movement parameters
        # We have velocity, not just speed. This is to ensure smooth sliding movement!
        self.vel = pygame.Vector2(0,0)
        self.pos = pygame.Vector2(WIDTH//2, HEIGHT//2)
        self.hitbox = pygame.Rect(0, 0, 20, 20)
        self.accel = accel
        self.friction = friction

        self.max_health = health
        self.health = health
        self.heal_delay = heal_delay
        self.heal_per_sec = heal_per_sec
        self.health_bar = HealthBar(pos=self.pos, max_health=self.health, curr_health=self.health)
        self.last_heal_time = 0

        # Level properties
        self.shot_amount = shot_amount
        self.bullet_speed = bullet_speed
        self.shot_delay = shot_delay
        self.shot_damage = shot_damage
        self.max_speed = max_speed
        self.defence = defence

        # Cannon properties
        self.cannon_image = pygame.image.load(path+"stg1_cannon.png").convert_alpha()
        self.cannon_size = (25,10)
        self.cannon_image = pygame.transform.scale(self.cannon_image, self.cannon_size)
        self.angle = 0
        self.last_shot_time = 0
        
    def cannonManage(self):
        if self.shot_amount == 1:
            self.cannon_image = pygame.image.load(path+"stg2_cannon.png").convert_alpha()
            self.cannon_size = (20,30)
        elif self.shot_amount == 2:
            self.cannon_image = pygame.image.load(path+"stg3_cannon.png").convert_alpha()
            self.cannon_size = (20,35)
        
        self.cannon_image = pygame.transform.scale(self.cannon_image, self.cannon_size)

    def update(self):
        # CONTROL MOVEMENT ==========================================
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.vel.x -= self.accel
        if keys[pygame.K_d]:
            self.vel.x += self.accel
        if keys[pygame.K_w]:
            self.vel.y -= self.accel
        if keys[pygame.K_s]:
            self.vel.y += self.accel

        # Apply damping friction (to increase smoothness) 
        self.vel *= self.friction

        # Resize velocity vector so that it does not exceed max_speed when diagonal
        if self.vel.length() > self.max_speed:
            self.vel.scale_to_length(self.max_speed)
        
        self.pos += self.vel

        # Inner min ensures x/y position does not go beyond one end of screen
        # Outer max ensures x/y position does not go beyond the other end of screen
        self.pos.x = max(self.radius, min(ARENA_BOUNDARY_WIDTH - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(HEIGHT - self.radius, self.pos.y))

        # CONTROL AIMING =====================================================
        mouse_pos = pygame.mouse.get_pos()
        direction = pygame.Vector2(mouse_pos) - self.pos
        self.angle = math.atan2(direction.y, direction.x)      # Mouse angle in radians
        

        # UPDATE HITBOX AND HEALTH BAR ===================================
        self.hitbox.center = self.pos

        health_bar_offset = self.pos + pygame.Vector2(0, 20)
        self.health_bar.update(self.health, health_bar_offset)

    def shoot(self):
        bullets = []
        current_time = pygame.time.get_ticks()

        if current_time - self.last_shot_time >= self.shot_delay:
            self.last_shot_time = current_time

            # Get the starting position of the bullet via trigonometry + hardcoded offsets for bullet spread
            dir_vector_1 = pygame.Vector2(math.cos(self.angle), math.sin(self.angle))
            dir_vector_2 = pygame.Vector2(math.cos(self.angle+0.05), math.sin(self.angle+0.05))
            dir_vector_3 = pygame.Vector2(math.cos(self.angle-0.05), math.sin(self.angle-0.05))
            bullet_pos = self.pos + dir_vector_1 * self.cannon_size[0]

            # Instantiate a bullet depending on level of shot amount skill
            if self.shot_amount == 0:
                bullets.append(PlayerBullet(bullet_pos, dir_vector_1, self.bullet_speed, self.shot_damage)) 
            if self.shot_amount == 1:
                bullets.append(PlayerBullet(bullet_pos, dir_vector_1, self.bullet_speed, self.shot_damage))
                bullets.append(PlayerBullet(bullet_pos, dir_vector_2, self.bullet_speed, self.shot_damage)) 
            if self.shot_amount == 2:
                bullets.append(PlayerBullet(bullet_pos, dir_vector_1, self.bullet_speed, self.shot_damage)) 
                bullets.append(PlayerBullet(bullet_pos, dir_vector_2, self.bullet_speed, self.shot_damage)) 
                bullets.append(PlayerBullet(bullet_pos, dir_vector_3, self.bullet_speed, self.shot_damage)) 
        
            return bullets
        

    def draw(self, surface):
        self.cannonManage()

        # Creating a surface for the cannon so it can be easily rotated
        rotated_cannon = pygame.transform.rotate(self.cannon_image, -math.degrees(self.angle))

        # Offsetting the cannon centre so it protrudes on one side of the player
        dir_vector = pygame.Vector2(math.cos(self.angle),math.sin(self.angle))
        offset_pos = self.pos + dir_vector * (self.cannon_size[0]//3)

        # Blit the rotated cannon on screen
        rect = rotated_cannon.get_rect(center=offset_pos)
        surface.blit(rotated_cannon, rect.topleft)

        # Draw the player and outline over the cannon
        pygame.draw.circle(surface, self.fill, self.pos, self.radius)
        pygame.draw.circle(surface, self.outline, self.pos, self.radius, self.thickness)
        
        self.health_bar.draw(surface)
        # Draw hitbox
        # pygame.draw.rect(surface, RED, self.hitbox)


# DRIVER CODE ============================================================

def main():
    clock = pygame.time.Clock()
    player = Player()
    upgrade_screen = UpgradeScreen(player=player)
    # level_bar = LevelBar()
    pause_screen = PauseScreen()
    entities = [player,upgrade_screen]

    # spawn_loc = [(0,0), (ARENA_BOUNDARY_WIDTH,0), (0,HEIGHT), (ARENA_BOUNDARY_WIDTH,HEIGHT)]
    # for loc in spawn_loc:
    #     square = Square(pos=loc, health=20, player=player)
    #     entities.append(square)
    #     GLOBAL_ENEMY_POS[square] = loc

    spawn_loc = [(0,0), (200,0), (0,200), (200,200)]
    for loc in spawn_loc:
        dome = Dome(pos=loc, health=20, player=player)
        entities.append(dome)
        GLOBAL_ENEMY_POS[dome] = loc
    
    # GAME LOOP ================================
    running = True
    while running:
        dt = clock.tick(60)/1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                upgrade_screen.click(event.pos)

        # GET MOUSE INPUTS ===================================
        mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()

        # VERIFY GAME PAUSE ===============================================
        paused = upgrade_screen.arena_area.collidepoint(mouse_pos)

        # DRAWING PAUSE SCREEN ===========================
        if paused:
            screen.fill(WHITE)
            for entity in entities:
                entity.draw(screen)
            pause_screen.draw(screen)

        else:
            # SHOOTING MECHANIC ===============================================
            if mouse_buttons[0]:
                bullets = player.shoot()
                if bullets:    # Verifying whether list is empty to reduce unnecessary processing when added to entities list
                    entities.extend(bullets)
            
            # DRAWING AND UPDATING ALL ENTITIES ==========================================
            screen.fill(WHITE)
            for entity in entities[:]:   # Entities[:] is a shallow copy, because entities is already being consistently updated above
                                         # Without this, bullets lag a bit
                entity.draw(screen)
                entity.update()

                # Remove player bullet from entity list if it is off screen to conserve memory 
                if isinstance(entity, PlayerBullet):
                    if entity.off_screen() or entity.collide():
                        entities.remove(entity)

                # Update positions for all enemies in the global position dictionary for collision checking
                if isinstance(entity, Enemy):
                    GLOBAL_ENEMY_POS[entity] = entity.hitbox
                    if entity.check_death() or entity.collide():
                        entities.remove(entity)
                        GLOBAL_ENEMY_POS.pop(entity)
            
        pygame.display.flip() 

    pygame.quit()

main()