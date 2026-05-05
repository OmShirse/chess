import pygame

pygame.init()
screen = pygame.display.set_mode((800, 800))
font = pygame.font.SysFont("arial", 20)

SQUARE_SIZE = 100

running = True
while running:
    screen.fill((255, 255, 255))

    mouse_x, mouse_y = pygame.mouse.get_pos()
    # convert mouse position to grid position
    col = mouse_x // SQUARE_SIZE
    row = mouse_y // SQUARE_SIZE
    
    for i in range(8):        
        for j in range(8):    
            x = j * SQUARE_SIZE
            y = i * SQUARE_SIZE
            if (i + j) % 2 == 0:
                color = (0, 0, 0)
            else:
                color = (180, 180, 180)
            pygame.draw.rect(screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

    # display hovered position
    text = font.render(f"({row}, {col})", True, (255, 0, 0))
    screen.blit(text, (10, 10))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.update()

pygame.quit()
