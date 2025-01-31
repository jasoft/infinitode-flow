import cv2
import logging
import numpy as np
import pygetwindow as gw
import pyautogui
import time
import keyboard
import pydirectinput as di

# 配置日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# 设置合成按钮、最大数量按钮和确定按钮的坐标
SYNTHESIS_BUTTON = (2578, 1776)
MAX_QUANTITY_BUTTON = (2444, 1673)
CONFIRM_BUTTON = (2210, 1832)
CANCEL_BUTTON = (2436, 1814)

PROGRESS_BAR = (1959, 1618)
CLICK_DELAY = 0.5


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


# 查找界面上的所有方框
def find_boxes(screenshot):
    # 转换为灰度图
    gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    # 边缘检测
    edges = cv2.Canny(gray, 50, 150)
    # 查找轮廓
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for contour in contours:
        # 获取轮廓的边界框
        x, y, w, h = cv2.boundingRect(contour)
        # 过滤宽度小于100或高度小于100，或宽度大于300或高度大于300的框
        if 100 <= w <= 300 and 100 <= h <= 300:
            boxes.append((x, y, w, h))

    # 过滤重叠的方框
    filtered_boxes = []
    for box in boxes:
        x1, y1, w1, h1 = box
        keep = True
        for other_box in boxes:
            if box == other_box:
                continue
            x2, y2, w2, h2 = other_box
            if (
                x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2
            ):  # 检查是否重叠
                overlap_area = (min(x1 + w1, x2 + w2) - max(x1, x2)) * (
                    min(y1 + h1, y2 + h2) - max(y1, y2)
                )
                box_area = w1 * h1
                other_box_area = w2 * h2
                if overlap_area / box_area > 0.5 or overlap_area / other_box_area > 0.5:
                    if box_area < other_box_area:
                        keep = False
                        break
        if keep:
            filtered_boxes.append(box)

    return filtered_boxes


# 按从下到上、从右到左排序方框
def sort_boxes(boxes):
    # 先按y坐标从大到小排序（从下到上）
    boxes.sort(key=lambda box: box[1], reverse=True)
    # 再按y坐标分组后，按x坐标从大到小排序（从右到左）
    sorted_boxes = []
    current_y = None
    current_row = []
    for box in boxes:
        if (
            current_y is None or abs(box[1] - current_y) < 10
        ):  # 假设同一排的y坐标差异不超过10
            current_row.append(box)
            current_y = box[1]
        else:
            current_row.sort(key=lambda box: box[0], reverse=True)
            sorted_boxes.extend(current_row)
            current_row = [box]
            current_y = box[1]
    if current_row:
        current_row.sort(key=lambda box: box[0], reverse=True)
        sorted_boxes.extend(current_row)
    return sorted_boxes


# 点击方框中心点
def click_box_center(box):
    x, y, w, h = box
    center_x = x + w // 2
    center_y = y + h // 2
    di.click(center_x, center_y)
    logging.info(f"点击方框中心点: ({center_x}, {center_y})")


# 主程序
def main():
    logging.info("程序开始")

    # 窗口标题（根据实际窗口名称修改）
    window_title = "Infinitode 2"
    if not activate_window(window_title):
        return

    # 检测到esc按下则退出循环
    # 截取窗口区域
    screenshot = np.array(pyautogui.screenshot())
    # 查找方框
    boxes = find_boxes(screenshot)
    if not boxes:
        print("未找到方框，退出程序")
        return

    # 排序方框
    sorted_boxes = sort_boxes(boxes)
    # 在窗口上画出boxes并标注顺序号
    # for i, box in enumerate(sorted_boxes):
    #     x, y, w, h = box
    #     cv2.rectangle(screenshot, (x, y), (x + w, y + h), (0, 255, 0), 2)
    #     cv2.putText(
    #         screenshot,
    #         str(i + 1),
    #         (x, y - 10),
    #         cv2.FONT_HERSHEY_SIMPLEX,
    #         0.9,
    #         (0, 255, 0),
    #         2,
    #     )

    # # 显示带有方框和顺序号的图像
    # cv2.imshow("Boxes with Order", screenshot)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # 遍历方框并点击
    for box in sorted_boxes:
        if keyboard.is_pressed("esc"):
            logging.info("检测到ESC按下，退出程序")
            return

        click_box_center(box)
        # 点击合成按钮
        logging.info("点击合成按钮")
        di.click(*SYNTHESIS_BUTTON)
        # 检查进度条颜色
        progress_bar_exists = pyautogui.pixelMatchesColor(
            *PROGRESS_BAR, (0x22, 0x22, 0x22)
        )
        logging.debug(f"进度条颜色: {pyautogui.pixel(*PROGRESS_BAR)}")
        if not progress_bar_exists:
            pyautogui.click(*CANCEL_BUTTON)
            time.sleep(1)
            logging.info("进度条颜色不匹配，点击取消按钮")
            continue

        # 点击最大数量按钮
        logging.info("找到进度条,点击最大数量按钮")
        di.click(*MAX_QUANTITY_BUTTON)

        # 点击确定按钮
        logging.info("点击确定按钮")
        di.click(*CONFIRM_BUTTON)


if __name__ == "__main__":
    main()
