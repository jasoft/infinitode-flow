import time
import logging
import pyautogui
import pydirectinput as di
import pyautogui
import asyncio
import pygetwindow as gw

CLICK_DELAY = 0.2

# 配置日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def log_click(point, action):
    logging.info(f"{action} at coordinates: ({point[0]}, {point[1]})")


# Override pyautogui.click to log all clicks
original_click = di.click


def logged_click(*args, **kwargs):
    if len(args) >= 2:
        log_click((args[0], args[1]), "Clicked")
    logging.debug(f"{args, kwargs}")

    original_click(*args, **kwargs)
    time.sleep(CLICK_DELAY)


di.click = logged_click


# 激活Infinitode 2窗口
def activate_window(title):
    try:
        window = gw.getWindowsWithTitle(title)[0]
        if window:
            window.maximize()
            window.activate()
            time.sleep(1)  # 等待窗口激活
            return True
        else:
            print(f"未找到窗口: {title}")
            return False
    except Exception as e:
        print(f"激活窗口失败: {e}")
        return False


# 棋盘参数
cellsize = 90
boardcenter = (1920, 1010)


async def element_exists(element):
    logging.info(f"查找 {element}")
    try:
        await asyncio.to_thread(
            pyautogui.locateOnScreen, f"elements/{element}.png", confidence=0.9
        )
        logging.info(f"找到 {element}")
        return True
    except Exception:
        logging.info(f"没有找到 {element}")
        return False


async def click_element(image_file, confidence=0.9, waitUntilSuccess=True):
    while True:
        try:
            logging.info(f"查找 {image_file}")
            element = await asyncio.to_thread(
                pyautogui.locateOnScreen,
                f"elements/{image_file}.png",
                minSearchTime=3,
                confidence=confidence,
            )
            if element:
                element_center = pyautogui.center(element)
                di.click(element_center.x, element_center.y)
                logging.info(f"点击 {image_file}")
                return True
        except Exception:
            logging.info(f"没有找到 {image_file}")
            if not waitUntilSuccess:
                return False
        await asyncio.sleep(1)
