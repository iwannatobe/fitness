from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.properties import BooleanProperty
import os

import theme
import sounds

ICONS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons")
from assets.icon_map import EXERCISE_ICON_MAP

def _rgba_hex(color):
    r, g, b = int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
    return f"{r:02x}{g:02x}{b:02x}"

EXERCISE_COLORS = {
    "卧推": (0.94, 0.35, 0.25, 1), "深蹲": (0.90, 0.50, 0.18, 1),
    "硬拉": (0.84, 0.22, 0.28, 1), "引体向上": (0.93, 0.55, 0.15, 1),
    "杠铃划船": (0.78, 0.38, 0.22, 1), "推举": (0.88, 0.32, 0.34, 1),
    "哑铃弯举": (0.84, 0.44, 0.18, 1), "臂屈伸": (0.90, 0.28, 0.24, 1),
    "俯卧撑": (0.83, 0.34, 0.30, 1), "卷腹": (0.93, 0.40, 0.20, 1),
    "腿举": (0.80, 0.30, 0.34, 1), "飞鸟": (0.88, 0.45, 0.28, 1),
    "杠铃平板卧推": (0.94, 0.30, 0.22, 1), "哑铃上斜卧推": (0.92, 0.36, 0.26, 1),
    "哑铃侧平举": (0.88, 0.42, 0.30, 1), "绳索三头下压": (0.90, 0.32, 0.28, 1),
    "面拉": (0.85, 0.38, 0.32, 1), "坐姿杠铃肩推": (0.90, 0.34, 0.26, 1),
    "窄距卧推": (0.86, 0.36, 0.28, 1), "高位下拉": (0.78, 0.40, 0.24, 1),
    "坐姿绳索划船": (0.80, 0.42, 0.22, 1), "杠铃弯举": (0.82, 0.44, 0.20, 1),
    "锤式弯举": (0.84, 0.42, 0.18, 1), "单臂哑铃划船": (0.76, 0.40, 0.26, 1),
    "T杆划船": (0.78, 0.38, 0.24, 1), "上斜哑铃弯举": (0.82, 0.43, 0.20, 1),
    "反握弯举": (0.80, 0.44, 0.22, 1), "杠铃深蹲": (0.88, 0.48, 0.18, 1),
    "罗马尼亚硬拉": (0.82, 0.24, 0.30, 1), "坐姿腿弯举": (0.65, 0.38, 0.70, 1),
    "站姿提踵": (0.55, 0.48, 0.82, 1), "传统硬拉": (0.80, 0.20, 0.28, 1),
    "保加利亚分腿蹲": (0.60, 0.40, 0.74, 1), "俯卧腿弯举": (0.68, 0.36, 0.72, 1),
    "高脚杯深蹲": (0.62, 0.42, 0.76, 1), "坐姿提踵": (0.56, 0.46, 0.80, 1),
    "跑步": (0.20, 0.55, 0.88, 1), "游泳": (0.15, 0.60, 0.84, 1),
    "骑行": (0.24, 0.68, 0.58, 1), "椭圆机": (0.28, 0.54, 0.78, 1),
    "跳绳": (0.20, 0.64, 0.74, 1), "爬楼": (0.24, 0.50, 0.84, 1),
    "快走": (0.30, 0.60, 0.70, 1), "HIIT": (0.84, 0.24, 0.38, 1),
    "划船机": (0.18, 0.54, 0.80, 1), "登山": (0.38, 0.55, 0.60, 1),
    "滑雪": (0.14, 0.65, 0.88, 1), "瑜伽": (0.50, 0.38, 0.80, 1),
}

EXERCISE_ICONS = {
    "卧推": "\u25b2", "深蹲": "\u25bc", "硬拉": "\u25b2", "引体向上": "\u2191",
    "杠铃划船": "\u25c4", "推举": "\u25b2", "哑铃弯举": "\u25c6", "臂屈伸": "\u25bc",
    "俯卧撑": "\u25cf", "卷腹": "\u2605", "腿举": "\u25bc", "飞鸟": "\u25ba",
    "杠铃平板卧推": "\u25b2", "哑铃上斜卧推": "\u25b2", "哑铃侧平举": "\u25ba",
    "绳索三头下压": "\u25bc", "面拉": "\u25c4", "坐姿杠铃肩推": "\u25b2", "窄距卧推": "\u25cf",
    "高位下拉": "\u25bc", "坐姿绳索划船": "\u25c4", "杠铃弯举": "\u25c6", "锤式弯举": "\u25c6",
    "单臂哑铃划船": "\u25ba", "T杆划船": "\u25c4", "上斜哑铃弯举": "\u25c6", "反握弯举": "\u25c6",
    "杠铃深蹲": "\u25bc", "罗马尼亚硬拉": "\u25b2", "坐姿腿弯举": "\u25bc", "站姿提踵": "\u25cf",
    "传统硬拉": "\u25b2", "保加利亚分腿蹲": "\u25bc", "俯卧腿弯举": "\u25bc", "高脚杯深蹲": "\u25bc", "坐姿提踵": "\u25cf",
    "跑步": "\u266b", "游泳": "\u2668", "骑行": "\u2660", "椭圆机": "\u2666",
    "跳绳": "\u266a", "爬楼": "\u25b2", "快走": "\u2663", "HIIT": "\u2665",
    "划船机": "\u25c4", "登山": "\u25b2", "滑雪": "\u2666", "瑜伽": "\u2605",
}


class PresetGrid(FloatLayout):
    edit_mode_active = BooleanProperty(False)

    def __init__(self, presets, on_tap, on_custom, on_delete=None, **kwargs):
        super().__init__(**kwargs)
        self._on_tap_cb = on_tap
        self._on_custom_cb = on_custom
        self._on_delete_cb = on_delete
        self._preset_names = list(presets)
        self._hint = None
        self._edit_mode = False
        self._long_press_ev = None
        self._touch_start = None
        self._btn_map = {}
        self._x_btns = {}
        self._grid = GridLayout(cols=2, spacing=dp(10), size_hint=(1, None))
        self._grid.bind(minimum_height=self._grid.setter("height"))
        self._grid.bind(minimum_height=self.setter("height"))
        self.bind(height=lambda _, h: setattr(self._grid, 'width', self.width))
        self.add_widget(self._grid)
        self._rebuild()

    def _rebuild(self):
        self._grid.clear_widgets()
        self._btn_map.clear()
        for x_btn in list(self._x_btns.values()):
            if x_btn.parent: x_btn.parent.remove_widget(x_btn)
        self._x_btns.clear()
        for name in self._preset_names:
            icon = EXERCISE_ICONS.get(name, "")
            if icon:
                clr = EXERCISE_COLORS.get(name, theme.ACCENT)
                ictext = f"[color={_rgba_hex(clr)}][font=Symbols]{icon}[/font][/color]"
                display = f"{ictext} {name}"
            else:
                display = name
            btn = Button(text=display, markup=bool(icon),
                         size_hint_y=None, height=dp(38),
                         background_normal="", background_color=theme.SURFACE_HIGH,
                         color=theme.TEXT_PRIMARY, font_size=dp(theme.FONT_LABEL))
            self._add_icon_strip(btn, EXERCISE_COLORS.get(name, theme.GOLD))
            btn.bind(on_release=lambda _, n=name: self._handle_tap(n))
            sounds.bind_feedback(btn, bg_color=theme.SURFACE_HIGH)
            self._grid.add_widget(btn)
            self._btn_map[name] = btn
        cb = Button(text="+ 自定义", size_hint_y=None, height=dp(38),
                    background_normal="", background_color=theme.SURFACE,
                    color=theme.TEXT_SECONDARY, font_size=dp(theme.FONT_LABEL))
        cb.bind(on_release=lambda _: self._on_custom_cb())
        sounds.bind_feedback(cb, bg_color=theme.SURFACE)
        self._grid.add_widget(cb)

    def _add_icon_strip(self, btn, color):
        strip_w = dp(4)
        with btn.canvas.after:
            Color(*color)
            btn._icon_strip = Rectangle(pos=(dp(2), dp(4)), size=(strip_w, btn.height - dp(8)))
        def update(*_):
            btn._icon_strip.size = (strip_w, btn.height - dp(8))
        btn.bind(size=update)

    def _place_x_btns(self):
        for name, x_btn in self._x_btns.items():
            if x_btn.parent: x_btn.parent.remove_widget(x_btn)
        self._x_btns.clear()
        for name, btn in self._btn_map.items():
            bx, by = btn.to_window(*btn.pos)
            px, py = self.to_window(*self.pos)
            rel_x, rel_y = bx - px, by - py
            x_size = dp(20)
            x_btn = Button(text="X", size_hint=(None, None), size=(x_size, x_size),
                           pos=(rel_x + btn.width - x_size * 0.5, rel_y + btn.height - x_size * 0.5),
                           background_normal="", background_color=theme.DANGER,
                           color=(0.95,0.95,0.95,1), font_size=dp(12))
            x_btn.bind(on_release=lambda _, n=name: self._delete_preset(n))
            sounds.bind_feedback(x_btn, bg_color=theme.DANGER)
            self.add_widget(x_btn)
            self._x_btns[name] = x_btn

    def _remove_x_btns(self):
        for x_btn in list(self._x_btns.values()):
            if x_btn.parent: x_btn.parent.remove_widget(x_btn)
        self._x_btns.clear()

    def _handle_tap(self, name):
        if self._edit_mode:
            self._exit_edit_mode()
        else:
            self._on_tap_cb(name)

    def _enter_edit_mode(self):
        if self._edit_mode: return
        self._edit_mode = True
        self.edit_mode_active = True
        self._place_x_btns()

    def _exit_edit_mode(self):
        self._edit_mode = False
        self.edit_mode_active = False
        self._remove_x_btns()

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self._edit_mode:
            for x_btn in self._x_btns.values():
                if x_btn.collide_point(*touch.pos):
                    return super().on_touch_down(touch)
        hit = False
        for btn in self._btn_map.values():
            if btn.collide_point(*touch.pos): hit = True; break
        if not hit:
            if self._edit_mode: self._exit_edit_mode()
            return super().on_touch_down(touch)
        self._touch_start = touch.pos
        self._long_press_ev = Clock.schedule_once(lambda _: self._on_long_press(), 0.55)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._long_press_ev:
            dx = touch.x - self._touch_start[0]
            dy = touch.y - self._touch_start[1]
            if dx * dx + dy * dy > dp(8) ** 2:
                Clock.unschedule(self._long_press_ev)
                self._long_press_ev = None
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._long_press_ev:
            Clock.unschedule(self._long_press_ev)
            self._long_press_ev = None
        return super().on_touch_up(touch)

    def _on_long_press(self):
        self._long_press_ev = None
        if not self._edit_mode: self._enter_edit_mode()

    def _delete_preset(self, name):
        if name in self._preset_names: self._preset_names.remove(name)
        self._rebuild()
        if self._on_delete_cb: self._on_delete_cb(name)
        if self._preset_names: self._enter_edit_mode()
        else: self._exit_edit_mode()

    def add_preset(self, name):
        if name and name not in self._preset_names: self._preset_names.append(name)
        self._rebuild()

    def _btn_at(self, pos):
        for btn in self._btn_map.values():
            if btn.collide_point(*pos): return btn
        return None
