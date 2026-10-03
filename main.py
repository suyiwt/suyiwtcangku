# 【必须放在最前面】关闭Kivy崩溃报告
import os
os.environ['KIVY_NO_BUGREPORT'] = '1'
os.environ['KIVY_NO_CONSOLELOG'] = '1'
os.environ["KIVY_METRICS_DENSITY"] = "1"

import kivy
kivy.require('2.3.0')
import platform
import threading
import time
from datetime import datetime, timedelta
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy.graphics import Color, Rectangle

# plyer 安卓原生接口
try:
    from plyer import notification, vibrator
    plyer_available = True
except Exception:
    plyer_available = False

# Windows 蜂鸣
try:
    import winsound
except ImportError:
    winsound = None


class TimerLogic:
    def __init__(self):
        self.remaining_seconds = 0
        self.is_running = False
        self.total_seconds = 0
        self.initial_elapsed = 0
        self.started_at = None
        self.target_pct = 81
        self._thread = None
        self._stop_event = threading.Event()

    def start_calc(self, delivery_h, elapsed_h, elapsed_m, target_pct):
        try:
            d_hours = float(delivery_h) if delivery_h else 0
            e_hours = float(elapsed_h) if elapsed_h else 0
            e_mins = float(elapsed_m) if elapsed_m else 0
            target = float(target_pct) if target_pct else 0

            self.total_seconds = int(d_hours * 3600)
            self.initial_elapsed = int(e_hours * 3600) + int(e_mins * 60)
            self.target_pct = int(target)

            if self.total_seconds <= 0:
                return -1, "Delivery time must be greater than 0,baby!."

            alert_point = int(self.total_seconds * target / 100.0)

            if self.initial_elapsed >= alert_point:
                return -1, f"Elapsed time has already reached {int(target)}% mark.Check input."

            self.remaining_seconds = alert_point - self.initial_elapsed
            self.started_at = datetime.now()
            self.is_running = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._countdown_thread, daemon=True)
            self._thread.start()

            eta = self.started_at + timedelta(seconds=self.remaining_seconds)
            msg = (f"Started\n"
                   f"Total:{self.total_seconds}s\n"
                   f"Target:{int(target)}% ({alert_point}s)\n"
                   f"Remaining:{self.remaining_seconds}s\n"
                   f"ETA:{eta.strftime('%H:%M:%S')}")
            return 0, msg
        except ValueError:
            return -1, "Input contains invalid characters"

    def _countdown_thread(self):
        while self.is_running and not self._stop_event.is_set():
            time.sleep(1)
            if self.remaining_seconds > 0:
                self.remaining_seconds -= 1
            else:
                self.is_running = False
                break

    def stop(self):
        self.is_running = False
        self._stop_event.set()

    def get_current_progress(self):
        if self.total_seconds <= 0:
            return 0.0
        if self.started_at and self.is_running:
            elapsed_now = self.initial_elapsed + int((datetime.now() - self.started_at).total_seconds())
        else:
            elapsed_now = self.initial_elapsed
        pct = elapsed_now / self.total_seconds * 100.0
        return min(pct, 100.0)

    def get_eta(self):
        if not self.started_at or not self.is_running:
            return None
        return self.started_at + timedelta(seconds=self.remaining_seconds)


class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = 12
        self.padding = [20, 20, 20, 20]
        self.logic = TimerLogic()
        self.trigger_target_reached = False
        self.flash_active = False
        self.flash_color_state = False

        # 标题
        self.add_widget(Label(text="ITSC Ticket Timer V1", font_size="20sp", bold=True, size_hint_y=None, height=40))

        # 输入区域
        input_box = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None, height=170)
        row1 = BoxLayout(size_hint_y=None, height=45)
        row1.add_widget(Label(text=" Total Delivery(hour):", size_hint_x=0.4))
        self.input_delivery = TextInput(text="2.1", font_size="18sp", multiline=False, input_filter="float")
        row1.add_widget(self.input_delivery)
        input_box.add_widget(row1)

        row2 = BoxLayout(size_hint_y=None, height=45)
        row2.add_widget(Label(text=" Elapsed(h):", size_hint_x=0.25))
        self.input_h = TextInput(text="1", font_size="18sp", multiline=False, input_filter="float")
        row2.add_widget(self.input_h)
        row2.add_widget(Label(text="(min):", size_hint_x=0.15))
        self.input_m = TextInput(text="40", font_size="18sp", multiline=False, input_filter="float")
        row2.add_widget(self.input_m)
        input_box.add_widget(row2)

        row3 = BoxLayout(orientation="vertical", size_hint_y=None, height=70)
        self.slider_label = Label(text="Target progress:81%", font_size="14sp", size_hint_y=None, height=22)
        self.slider_target = Slider(min=1, max=100, value=81, step=1)
        self.slider_target.bind(value=self.on_slider_change)
        row3.add_widget(self.slider_label)
        row3.add_widget(self.slider_target)
        input_box.add_widget(row3)
        self.add_widget(input_box)

        self.input_delivery.bind(text=self.on_input_change)
        self.input_h.bind(text=self.on_input_change)
        self.input_m.bind(text=self.on_input_change)

        # 按钮区域
        btn_box = BoxLayout(size_hint_y=None, height=55, spacing=20)
        self.btn_start = Button(text="Start Timer", background_color=(0.3, 0.8, 0.3, 1))
        self.btn_stop = Button(text="Stop", background_color=(0.8, 0.3, 0.3, 1))
        self.btn_start.bind(on_press=self.on_start)
        self.btn_stop.bind(on_press=self.on_stop)
        btn_box.add_widget(self.btn_start)
        btn_box.add_widget(self.btn_stop)
        self.add_widget(btn_box)

        # 信息展示区
        info_box = BoxLayout(orientation="vertical", spacing=14)
        # Now
        time_row_now = BoxLayout(size_hint_y=None, height=36, spacing=10)
        time_row_now.add_widget(Label(text="Now", font_size="14sp", color=(0.5,0.5,0.5,1), size_hint_x=0.3))
        self.lbl_now_val = Label(text="--:--:--", font_size="18sp", color=(0.9,0.9,0.9,1), size_hint_x=0.7, halign="right")
        time_row_now.add_widget(self.lbl_now_val)
        info_box.add_widget(time_row_now)

        # Finish
        time_row_finish = BoxLayout(size_hint_y=None, height=36, spacing=10)
        time_row_finish.add_widget(Label(text="Finish", font_size="14sp", color=(0.5,0.5,0.5,1), size_hint_x=0.3))
        self.lbl_finish_val = Label(text="--:--:--", font_size="18sp", color=(1,0.7,0.2,1), size_hint_x=0.7, halign="right")
        time_row_finish.add_widget(self.lbl_finish_val)
        info_box.add_widget(time_row_finish)

        self.lbl_current_pct = Label(text="Current Progress: 0.0%", font_size="16sp", color=(0.2,0.4,0.8,1), bold=True, size_hint_y=None, height=32)
        info_box.add_widget(self.lbl_current_pct)
        self.lbl_progress = Label(text="Target Threshold:81%", font_size="16sp", color=(0.2,0.4,0.8,1), bold=True, size_hint_y=None, height=32)
        info_box.add_widget(self.lbl_progress)
        self.lbl_result = Label(text="--:--:--", font_size="48sp", color=(0.2,0.2,0.8,1), bold=True, size_hint_y=None, height=70)
        info_box.add_widget(self.lbl_result)
        self.add_widget(info_box)

        Clock.schedule_interval(self.update_ui, 0.5)
        self.calc_preview_progress()
        # 屏幕闪烁定时器
        self.flash_clock = Clock.schedule_interval(self.flash_screen, 0.4)

    def flash_screen(self, dt):
        if not self.flash_active:
            self.canvas.before.clear()
            return
        with self.canvas.before:
            self.canvas.before.clear()
            if self.flash_color_state:
                Color(1,0,0,0.4)
            else:
                Color(0,0,0,0)
            Rectangle(pos=self.pos, size=self.size)
        self.flash_color_state = not self.flash_color_state

    def on_slider_change(self, instance, value):
        target = int(value)
        self.slider_label.text = f"Target Progress:{target}%"
        self.lbl_progress.text = f"Target Threshold: {target}%"
        self.calc_preview_progress()

    def on_input_change(self, instance, value):
        self.calc_preview_progress()

    def calc_preview_progress(self):
        try:
            d_h = float(self.input_delivery.text)
            e_h = float(self.input_h.text)
            e_m = float(self.input_m.text)
            total_sec = d_h * 3600
            elapsed_sec = e_h * 3600 + e_m * 60
            if total_sec <= 0:
                preview_pct = 0.0
            else:
                preview_pct = (elapsed_sec / total_sec) * 100
                preview_pct = min(preview_pct,100.0)
            self.lbl_current_pct.text = f"Current Progress: {preview_pct:.1f}%"
        except ValueError:
            self.lbl_current_pct.text = "Current Progress: 0.0%"

    def on_start(self, instance):
        d = self.input_delivery.text
        h = self.input_h.text
        m = self.input_m.text
        target = int(self.slider_target.value)
        status_code, msg = self.logic.start_calc(d, h, m, target)
        if status_code == -1:
            self.show_popup("Error", msg)
            return
        self.btn_start.disabled = True
        self.btn_stop.disabled = False
        self.trigger_target_reached = False
        self.flash_active = False

    def on_stop(self, instance):
        self.logic.stop()
        self.lbl_result.text = "stopped"
        self.lbl_result.color = (0.5, 0.5, 0.5, 1)
        self.lbl_result.font_size = "36sp"
        self.btn_start.disabled = False
        self.btn_stop.disabled = True
        self.calc_preview_progress()
        self.flash_active = False

    @mainthread
    def on_target_reached(self):
        if self.trigger_target_reached:
            return
        self.trigger_target_reached = True
        target = self.logic.target_pct
        self.lbl_result.text = f"TARGET {target}% HIT!"
        self.lbl_result.font_size = "30sp"
        self.lbl_result.color = (1, 0.3, 0, 1)
        self.flash_active = True  # 开启屏幕闪烁

        # 跨平台提醒
        if plyer_available:
            # 安卓系统消息通知
            notification.notify(title="Timer Alert", message="Target Progress Reached!", app_name="ITSC Timer")
            # 持续震动（安卓，震动2秒，间隔1秒循环）
            threading.Thread(target=self.vibrate_loop, daemon=True).start()
            # 播放系统铃声提示音
            try:
                notification.notify(title="Timer Alert", message="Target Progress Reached!", app_name="ITSC Timer", sound=True)
            except Exception:
                pass
        else:
            # Windows电脑端蜂鸣
            if winsound:
                winsound.Beep(1000, 800)

        Clock.schedule_once(lambda dt: self._show_alert_popup(target), 0.3)
        self.logic.stop()

    def vibrate_loop(self):
        # 循环震动，持续10秒后自动停止
        stop_time = time.time() + 10
        while time.time() < stop_time:
            try:
                vibrator.vibrate(2)
                time.sleep(1)
            except Exception:
                break

    def _show_alert_popup(self, target):
        content = BoxLayout(orientation="vertical", spacing=10, padding=20)
        content.add_widget(Label(text=f"Target {target}% Reached", font_size="22sp", bold=True, color=(1, 0.3, 0, 1)))
        content.add_widget(Label(text=f"Please take action now.", font_size="16sp", halign="center"))
        btn = Button(text="ok", size_hint_y=None, height=50, background_color=(1, 0.3, 0, 1))
        btn.bind(on_press=self.on_popup_ok)
        content.add_widget(btn)
        popup = Popup(title="Reminder", content=content, size_hint=(None, None), size=(320, 250), auto_dismiss=False)
        popup.open()
        self.popup_ref = popup

    def on_popup_ok(self, inst):
        self.popup_ref.dismiss()
        self.flash_active = False  # 关闭屏幕闪烁

    def update_ui(self, dt):
        now = datetime.now()
        self.lbl_now_val.text = now.strftime("%H:%M:%S")
        if not self.logic.is_running:
            return

        progress = self.logic.get_current_progress()
        target = self.logic.target_pct
        self.lbl_current_pct.text = f"Current Progress: {progress:.1f}%"

        if progress >= target:
            self.on_target_reached()
            return

        if progress >= target * 0.8:
            color = (1, 0.6, 0, 1)
        else:
            color = (0.2, 0.4, 0.8, 1)

        self.lbl_current_pct.color = color
        self.lbl_progress.text = f"Target Threshold: {target}%"
        self.lbl_progress.color = color

        finish_time = self.logic.get_eta()
        if finish_time:
            self.lbl_finish_val.text = finish_time.strftime("%H:%M:%S")
        else:
            self.lbl_finish_val.text = "__:__:__"

        sec = int(self.logic.remaining_seconds)
        h = sec // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        self.lbl_result.text = f"{h:02d}:{m:02d}:{s:02d}"
        self.lbl_result.font_size = "48sp"
        self.lbl_result.color = (0, 0.8, 0, 1)

    def show_popup(self, title, msg):
        content = Label(text=msg, font_size="15sp")
        popup = Popup(title=title, content=content, size_hint=(None, None), size=(300, 200))
        popup.open()


class TimerApp(App):
    def build(self):
        Window.size = (520, 680)
        return MainLayout()


if __name__ == "__main__":
    TimerApp().run()
