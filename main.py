import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import RPi.GPIO as GPIO  # Enabled GPIO for PiTFT

import pygame
import time
import random
import json
import math
import pigame
from pygame.locals import *


os.putenv('SDL_VIDEODRV', 'fbcon')
os.putenv('SDL_FBDEV', '/dev/fb0')
os.putenv('SDL_MOUSEDRV', 'dummy')
os.putenv('SDL_MOUSEDEV', '/dev/null')
os.putenv('DISPLAY', '')



pygame.init()
pitft = pigame.PiTft()


#window = pitft  # Use pitft as the window surface
disp_w, disp_h = 320, 240
win = pygame.display.set_mode((disp_w, disp_h))

win.fill((0,0,0))

# GPIO joystick pins for us 
ltfs_ctrl_pin  = 5    # BCM 5
rtfs_ctrl_pin = 19   # BCM 19

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(ltfs_ctrl_pin,  GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(rtfs_ctrl_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Button callback for bailout buttons 
play = True
def button_callback(channel):
    global play
    play = False
    cleanup_and_exit()





# Button pins setup for PiTFT setting up 
PIN_NUMBERS = [17, 22, 23, 27]
for n in PIN_NUMBERS:
    GPIO.setup(n, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(n, GPIO.RISING, callback=button_callback, bouncetime=300)

# Colors
clr_blk       = (  0,   0,   0)

clr_wht       = (255, 255, 255)

clr_dk_blu   = (  0,   0, 200)
clr_dk_rd    = (200,   0,   0)
clr_dk_grn  = (  0, 200,   0)

clr_brt_rd  = (255,   0,   0)
clr_brt_grn= (  0, 255,   0)
clr_brt_blu = (  0,   0, 255)


# Leaderboard and user data for us 
LEADERBOARD_FILE = 'leaderboard.json'
current_uname = "Player"
ldrboard = []

# Images in game
bball_img = pygame.image.load('basketball.png').convert_alpha()
bball_img = pygame.transform.scale(bball_img, (30, 30))
bg             = pygame.image.load('background.jpg')
bg             = pygame.transform.scale(bg, (320, 240))
gbg_img    = pygame.image.load('garbage.png').convert_alpha()
gbg_img    = pygame.transform.scale(gbg_img, (40, 40))
bskt_img     = pygame.image.load('basket.png')
bskt_img     = pygame.transform.scale(bskt_img, (50, 50))

tmr = pygame.time.Clock()

def cleanup_and_exit():
    global play
    print("Exiting")
    # Quick check on leaderboard file
    if os.path.exists(LEADERBOARD_FILE):
        print(f"Our Leaderboard file exists at exit: {os.path.abspath(LEADERBOARD_FILE)}")
    
    GPIO.cleanup()  # Enable GPIO cleanup
    pygame.quit()
    import sys
    sys.exit(0)



# Establishig our game classes
class HoopController:
    def __init__(self, x, y):
        self.pos_x = x
        self.pos_y = y
        self.spd = 10
        self.col_area = {
            'left': self.pos_x + 10,
            'top': self.pos_y + 10,
            'width': 20,
            'height': 20
        }
    
    def draw(self, win):
        pos_x = int(self.pos_x)
        pos_y = int(self.pos_y)
        win.blit(bskt_img, (pos_x, pos_y))
        self.col_area = {
            'left': pos_x + 10,
            'top': pos_y + 10,
            'width': 20,
            'height': 20
        }
        
    def get_hitbox(self):
        return (
            self.col_area['left'], 
            self.col_area['top'], 
            self.col_area['width'], 
            self.col_area['height']
        )



class Ball:
    def __init__(self, x, y, b_type):
        self.pos_x   = x
        self.pos_y   = y
        self.b_type = b_type
        self.sz = 30
        self.col_box = {
            'left': self.pos_x,
            'top': self.pos_y,
            'width': self.sz,
            'height': self.sz
        }
    
    def draw(self, win):
        if self.b_type == 0:
            ball = pygame.transform.scale(bball_img, (30, 30))
            win.blit(ball, (int(self.pos_x), int(self.pos_y)))
            self.col_box = {
                'left': int(self.pos_x),
                'top': int(self.pos_y),
                'width': self.sz,
                'height': self.sz
            }
            
    def get_hitbox(self):
        return (
            self.col_box['left'], 
            self.col_box['top'], 
            self.col_box['width'], 
            self.col_box['height']
        )



class Obstacle:
    def __init__(self, x, y, obs_type=0):
        self.pos_x = x
        self.pos_y = y
        self.spd = 5
        self.sz = 40
        self.obs_type = obs_type
        self.dngr_zone = {
            'left': self.pos_x,
            'top': self.pos_y,
            'width': self.sz,
            'height': self.sz
        }
    
    
    def draw(self, win):
        win.blit(gbg_img, (int(self.pos_x)+8, int(self.pos_y)-5))
        self.dngr_zone = {
            'left': int(self.pos_x),
            'top': int(self.pos_y),
            'width': self.sz,
            'height': self.sz
        }
        
    
    def get_hitbox(self):
        return (
            self.dngr_zone['left'],
            self.dngr_zone['top'],
            self.dngr_zone['width'],
            self.dngr_zone['height']
        )




def create_text_elements(text, font):
    txtSrf = font.render(text, True, clr_blk)
    return txtSrf, txtSrf.get_rect()



def render_text_message(msg, x, y, size):
    regText = pygame.font.Font("freesansbold.ttf", size)
    txtSrf, txtRect = create_text_elements(msg, regText)
    txtRect.center = (x, y)
    win.blit(txtSrf, txtRect)



def initialize_leaderboard():
    global ldrboard
    if os.path.exists(LEADERBOARD_FILE):
        print(f"Loading leaderboard from {os.path.abspath(LEADERBOARD_FILE)}")
        # Seeing for opeining
        f = open(LEADERBOARD_FILE, 'r')
        ldrboard = json.load(f)
        f.close()
        print(f"Loaded leaderboard with {len(ldrboard)} entries")
    else:
        print(f"Leaderboard file not found, creating new one")
        ldrboard = []
        # Creating our empty file
        f = open(LEADERBOARD_FILE, 'w')
        
        
        json.dump(ldrboard, f)
        f.close()
        print(f"Created new leaderboard file at {os.path.abspath(LEADERBOARD_FILE)}")



def record_player_score(uname, scr):
    global ldrboard
    print(f"Saving score for {uname}: {scr}")
    # Adding a new score
    ldrboard.append({"name": uname, "score": scr})
    # Sortig based on the score 
    ldrboard = sorted(ldrboard, key=lambda x: x["score"], reverse=True)
    # Keeping only top 5 scores for us 
    ldrboard = ldrboard[:5]
    # Savig to file of leaderboard
    print(f"Writing to {LEADERBOARD_FILE}")
    f = open(LEADERBOARD_FILE, 'w')
    json.dump(ldrboard, f)
    f.close()
    print(f"Leaderboard saved successfully")



def show_leaderboard_screen():
    intro = True
    # Make sure leaderboard is up to date sufficiently 
    initialize_leaderboard()
    
    while intro:
        pitft.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if 120 < pos[0] < 200 and 210 < pos[1] < 235:
                    return
        
        win.fill(clr_wht)
        
        render_text_message("LEADERBOARD", 160, 30, 24)
        
        
        
        if not ldrboard:
            render_text_message("No scores yet!", 160, 80, 16)
        else:
            y_pos = 70
            for i, entry in enumerate(ldrboard[:7]):  # Show top 7 scores
                render_text_message(f"{i+1}. {entry['name']}: {entry['score']}", 160, y_pos, 16)
                y_pos += 20
        
        # Displaying our total entries
        if ldrboard:
            render_text_message(f"Total entries: {len(ldrboard)}", 160, 190, 12)
        
        pygame.draw.rect(win, clr_brt_blu, (120, 210, 80, 25))
        render_text_message("Back", 160, 222, 16)
        pygame.display.update()
        tmr.tick(15)



def prompt_for_username():
    global current_uname
    inpt_box = pygame.Rect(90, 120, 140, 32)
    clr_inactive = pygame.Color('lightskyblue3')
    clr_active = pygame.Color('dodgerblue2')
    color = clr_active  # Start with active color
    active = True  
    text = ''
    done = False
    
    print("Enter username with keyboard")
    
    while not done:
        pitft.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # If user clicked the Submit button
                if 90 < event.pos[0] < 230 and 170 < event.pos[1] < 195:
                    if text:
                        current_uname = text
                        done = True
            
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if text:
                        current_uname = text
                        done = True
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    # Limit username to 10 characters
                    if len(text) < 10:
                        text += event.unicode
        
        win.fill(clr_wht)
        render_text_message("Enter Your Name", 160, 80, 24)
        
        # Render our current text
        txt_surface = pygame.font.Font("freesansbold.ttf", 20).render(text, True, color)
        # Resize our box if the text is too long for it 
        width = max(140, txt_surface.get_width()+10)
        inpt_box.w = width
        # Blit the text for us 
        win.blit(txt_surface, (inpt_box.x+5, inpt_box.y+5))
        # Blit the input_box rect
        pygame.draw.rect(win, color, inpt_box, 2)
        
        # Submit button for us 
        pygame.draw.rect(win, clr_brt_grn, (90, 170, 140, 25))
        render_text_message("Submit", 160, 182, 16)
        
        # Add instruction for keyboard usage type method
        render_text_message("Type name and press Enter", 160, 210, 14)
        
        pygame.display.update()
        
        tmr.tick(30)



def render_menu_elements():
    # just draws placeholders for menu for us 
    pygame.draw.rect(win, clr_brt_grn, (20, 150, 75, 50))
    pygame.draw.rect(win, clr_dk_rd,   (215,150,75,50))
    pygame.draw.rect(win, clr_brt_blu,(110,150,75,50))
    pygame.draw.rect(win, (255,165,0),(140,90,75,50))  # Orange leaderboard button
    render_text_message("Start", 20+37, 150+25, 20)
    render_text_message("Quit", 215+37,150+25, 20)
    render_text_message("Help",110+37,150+25, 20)
    render_text_message("Scores",140+37,90+25, 20)



def display_help_screen():
    intro = True
    while intro:
        pitft.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if 120 < pos[0] < 180 and 160 < pos[1] < 185:
                    return
        win.fill(clr_wht)
        render_text_message("HOW TO PLAY", 160, 40, 20)
        # Seeing the instructios
        render_text_message("Use joystick or buttons", 160, 80, 14)
        render_text_message("Catch as many balls as ",     160,100,14)
        render_text_message("you can, but",              160,120,14)
        render_text_message("avoid garbage!",            160,140,14)
        pygame.draw.rect(win, clr_brt_blu, (120,160,60,25))
        render_text_message("Back", 150, 170, 14)
        pygame.display.update()
        tmr.tick(15)




def display_main_menu():
    intro = True
    # Leaderboard can now be loaded 
    initialize_leaderboard()
    
    while intro:
        win.blit(bg, (0,0))
        render_text_message("BASKETBALL CATCHER", 160, 20, 20)
        render_text_message(f"Player: {current_uname}", 160, 50, 16)
        render_menu_elements()
        
        # Handle touch events for menu
        pitft.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                # Start button
                if 20 < pos[0] < 95 and 150 < pos[1] < 200:
                    return
                # Quit button
                elif 215 < pos[0] < 290 and 150 < pos[1] < 200:
                    cleanup_and_exit()
                # Help button
                elif 110 < pos[0] < 185 and 150 < pos[1] < 200:
                    display_help_screen()
                # Leaderboard button
                elif 140 < pos[0] < 215 and 90 < pos[1] < 140:
                    show_leaderboard_screen()
                # Change name area to click on player name
                elif 120 < pos[0] < 200 and 40 < pos[1] < 60:
                    prompt_for_username()
                    
        pygame.display.update()
        tmr.tick(15)



def display_game_over_screen(scr, reason):
    print("Entering show_game_over function")
    # Game over screen can come o 
    win.fill(clr_blk)
    render_text_message("Game Over!",     disp_w//2, disp_h//2-50, 30)
    render_text_message(f"Final Score: {scr}", disp_w//2, disp_h//2- 25, 25)
    render_text_message(f"Player: {current_uname}", disp_w//2, disp_h//2, 20)
    if reason:
        render_text_message(f"Reason: {reason}", disp_w//2, disp_h//2+25, 16)
    
    # Save score to leaderboard for us 
    print("Game over screen - saving final score")
    record_player_score(current_uname, scr)
    
    # press any key can now pulsate on and off 
    start_time = time.time()
    print("Waiting for key press to continue")
    waiting = True
    
    while waiting:
        pitft.update()
        # Clear only the bottom portion for animated message
        pygame.draw.rect(win, clr_blk, (0, disp_h//2+40, disp_w, 40))
        
        # Calculating pulsing effect for message
        elapsed = time.time() - start_time
        pulse = abs(math.sin(elapsed * 3))
        
        # Changing color based on made pulse
        color = (int(255*pulse), int(255*pulse), 255)
        
        # Render with our color
        font = pygame.font.Font("freesansbold.ttf", 18)
        text = font.render("PRESS ANY KEY TO CONTINUE", True, color)
        text_rect = text.get_rect(center=(disp_w//2, disp_h//2+50))
        win.blit(text, text_rect)
        
        pygame.display.update()
        
        # see if there are button presses on the PiTFT
        for pin in PIN_NUMBERS:
            if GPIO.input(pin) == GPIO.LOW:
                print(f"Button {pin} pressed, we can go through continuing")
                waiting = False
                break
        
        # touch events can also be checked 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("Quit event received during game over screen")
                cleanup_and_exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                print("Touch received, continuing")
                waiting = False
            if event.type == pygame.KEYDOWN:
                print("Key press received, continuing")
                waiting = False
        
        # delay
        pygame.time.delay(50)
    
    
    print("Exiting show_game_over function")
    # back to main menu
    return
        
       



def run_game_loop():
    global play
    
    plyr_scr = 0
    act_bballs = []
    act_obsts = []
    ball_spwn_tmr = 0
    obst_spwn_tmr = 0
    

    ball_base_vel = 5

    basket = HoopController(disp_w*0.35, disp_h-50)
    play   = True
    curr_lvl  = 1
    gmovr_reason = None  
    
    # level thresholds and parameters for us
    lvl_thresh = [15, 30]
    lvl_sets = {
        1: {"basket_vel": 10, "add_basketball_rate":30, "basketball_vel": 5, "garbage_vel":2,  "add_garbage_rate":100, "garbage_amount":1},
        2: {"basket_vel": 12, "add_basketball_rate":25, "basketball_vel": 7, "garbage_vel":4,  "add_garbage_rate":85,  "garbage_amount":2},
        3: {"basket_vel": 15, "add_basketball_rate":20, "basketball_vel": 9, "garbage_vel":6,  "add_garbage_rate":70,  "garbage_amount":3}
    }

    curr_spds = lvl_sets[curr_lvl]
    basket.spd   = curr_spds["basket_vel"]

    # Main game loop described
    while play:
        pitft.update()
        # handle Pygame quit functionality 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                play = False
                cleanup_and_exit()
    
        # PiTFT joystick controls based on GPIO pin checks
        if GPIO.input(ltfs_ctrl_pin) == GPIO.LOW and basket.pos_x > basket.spd-5:
            basket.pos_x -= basket.spd
        elif GPIO.input(rtfs_ctrl_pin) == GPIO.LOW and basket.pos_x < disp_w - basket.spd - 50:
            basket.pos_x += basket.spd
            
        # We can see touchscreen as well for movement
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                touch_x = event.pos[0]
                # Move left or right based on having the touch position
                if touch_x < disp_w // 2:
                    if basket.pos_x > basket.spd-5:
                        basket.pos_x -= basket.spd
                else:
                    if basket.pos_x < disp_w - basket.spd - 50:
                        basket.pos_x += basket.spd

        win.blit(bg, (0,0))

        
        
        # basketball can spawn
        ball_spwn_tmr += 1
        if ball_spwn_tmr >= curr_spds["add_basketball_rate"]:
            ball_spwn_tmr = 0
            ball_spwn_x = random.randrange(100, disp_w-100)
            ball_spwn_y = 0
            act_bballs.append(Ball(ball_spwn_x, ball_spwn_y, 0))

        # spawn garbage
        obst_spwn_tmr += 1
        if obst_spwn_tmr >= curr_spds["add_garbage_rate"]:
            obst_spwn_tmr = 0
            for _ in range(curr_spds["garbage_amount"]):
                obst_spwn_x = random.randrange(100, disp_w-100)
                obst_spwn_y = 0
                act_obsts.append(Obstacle(obst_spwn_x, obst_spwn_y, 0))

        # lets allow for the basketballs to be drawn ad moved
        for ball in act_bballs:
            ball.draw(win)
            ball.pos_y += curr_spds["basketball_vel"]  
            
        # catch logic
        for item in act_bballs[:]:
            hitbox = item.get_hitbox()
            center_x = hitbox[0] + hitbox[2]//2
            center_y = hitbox[1] + hitbox[3]//2
            
            basket_hitbox = basket.get_hitbox()
            if (basket_hitbox[0] <= center_x <= basket_hitbox[0]+basket_hitbox[2] and
                basket_hitbox[1] <= center_y <= basket_hitbox[1]+basket_hitbox[3]):
                act_bballs.remove(item)
                plyr_scr += 1
            # Remove now if it is off the screen
            if item.pos_y > disp_h:
                act_bballs.remove(item)

        # drawing as well as moving the garbage
        for obstacle in act_obsts:
            
            obstacle.draw(win)
            obstacle.pos_y += curr_spds["garbage_vel"]
        
        # Check for garbage collision with basket for us 
        end_game = False
        for obstacle in act_obsts[:]:
            hitbox = obstacle.get_hitbox()
            
            obst_ctr_x = hitbox[0] + hitbox[2]//2
            obst_ctr_y = hitbox[1] + hitbox[3]//2
            
            
            basket_hitbox = basket.get_hitbox()
            bskt_lft = basket_hitbox[0]
            
            bskt_rght = basket_hitbox[0] + basket_hitbox[2]
            
            bskt_top = basket_hitbox[1]
            bskt_btm = basket_hitbox[1] + basket_hitbox[3]
            
            # Check if garbage center becomes inside basket
            if (bskt_lft <= obst_ctr_x <= bskt_rght and bskt_top <= obst_ctr_y <= bskt_btm):
                # Game over when garbage hits
                print(f"Game over! Garbage hit.")
                print(f"Basket hitbox: {basket_hitbox}")
                print(f"Garbage position: ({obst_ctr_x}, {obst_ctr_y})")
                print(f"Basket left={bskt_lft}, right={bskt_rght}, top={bskt_top}, bottom={bskt_btm}")
                
                play = False
                
                end_game = True
                
                print("Setting end_game to True, will break loop")
                
                # Garbage has indicator hit for it in red
                win.fill((255, 0, 0))  
                render_text_message("GARBAGE COLLECTED!", disp_w//2, disp_h//2, 24)
                pygame.display.update()
                
                time.sleep(1)  
                
                gmovr_reason = "Garbage collected"
                break
            # Taking away when off the screen
            if obstacle.pos_y > disp_h:
                act_obsts.remove(obstacle)
        
        
        
        # Force game to end when garbage is hit
        if end_game:
            break

        # level up can be done
        if curr_lvl < 3 and plyr_scr >= lvl_thresh[curr_lvl-1]:
            curr_lvl += 1
            curr_spds = lvl_sets[curr_lvl]
            basket.spd   = curr_spds["basket_vel"]
            
            render_text_message(f"Level {curr_lvl}!", disp_w//2, disp_h//2, 30)
            pygame.display.update()
            time.sleep(1.5)

        # HUD for our game
        render_text_message(f"Level: {curr_lvl}", 50, 20, 16)
        render_text_message(f"Score: {plyr_scr}",  50, 40, 16)
        basket.draw(win)

        pygame.display.update()
        tmr.tick(60)

    
    
    # game over screen can be shpwn to us 
    print("Main game loop ended, showing game over screen now")
    display_game_over_screen(plyr_scr, gmovr_reason)
    
    print("Game over screen completed, returning to main menu for us ")
    return



if __name__ == "__main__":
    # leaderboard now initialized
    initialize_leaderboard()
    prompt_for_username()
    
    # Main game loop for the game play
    running = True
    while running:
        print("\n Starting new game session here")
        display_main_menu()  
        
        print("Menu completed, we are now starting game")
        run_game_loop()        
        
        print("Game completed, we can go back to main loop")
        
