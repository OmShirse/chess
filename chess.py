import pygame

pygame.init()
screen = pygame.display.set_mode((1080, 1080))

running = True
while running:
    screen.fill((255, 255, 255))
    
    for column in range(50,750,200):
        for row in range(100,900,200):
            pygame.draw.rect(screen, (0, 0, 0), (row, column, 100, 100))
        for row in range(200,900,200):
            pygame.draw.rect(screen, (180, 180, 180), (row, column, 100, 100))

    for column in range(150,750,200):
        for row in range(200,900,200):
            pygame.draw.rect(screen, (0, 0, 0), (row, column, 100, 100))
        for row in range(100,900,200):
            pygame.draw.rect(screen, (180, 180, 180), (row, column, 100, 100))

for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.update()

pygame.quit()
