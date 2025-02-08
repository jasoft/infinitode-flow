# language: python
import asyncio
import time
import threading
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn

console = Console()


class ConsoleMonitor:
    def __init__(self, max_status=5, countdown_time=600):
        self.max_status = max_status
        self.status_history = []
        self.countdown_time = countdown_time
        self.remaining_time = countdown_time
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.fields[remaining_time]}s"),
            console=console,
            transient=True,
        )
        # 添加一个倒计时任务，总值为 countdown_time
        self.task = self.progress.add_task(
            "倒计时", total=self.countdown_time, remaining_time=self.remaining_time
        )
        self._lock = threading.Lock()
        self._running = False
        self._info = {}

    def update_status(self, status_text, color="white"):
        with self._lock:
            self.status_history.append((status_text, color))
            if len(self.status_history) > self.max_status:
                self.status_history.pop(0)

    def set_countdown(self, remaining_time):
        with self._lock:
            if remaining_time < 0:
                remaining_time = 0
            elif remaining_time > self.countdown_time:
                remaining_time = self.countdown_time
            self.remaining_time = remaining_time
            completed = self.countdown_time - self.remaining_time
            self.progress.update(
                self.task, remaining_time=self.remaining_time, completed=completed
            )

    def set_countdown_time(self, countdown_time):
        with self._lock:
            self.countdown_time = countdown_time
            self.remaining_time = countdown_time
            self.progress.update(
                self.task,
                total=self.countdown_time,
                remaining_time=self.remaining_time,
                completed=0,
            )

    def update_info(self, key, value):
        """更新固定信息"""
        with self._lock:
            self._info[key] = value

    def render(self):
        with self._lock:
            # 拼接 status_history 为多行文本
            status_lines = "\n".join(
                f"[{color}]{text}[/{color}]" for text, color in self.status_history
            )
            # 拼接固定信息为多行文本
            info_lines = "\n".join(
                f"[white]{k}: [yellow]{v}[/yellow][/white]"
                for k, v in self._info.items()
            )

        status_panel = Panel(
            status_lines if status_lines else "无状态信息",
            title="脚本运行监控",
            border_style="blue",
        )
        info_panel = Panel(
            info_lines if info_lines else "无信息",
            title="看板",
            border_style="green",
        )
        return Group(status_panel, info_panel, self.progress)

    def start(self, refresh_interval=0.1):
        self._running = True

        # Live 运行在当前线程
        thread = threading.Thread(
            target=self._live_loop, args=(refresh_interval,), daemon=True
        )
        thread.start()

    def _live_loop(self, refresh_interval):
        with Live(self.render(), console=console, auto_refresh=False) as live:
            while self._running:
                live.update(self.render())
                live.refresh()
                time.sleep(refresh_interval)
                with self._lock:
                    if self.remaining_time > 0:
                        self.remaining_time -= refresh_interval
                        if self.remaining_time < 0:
                            self.remaining_time = 0
                        completed = self.countdown_time - self.remaining_time
                        self.progress.update(
                            self.task,
                            remaining_time=int(self.remaining_time),
                            completed=completed,
                        )

    def stop(self):
        self._running = False


if __name__ == "__main__":
    monitor = ConsoleMonitor(max_status=5, countdown_time=200)
    monitor.start(refresh_interval=0.1)

    # 模拟状态和倒计时更新
    import random

    colors = ["cyan", "yellow", "green", "red", "magenta"]
    score = 0
    start_time = time.time()
    running = True  # 添加运行状态标志

    # 创建更新运行时间的线程
    def update_runtime():
        while running:  # 使用运行状态标志控制线程
            runtime = int(time.time() - start_time)
            hours = runtime // 3600
            minutes = (runtime % 3600) // 60
            seconds = runtime % 60
            monitor.update_info("运行时间", f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            time.sleep(1)

    runtime_thread = threading.Thread(target=update_runtime, daemon=True)
    runtime_thread.start()

    try:
        while True:
            # 每隔 0.5 秒更新状态
            monitor.update_status(
                f"当前状态更新：{random.randint(0, 100)}", color=random.choice(colors)
            )
            # 更新分数
            score += random.randint(10, 100)
            monitor.update_info("分数", score)
            monitor.update_info("金币", random.randint(100, 999))

            time.sleep(0.5)
            # 每隔随机时间更新倒计时
            if random.random() < 0.1:
                new_countdown_time = random.randint(10, 30)
                monitor.set_countdown_time(new_countdown_time)
                monitor.update_status(
                    f"倒计时时间更新为：{new_countdown_time}秒", color="blue"
                )
    except KeyboardInterrupt:
        running = False  # 设置运行状态为False
        runtime_thread.join(timeout=2)  # 等待计时线程结束，最多等待2秒
        monitor.stop()
        console.print("ConsoleMonitor 已停止")
