import pygame
import math
from abc import ABC, abstractmethod

# CONSTANTS + INITIALISATION ===================================================

WHITE = (255,255,255)
GREY = (145, 145, 145)
BLACK = (0,0,0)
PLAYER_BLUE = (0, 110, 255)

WIDTH = 960
HEIGHT = 540
ARENA_BOUNDARY_WIDTH = 680
ARENA_BOUNDARY_HEIGHT = 480

path = "src/assets/"

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
screen.fill(WHITE)
pygame.display.set_caption("Dieflow")

# CLASSES ===============================================================

# TODO: Implement upgrades: More bullets, more bullet damage
#       Right now make more bullets.

# TODO: Make game pause when mouse on the upgrade screen

class Entity():
    @abstractmethod
    def update():
        pass

    @abstractmethod
    def draw():
        pass

class UpgradeScreen(Entity):
    def __init__(self):
        self.bg_colour = GREY
        self.shot_amount = 1
        self.bullet_speed = 1
        self.shot_delay = 1
        self.shot_damage = 1
        self.max_speed = 1
        self.defense = 1

    def update(self):
        pass

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_colour, (ARENA_BOUNDARY_WIDTH,0,WIDTH-ARENA_BOUNDARY_WIDTH, HEIGHT))
        self.upgrade_screen_image = pygame.image.load(path+"upgrade_screen.png").convert_alpha()
        screen.blit(self.upgrade_screen_image, (695, 20))

class LevelBar(Entity):
    def __init__(self):
        self.bg_colour = GREY

    def update(self):
        pass

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_colour, (0,ARENA_BOUNDARY_HEIGHT, ARENA_BOUNDARY_WIDTH, HEIGHT-ARENA_BOUNDARY_HEIGHT))

class Bullet(Entity):
    def __init__(self, pos, direction, speed=7, radius=5, colour=BLACK):
        self.pos = pygame.Vector2(pos)
        self.speed = speed
        self.vel = pygame.Vector2(direction)*speed
        self.radius = radius
        self.colour = colour

    def update(self):
        self.pos += self.vel
    
    def draw(self, surface):
        pygame.draw.circle(surface, self.colour, self.pos, self.radius)
    
    def off_screen(self):
        return (self.pos.x < 0 or self.pos.x > ARENA_BOUNDARY_WIDTH-self.speed or 
                self.pos.y < 0 or self.pos.y > ARENA_BOUNDARY_HEIGHT-self.speed)

class Player(Entity):
    def __init__(self, radius=10, thickness=1, accel=0.5, friction=0.9, level=1, 
                 shot_amount=1, bullet_speed=7, shot_delay=400, shot_damage=10, max_speed=6,defense=5):
        self.radius = radius
        self.fill = PLAYER_BLUE
        self.outline = BLACK
        self.thickness = thickness
        self.level = level   # Determine what this is used for
        
        # Movement parameters
        # We have velocity, not just speed. This is to ensure smooth sliding movement!
        self.vel = pygame.Vector2(0,0)
        self.pos = pygame.Vector2(WIDTH//2, HEIGHT//2)
        self.accel = accel
        self.friction = friction

        # Level properties
        self.shot_amount = shot_amount
        self.bullet_speed = bullet_speed
        self.shot_delay = shot_delay
        self.shot_damage = shot_damage
        self.max_speed = max_speed
        self.defense = defense

        # Cannon properties
        self.cannon_image = pygame.image.load(path+"stg1_cannon.png").convert_alpha()
        self.cannon_size = (25,10)
        self.cannon_image = pygame.transform.scale(self.cannon_image, self.cannon_size)
        self.angle = 0
        self.last_shot_time = 0
        
    
    def upgradeManage(self):
        if self.level >= 10 and self.level < 20:
            self.cannon_image = pygame.image.load(path+"stg2_cannon.png").convert_alpha()
            self.cannon_size = (20,30)
        if self.level >= 20:
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
        self.pos.y = max(self.radius, min(ARENA_BOUNDARY_HEIGHT - self.radius, self.pos.y))

        # CONTROL AIMING =====================================================
        mouse_pos = pygame.mouse.get_pos()
        direction = pygame.Vector2(mouse_pos) - self.pos
        self.angle = math.atan2(direction.y, direction.x)        
    
    def shoot(self):
        current_time = pygame.time.get_ticks()

        if current_time - self.last_shot_time >= self.shot_delay:
            self.last_shot_time = current_time

            # Get the starting position of the bullet via trigonometry
            dir_vector = pygame.Vector2(math.cos(self.angle),math.sin(self.angle))
            bullet_pos = self.pos + dir_vector * self.cannon_size[0]

            # Instantiate a bullet
            return Bullet(bullet_pos, dir_vector)

        return None

    def draw(self, surface):
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

# DRIVER CODE ============================================================

def main():
    clock = pygame.time.Clock()
    player = Player()
    upgrade_screen = UpgradeScreen()
    level_bar = LevelBar()
    entities = [player,upgrade_screen,level_bar]

    player.upgradeManage()

    # GAME LOOP ================================
    running = True
    while running:
        dt = clock.tick(60)/1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # GET MOUSE INPUTS ===================================
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]:
            entities.append(player.shoot())
            
        # DRAW + UPDATE ALL ENTITIES ===========================
        screen.fill(WHITE)
        for entity in entities:
            if entity:
                entity.update()
                entity.draw(screen)

                # Remove bullet from entity list if it is off screen to conserve memory 
                if isinstance(entity, Bullet):
                    if entity.off_screen():
                        entities.remove(entity)

        pygame.display.flip() 

    pygame.quit()

main()