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

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
screen.fill(WHITE)
pygame.display.set_caption("Dieflow")

# CLASSES ===============================================================

class Entity():
    @abstractmethod
    def update():
        pass

    @abstractmethod
    def draw():
        pass


class Bullet(Entity):
    def __init__(self, pos, direction, speed=7, radius=5, colour=BLACK):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(direction)*speed
        self.radius = radius
        self.colour = colour

    def update(self):
        self.pos += self.vel
    
    def draw(self, surface):
        pygame.draw.circle(surface, self.colour, self.pos, self.radius)
    
    def off_screen(self):
        return (self.pos.x < 0 or self.pos.x > WIDTH or self.pos.y < 0 or self.pos.y > HEIGHT)

class Player(Entity):
    def __init__(self, radius=10, thickness=1, max_speed=6, accel=0.5, friction=0.9):
        self.radius = radius
        self.fill = PLAYER_BLUE
        self.outline = BLACK
        self.thickness = thickness
        
        # Movement parameters
        # We have velocity, not just speed. This is to ensure smooth sliding movement!
        self.vel = pygame.Vector2(0,0)
        self.pos = pygame.Vector2(WIDTH//2, HEIGHT//2)
        self.max_speed = max_speed
        self.accel = accel
        self.friction = friction

        # Cannon properties
        self.cannon_size = (20,10)
        self.cannon_fill = GREY
        self.angle = 0
    
    def update(self):
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
        self.pos.x = max(self.radius, min(WIDTH - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(HEIGHT - self.radius, self.pos.y))

        mouse_pos = pygame.mouse.get_pos()
        direction = pygame.Vector2(mouse_pos) - self.pos
        self.angle = math.atan2(direction.y, direction.x)        
    
    def shoot(self):
        # Get the starting position of the bullet via trigonometry
        dir_vector = pygame.Vector2(math.cos(self.angle),math.sin(self.angle))
        bullet_pos = self.pos + dir_vector * self.cannon_size[0]

        # Instantiate a bullet
        return Bullet(bullet_pos, dir_vector)

    def draw(self, surface):
        # Creating a surface for the cannon so it can be easily rotated
        cannon_surface = pygame.Surface(self.cannon_size, pygame.SRCALPHA)
        pygame.draw.rect(cannon_surface, self.cannon_fill, (0,0,*self.cannon_size))
        rotated_cannon = pygame.transform.rotate(cannon_surface, -math.degrees(self.angle))

        # Offsetting the cannon centre so it protrudes on one side of the player
        dir_vector = pygame.Vector2(math.cos(self.angle),math.sin(self.angle))
        offset_pos = self.pos + dir_vector * (self.cannon_size[0]//2)

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
    entities = [player]

    running = True
    while running:
        dt = clock.tick(60)/1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                entities.append(player.shoot())
        
        screen.fill(WHITE)
        for entity in entities:
            entity.update()
            entity.draw(screen)

            # Remove bullet from entity list if it is off screen to conserve memory 
            if isinstance(entity, Bullet):
                if entity.off_screen():
                    entities.remove(entity)

        pygame.display.flip() 

    pygame.quit()

main()