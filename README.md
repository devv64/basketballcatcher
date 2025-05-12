# Basketball Catcher Game

A simple game where you control a basket and catch basketballs while avoiding garbage.

## Features

- Username input for personalized gameplay
- Persistent leaderboard for top scores
- Three difficulty levels that increase as you score points
- Works on both desktop and Raspberry Pi with PiTFT display

## Requirements

- Python 3
- Pygame
- Raspberry Pi with PiTFT (for PiTFT version)

## Running the Game

### Desktop Version

To run the desktop version of the game:

```bash
# Activate virtual environment (if used)
source venv/bin/activate

# Run the game
python main.py
```

### PiTFT Version (Raspberry Pi)

To run the game on a Raspberry Pi with PiTFT display:

```bash
# Make sure you have RPi.GPIO installed
pip install RPi.GPIO

# Run the PiTFT version
sudo python pitft_game.py
```

Note: The PiTFT version requires root privileges to access GPIO pins.

## Controls

### Desktop Version
- Left/Right arrow keys: Move basket
- Mouse: Click menu options

### PiTFT Version
- Left/Right joystick (GPIO pins 5 and 19): Move basket
- Touchscreen: Tap left/right half of screen to move
- Physical buttons: Exit game (buttons on pins 17, 22, 23, 27)
- Touchscreen: Tap menu options

## Gameplay

1. Enter your username
2. Navigate the main menu
3. Catch basketballs to score points
4. Avoid catching garbage - game ends if you catch it
5. Reach score thresholds to advance to more difficult levels
6. View the leaderboard to see top scores

## Customization

You can modify game parameters in the code:
- Speed settings for each level
- Scoring thresholds
- Visual elements

## Files

- `main.py` - Desktop version of the game
- `pitft_game.py` - PiTFT version for Raspberry Pi
- `basketball.png` - Basketball image
- `garbage.jpg` - Garbage image
- `basket.png` - Basket image
- `background.jpg` - Background image
- `leaderboard.json` - Saved leaderboard data (created automatically) # basketballcatcher
