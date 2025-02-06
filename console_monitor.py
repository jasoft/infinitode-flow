# language: python
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

    def render(self):
        with self._lock:
            # 拼接 status_history 为多行文本
            status_lines = "\n".join(
                f"[{color}]{text}[/{color}]" for text, color in self.status_history
            )
        status_panel = Panel(
            status_lines if status_lines else "无状态信息",
            title="Bot 当前状态",
            border_style="blue",
        )
        return Group(status_panel, self.progress)

    def start(self, refresh_interval=0.1):
        self._running = True
        # Live 运行在当前线程，会阻塞，因此使用后台线程启动
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

    try:
        while True:
            # 每隔 0.5 秒更新状态
            monitor.update_status(
                f"当前状态更新：{random.randint(0, 100)}", color=random.choice(colors)
            )
            time.sleep(0.5)
            # 每隔 5 秒动态更新倒计时时间
            if random.random() < 0.1:
                new_countdown_time = random.randint(10, 30)
                monitor.set_countdown_time(new_countdown_time)
                monitor.update_status(
                    f"倒计时时间更新为：{new_countdown_time}秒", color="blue"
                )
    except KeyboardInterrupt:
        monitor.stop()
        console.print("ConsoleMonitor 已停止")
