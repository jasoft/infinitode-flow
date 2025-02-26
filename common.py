import os
import time
import logging
import pyautogui
import pydirectinput as di
import asyncio
import pygetwindow as gw

CLICK_DELAY = 0.5

# 配置日志记录
logging.basicConfig(
    filename="infinitodebot.log",
    encoding="utf-8",
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
            window.activate()
            time.sleep(1)  # 等待窗口激活
            return True
        else:
            print(f"未找到窗口: {title}")
            return False
    except Exception as e:
        print(f"激活窗口失败: {e}")
        return False


def resize_window(title, w, h):
    try:
        window = gw.getWindowsWithTitle(title)[0]
        if window:
            window.resizeTo(w, h)
            window.activate()
            time.sleep(1)  # 等待窗口调整大小
            return True
        else:
            print(f"未找到窗口: {title}")
            return False
    except Exception as e:
        print(f"调整窗口大小失败: {e}")
        return False


# 棋盘参数
cellsize = 90
boardcenter = (1920, 1010)


class GameBot:
    def __init__(self, title, elements_path="elements"):
        self.title = title
        self.window = self._get_window()
        self.elements_path = elements_path

    def _get_window(self):
        try:
            window = gw.getWindowsWithTitle(self.title)[0]
            if window:
                return window
            else:
                raise Exception(f"未找到窗口: {self.title}")
        except Exception as e:
            raise Exception(f"获取窗口失败: {e}")

    async def click(self, x, y):
        if self.window:
            window_left, window_top = self.window.left, self.window.top
            click_x, click_y = window_left + x, window_top + y
            await asyncio.to_thread(di.click, click_x, click_y)
        else:
            raise Exception(f"窗口未激活: {self.title}")

    def activate(self):
        self.window.activate()

    def resize(self, w, h):
        self.window.resizeTo(w, h)

    async def element_exists(self, element):
        logging.debug(f"查找 {element}")
        try:
            await asyncio.to_thread(
                pyautogui.locateOnWindow,
                os.path.join(self.elements_path, f"{element}.png"),
                self.title,
                confidence=0.9,
            )
            logging.debug(f"找到 {element}")
            return True
        except Exception:
            logging.debug(f"没有找到 {element}")
            return False

    async def find_element(self, element):
        logging.info(f"查找 {element}")
        try:
            element_box = await asyncio.to_thread(
                pyautogui.locateOnWindow,
                os.path.join(self.elements_path, f"{element}.png"),
                self.title,
                confidence=0.9,
            )
            if element_box:
                element_center = pyautogui.center(element_box)
                logging.info(f"找到 {element_box}")
                return element_center
        except Exception:
            logging.info(f"没有找到 {element_box}")
            return None

    async def click_element(self, image_file, confidence=0.9, waitUntilSuccess=True):
        # TODO: search from window region
        while True:
            try:
                logging.debug(f"查找 {image_file}")
                element = await asyncio.to_thread(
                    pyautogui.locateOnWindow,
                    f"{self.elements_path}/{image_file}.png",
                    self.title,
                    minSearchTime=3,
                    confidence=confidence,
                )
                if element:
                    element_center = pyautogui.center(element)
                    di.click(element_center.x, element_center.y)
                    logging.info(f"点击 {image_file}")
                    return True
            except Exception:
                logging.debug(f"没有找到 {image_file}")
                if not waitUntilSuccess:
                    return False
            await asyncio.sleep(1)
