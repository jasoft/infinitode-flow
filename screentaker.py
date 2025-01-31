import time
import os
from PIL import ImageGrab


def take_screenshot():
    screenshot_dir = "screenshot"
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)

    while True:
        screenshot = ImageGrab.grab()
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        screenshot.save(os.path.join(screenshot_dir, f"screenshot_{timestamp}.png"))
        time.sleep(5)


if __name__ == "__main__":
    take_screenshot()
