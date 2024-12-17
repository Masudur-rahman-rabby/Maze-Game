import pygame
from random import randrange

from maze_generator import *

start_time = 0  # Variable to keep track of the start time
time = 30

# A* Algorithm for pathfinding
def astar(start, goal, grid_cells):
    open_set = {start}
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_set:
        current = min(open_set, key=lambda cell: f_score[cell])

        if current == goal:
            return reconstruct_path(came_from, goal)

        open_set.remove(current)

        for neighbor in current.get_neighbors(grid_cells):
            tentative_g_score = g_score[current] + 1

            if tentative_g_score < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)

                if neighbor not in open_set:
                    open_set.add(neighbor)

    return None

def heuristic(cell, goal):
    return abs(cell.x - goal.x) + abs(cell.y - goal.y)

# Function to reconstruct path for A* Algorithm
def reconstruct_path(came_from, current):
    total_path = [current]
    while current in came_from:
        current = came_from[current]
        total_path.append(current)
    return total_path[::-1]

def fuzzy_evaluate(state, grid_cells):
    # Fuzzy Variables
    player_dist = heuristic(state['player'], state['goal'])
    ai_dist = heuristic(state['ai'], state['goal'])
    path_complexity = calculate_path_complexity(state['ai'], state['goal'], grid_cells)
    obstacle_density = calculate_obstacle_density(state['ai'], grid_cells)
    player_proximity = heuristic(state['ai'], state['player'])
    food_collection_efficiency = calculate_food_efficiency(state['ai'], grid_cells)

    # Fuzzy Rules

    # Rule 1: Distance and Path Complexity
    if ai_dist < 3 and path_complexity < 3:
        move_quality = 'high'
    elif ai_dist > 7 and path_complexity > 5:
        move_quality = 'low'
    else:
        move_quality = 'medium'

    # Rule 2: Obstacle Density and Player Proximity
    if obstacle_density > 5 and player_proximity < 3:
        move_quality = 'medium'
    elif obstacle_density < 3 and player_proximity > 5:
        move_quality = 'high'
    else:
        move_quality = 'low'

    # Rule 3: Food Collection Efficiency
    if food_collection_efficiency > 0.7 and player_proximity > 5:
        move_quality = 'high'
    elif food_collection_efficiency < 0.3 and player_proximity < 3:
        move_quality = 'low'
    else:
        move_quality = 'medium'

    # Combine Fuzzy Logic Outputs
    if move_quality == 'high':
        return 1
    elif move_quality == 'medium':
        return 0
    else:
        return -1

# Additional helper functions to calculate fuzzy variables
def calculate_path_complexity(ai_pos, goal_pos, grid_cells):
    # Simplified version: calculate based on number of turns in the path
    path = astar(ai_pos, goal_pos, grid_cells)
    complexity = sum(1 for i in range(1, len(path) - 1) if path[i-1].x != path[i].x and path[i].y != path[i+1].y)
    return complexity

def calculate_obstacle_density(ai_pos, grid_cells):
    # Simplified version: count obstacles in the AI's vicinity
    neighbors = ai_pos.get_neighbors(grid_cells)
    return sum(1 for cell in neighbors if cell.is_wall)

def calculate_food_efficiency(ai_pos, grid_cells):
    # Simplified version: how close AI is to food compared to player
    food_distances = [heuristic(ai_pos, food_pos) for food_pos in grid_cells if food_pos.has_food()]
    closest_food = min(food_distances) if food_distances else float('inf')
    return 1 / closest_food if closest_food > 0 else 1


# Minimax algorithm with alpha-beta pruning
def minimax(state, depth, alpha, beta, maximizing_player, grid_cells):
    if depth == 0 or state['player'] == state['goal'] or state['ai'] == state['goal']:
        return fuzzy_evaluate(state, grid_cells)

    if maximizing_player:
        max_eval = float('-inf')
        for move in state['ai'].get_neighbors(grid_cells):
            new_state = state.copy()
            new_state['ai'] = move
            eval = minimax(new_state, depth - 1, alpha, beta, False, grid_cells)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in state['player'].get_neighbors(grid_cells):
            new_state = state.copy()
            new_state['player'] = move
            eval = minimax(new_state, depth - 1, alpha, beta, True, grid_cells)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval



# Second player class (AI)
class SecondPlayer:
    def __init__(self):
        self.img = pygame.image.load('img/murgi.png').convert_alpha()
        self.img = pygame.transform.scale(self.img, (TILE - 10, TILE - 10))
        self.rect = self.img.get_rect()
        self.set_pos()

    def set_pos(self):
        self.rect.topright = (WIDTH, 0)
        self.rect.move_ip(-5, 5)

    def draw(self):
        game_surface.blit(self.img, self.rect)




    # Modified move_towards_food method using Minimax
    def move_towards_food(self, food, grid_cells):
        # Define the initial game state
        state = {
            'player': grid_cells[player_rect.y // TILE * cols + player_rect.x // TILE],
            'ai': grid_cells[self.rect.y // TILE * cols + self.rect.x // TILE],
            'goal': grid_cells[food.rect.y // TILE * cols + food.rect.x // TILE]
        }

        # Determine the best move using Minimax with alpha-beta pruning
        best_move = None
        max_eval = float('-inf')

        # Get all possible moves (neighbors) for the AI
        possible_moves = state['ai'].get_neighbors(grid_cells)

        # Sort moves based on their heuristic to improve alpha-beta pruning efficiency
        possible_moves.sort(key=lambda move: heuristic(move, state['goal']))

        for move in possible_moves:
            # Update AI's position in the state
            new_state = state.copy()
            new_state['ai'] = move

            # Evaluate the move using Minimax
            eval = minimax(new_state, depth=3, alpha=float('-inf'), beta=float('inf'), maximizing_player=False,
                           grid_cells=grid_cells)

            if eval > max_eval:
                max_eval = eval
                best_move = move

        # Move the AI towards the best evaluated move
        if best_move:
            target_x, target_y = best_move.x * TILE, best_move.y * TILE
            dx = target_x - self.rect.x
            dy = target_y - self.rect.y

            if abs(dx) > abs(dy):
                dx = dx / abs(dx)
                dy = 0
            else:
                dx = 0
                dy = dy / abs(dy)

            self.rect.move_ip(dx * player_speed, dy * player_speed)
        else:
            print("No valid move found. Game Over.")
            pygame.quit()
            exit()


            
    def move_towards_food(self, food, grid_cells):
        start_cell = grid_cells[self.rect.y // TILE * cols + self.rect.x // TILE]
        goal_cell = grid_cells[food.rect.y // TILE * cols + food.rect.x // TILE]

        path = astar(start_cell, goal_cell, grid_cells)

        if path and len(path) > 1:
            next_cell = path[1]
            target_x, target_y = next_cell.x * TILE, next_cell.y * TILE
            dx = target_x - self.rect.x
            dy = target_y - self.rect.y
            if abs(dx) > abs(dy):
                dx = dx / abs(dx)
                dy = 0
            else:
                dx = 0
                dy = dy / abs(dy)
            self.rect.move_ip(dx * player_speed, dy * player_speed)
        else:
            print("Game Over")
            pygame.quit()
            exit()

# Food class
class Food:
    def __init__(self):
        self.img = pygame.image.load('img/food.png').convert_alpha()
        self.img = pygame.transform.scale(self.img, (TILE - 10, TILE - 10))
        self.rect = self.img.get_rect()
        self.set_pos()

    def set_pos(self):
        self.rect.bottomright = (WIDTH, HEIGHT)
        self.rect.move_ip(-5, -5)

    def draw(self):
        game_surface.blit(self.img, self.rect)

# Check if player collides with walls
def is_collide(x, y):
    tmp_rect = player_rect.move(x, y)
    if tmp_rect.collidelist(walls_collide_list) == -1:
        return False
    return True

# Check if player eats food
def eat_food():
    for food in food_list:
        if player_rect.collidepoint(food.rect.center):
            food.set_pos()
            return True
    return False

# Check if game is over
def is_game_over():
    global time, score, record, FPS
    if time < 0:
        pygame.time.wait(700)
        player_rect.center = TILE // 2, TILE // 2
        [food.set_pos() for food in food_list]
        set_record(record, score)
        record = get_record()
        time, score, FPS = 60, 0, 60
    else:
        for food in food_list:
            if player_rect.collidepoint(food.rect.center):
                surface.blit(text_font.render('You Win!', True, pygame.Color('green'), True),
                             (WIDTH + 30, 350))
                pygame.display.flip()
                pygame.time.wait(2000)
                pygame.quit()
                exit()
            elif second_player.rect.colliderect(food.rect):
                surface.blit(text_font.render('Game Over', True, pygame.Color('red'), True),
                             (WIDTH + 30, 350))
                pygame.display.flip()
                pygame.time.wait(2000)
                pygame.quit()
                exit()

# Get the record from file
def get_record():
    try:
        with open('record') as f:
            return f.readline()
    except FileNotFoundError:
        with open('record', 'w') as f:
            f.write('0')
            return 0

# Set the record to file
def set_record(record, score):
    rec = max(int(record), score)
    with open('record', 'w') as f:
        f.write(str(rec))

# Main game setup
FPS = 60
pygame.init()
game_surface = pygame.Surface(RES)
surface = pygame.display.set_mode((WIDTH + 300, HEIGHT))
clock = pygame.time.Clock()
bg = pygame.image.load('img/bg_main.jpg').convert()
grass_green = (126, 219, 156)
maze = generate_maze()
player_speed = 5
player_img = pygame.image.load('img/morog.png').convert_alpha()
player_img = pygame.transform.scale(player_img, (TILE - 2 * maze[0].thickness, TILE - 2 * maze[0].thickness))
player_rect = player_img.get_rect()
player_rect.center = TILE // 2, TILE // 2
directions = {pygame.K_LEFT: (-player_speed, 0), pygame.K_RIGHT: (player_speed, 0), pygame.K_UP: (0, -player_speed),
              pygame.K_DOWN: (0, player_speed)}
keys = {pygame.K_LEFT: pygame.K_LEFT, pygame.K_RIGHT: pygame.K_RIGHT, pygame.K_UP: pygame.K_UP,
        pygame.K_DOWN: pygame.K_DOWN}
direction = (0, 0)
food_list = [Food() for i in range(3)]
walls_collide_list = sum([cell.get_rects() for cell in maze], [])
pygame.time.set_timer(pygame.USEREVENT, 1000)
score = 0
record = get_record()
font = pygame.font.SysFont('Impact', 50)
text_font = pygame.font.SysFont('Impact', 80)
second_player = SecondPlayer()

# Main game loop
while True:
    surface.blit(bg, (WIDTH, 0))
    surface.blit(game_surface, (0, 0))
    game_surface.fill(grass_green)

    second_player.draw()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        if event.type == pygame.USEREVENT:
            time -= 1

    if start_time == 0:
        start_time = pygame.time.get_ticks() / 1000

    current_time = pygame.time.get_ticks() / 1000
    if current_time - start_time >= 20 and current_time - start_time <= 30:
        for food in food_list:
            second_player.move_towards_food(food, maze)

    pressed_key = pygame.key.get_pressed()
    for key, key_value in keys.items():
        if pressed_key[key_value] and not is_collide(*directions[key]):
            direction = directions[key]
            break
    if not is_collide(*direction):
        player_rect.move_ip(direction)

    for food in food_list:
        if current_time - start_time <= 20:
            # Here you can add logic if needed for player movement during the first 20 seconds
            pass
        else:
            second_player.move_towards_food(food, maze)

    [cell.draw(game_surface) for cell in maze]

    if eat_food():
        FPS += 10
        score += 1
    is_game_over()

    game_surface.blit(player_img, player_rect)
    [food.draw() for food in food_list]

    surface.blit(text_font.render('Vs Murgi', True, pygame.Color('gold'), None), (WIDTH + 0, 10))
    surface.blit(text_font.render('TIME', True, pygame.Color('cyan'), None), (WIDTH + 70, 100))
    surface.blit(font.render(f'{time}', True, pygame.Color('cyan'), None), (WIDTH + 70, 200))
    surface.blit(text_font.render('Result:', True, pygame.Color('forestgreen'), None), (WIDTH + 50, 350))
    surface.blit(font.render(f'{score}', True, pygame.Color('forestgreen'), None), (WIDTH + 70, 430))
    surface.blit(text_font.render('record:', True, pygame.Color('magenta'), None), (WIDTH + 30, 620))
    surface.blit(font.render(f'{record}', True, pygame.Color('magenta'), None), (WIDTH + 70, 700))

    pygame.display.flip()
    clock.tick(FPS)
