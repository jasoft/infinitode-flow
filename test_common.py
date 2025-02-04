import unittest
from common import resize_window
import pygetwindow as gw
import time
from common import GameBot


class TestCommonFunctions(unittest.TestCase):
    def test_resize_window(self):
        # 假设测试窗口的标题为 "Test Window"
        test_window_title = "Infinitode 2"

        # 创建一个测试窗口（仅用于测试目的，实际应用中需要确保窗口存在）
        test_window = gw.getWindowsWithTitle(test_window_title)[0]
        test_window.resizeTo(800, 600)  # 初始大小

        # 调用函数调整窗口大小
        result = resize_window(test_window_title, 1920, 1080)

        # 获取调整后的窗口大小
        resized_window = gw.getWindowsWithTitle(test_window_title)[0]
        width, height = resized_window.size

        # 断言函数返回值为 True
        self.assertTrue(result)

        # 断言窗口大小已调整为 1920x1080
        self.assertEqual(width, 1920)
        self.assertEqual(height, 1080)

    def test_click_in_window(self):
        window_title = "Infinitode 2"

        # 激活窗口
        controller = GameBot(window_title)
        controller.resize(1920, 1080)
        controller.activate()

        # 尝试点击几个窗口内的点
        points_to_click = [(100, 100), (200, 200), (300, 300)]

        for point in points_to_click:
            controller.click(point[0], point[1])
            time.sleep(1)  # 等待一秒观察点击效果


if __name__ == "__main__":
    unittest.main()
