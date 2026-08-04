"""Logo eject button: tap the logo to flip it open, revealing a red
EMERGENCY EJECT key that exports the fitness data as a backup file.
"""

import os
from datetime import datetime
from math import cos as _cos, sin as _sin

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from config import theme
import database as db
import sounds


class LogoEjectButton(FloatLayout):
    """Top-bar logo that flips open to reveal a red emergency eject key.

    Tap the logo -> flip animation opens to show a red EJECT key.
    Tap the key -> confirmation popup -> writes a JSON backup file.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self._open = False
        self._animating = False
        self._busy = False

        # front face: the app logo
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "icons", "icon.png")
        self._logo = Image(source=logo_path, allow_stretch=True, keep_ratio=True,
                           size_hint=(1, 1), pos_hint={"center_x": 0.5, "center_y": 0.5})
        self.add_widget(self._logo)

        # back face: instrument-style red eject key.
        # 图形指令引用存到 self（eject），canvas 上下文里赋值给子 widget 会丢失
        self._eject_size = dp(28)
        self._back = Widget(size_hint=(None, None), size=(dp(28), dp(28)),
                            pos_hint={"center_x": 0.5, "center_y": 0.5})
        with self._back.canvas:
            Color(*theme.METAL_DARK)
            self._back_outer = Ellipse()
            Color(*theme.METAL_LIGHT)
            self._back_outer_edge = Line(width=dp(1.2))
            Color(0.72, 0.06, 0.04, 1)
            self._back_body = Ellipse()
            Color(0.30, 0.02, 0.02, 1)
            self._back_body_edge = Line(width=dp(1))
            Color(1.0, 0.55, 0.08, 1)
            self._back_ring = Line(width=dp(1.6))
            Color(1.0, 0.95, 0.9, 0.30)
            self._back_gloss = Ellipse()
        self._back.bind(pos=self._sync_back, size=self._sync_back)
        self._sync_back(self._back)
        self._back.opacity = 0
        self.add_widget(self._back)

        # touch handling on the whole widget
        self.bind(on_touch_down=self._on_touch)

    def _circle_pts(self, cx, cy, r, n=28):
        pts = []
        for i in range(n):
            a = 6.2831853 * i / n
            pts.extend([cx + r * _cos(a), cy + r * _sin(a)])
        return pts

    def _sync_back(self, w, *_):
        cx = w.center_x
        cy = w.center_y
        r = w.width / 2.0
        # 金属外环
        self._back_outer.pos = w.pos
        self._back_outer.size = w.size
        self._back_outer_edge.points = self._circle_pts(cx, cy, r * 0.96)
        # 深红主体
        body_r = r * 0.80
        self._back_body.pos = (cx - body_r, cy - body_r)
        self._back_body.size = (body_r * 2, body_r * 2)
        self._back_body_edge.points = self._circle_pts(cx, cy, body_r * 0.99)
        # 橙色同心环
        self._back_ring.points = self._circle_pts(cx, cy, body_r * 0.52)
        # 玻璃高光
        gloss_r = body_r * 0.32
        gx = cx - body_r * 0.35 - gloss_r
        gy = cy + body_r * 0.42 - gloss_r
        self._back_gloss.pos = (gx, gy)
        self._back_gloss.size = (gloss_r * 2, gloss_r * 2)

    def _on_touch(self, widget, touch):
        if not self.collide_point(*touch.pos):
            return False
        if self._busy or self._animating:
            return True
        # 点一下：翻盖露出红色按钮 + 自动弹导出确认框
        self._flip_open()
        return True

    def _flip_open(self):
        self._animating = True
        sounds.play_click()
        # logo 淡出
        anim_logo = Animation(opacity=0, duration=0.12)
        anim_logo.bind(on_complete=lambda *_: self._finish_open())
        anim_logo.start(self._logo)
        # 确保红色按钮图形位置正确后淡入
        self._sync_back(self._back)
        self._back.opacity = 0
        Animation(opacity=1, duration=0.18).start(self._back)
        # 翻盖完成后自动弹确认框
        Clock.schedule_once(lambda dt: self._on_eject(), 0.2)

    def _flip_close(self, *_):
        if self._logo.opacity == 1 and self._back.opacity == 0:
            return
        self._animating = True
        sounds.play_click()
        # logo 淡入
        self._logo.opacity = 0
        Animation(opacity=1, duration=0.18).start(self._logo)
        # red key 淡出
        anim_back = Animation(opacity=0, duration=0.12)
        anim_back.bind(on_complete=lambda *_: self._finish_close())
        anim_back.start(self._back)

    def _finish_open(self):
        self._animating = False
        self._open = True

    def _finish_close(self):
        self._animating = False
        self._open = False

    def _on_eject(self):
        sounds.play_click()
        self._show_eject_popup()

    def _show_eject_popup(self):
        from kivy.uix.modalview import ModalView
        popup = ModalView(size_hint=(0.86, 0.44), auto_dismiss=True)
        popup.background = ""
        popup.background_color = (0, 0, 0, 0)

        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        with root.canvas.before:
            Color(*theme.CHASSIS)
            bg = Rectangle(pos=root.pos, size=root.size)
            Color(*theme.METAL_LIGHT)
            border = Line(rectangle=(*root.pos, *root.size), width=dp(1))
        root.bind(
            pos=lambda _, p: (setattr(bg, "pos", p),
                              setattr(border, "rectangle", (*p, root.width, root.height))),
            size=lambda _, s: (setattr(bg, "size", s),
                               setattr(border, "rectangle", (*root.pos, s[0], s[1]))),
        )
        root.add_widget(Label(
            text="[color=ff5d5d][b]EMERGENCY EJECT[/b][/color]\n[color=888888]数据导出[/color]",
            markup=True, color=theme.TEXT_PRIMARY, font_size=dp(15),
            halign="center", valign="middle", size_hint_y=None, height=dp(48)))
        root.add_widget(Label(
            text="将当前全部训练/饮食/身体数据导出为备份文件？\n可用于在新设备或更新后恢复，防止数据丢失。",
            color=theme.TEXT_SECONDARY, font_size=dp(12),
            halign="center", valign="middle", size_hint_y=None, height=dp(52)))

        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        cancel = Button(text="取消", background_normal="", background_color=theme.METAL_DARK,
                        color=theme.TEXT_PRIMARY, font_size=dp(14))
        cancel.bind(on_release=lambda _: popup.dismiss())
        btn_row.add_widget(cancel)
        confirm = Button(text="导出", background_normal="", background_color=theme.LED_RED,
                         color=(1, 1, 1, 1), font_size=dp(14), bold=True)
        confirm.bind(on_release=lambda _: (popup.dismiss(), self._do_export()))
        btn_row.add_widget(confirm)
        root.add_widget(btn_row)
        popup.add_widget(root)
        # 无论以何种方式关闭弹框（取消/导出/点外部），都翻回 logo 并隐藏红色按钮
        popup.bind(on_dismiss=self._flip_close)
        popup.open()

    def _do_export(self):
        self._busy = True
        try:
            path = db.save_backup_file()
            size_kb = os.path.getsize(path) // 1024
            self._show_result(True, f"已导出 {size_kb} KB\n{os.path.basename(path)}")
        except Exception as e:
            self._show_result(False, f"导出失败：{e}")
        finally:
            self._busy = False

    def _show_result(self, ok, msg):
        from kivy.uix.modalview import ModalView
        popup = ModalView(size_hint=(0.8, 0.34), auto_dismiss=True)
        popup.background = ""
        popup.background_color = (0, 0, 0, 0)
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        with root.canvas.before:
            Color(*theme.CHASSIS)
            bg = Rectangle(pos=root.pos, size=root.size)
            Color(*theme.METAL_LIGHT)
            border = Line(rectangle=(*root.pos, *root.size), width=dp(1))
        root.bind(
            pos=lambda _, p: (setattr(bg, "pos", p),
                              setattr(border, "rectangle", (*p, root.width, root.height))),
            size=lambda _, s: (setattr(bg, "size", s),
                               setattr(border, "rectangle", (*root.pos, s[0], s[1]))),
        )
        color = theme.LED_GREEN if ok else theme.DANGER
        root.add_widget(Label(text=f"[color={_rgb_hex(color)}][b]{'导出成功' if ok else '导出失败'}[/b][/color]",
                              markup=True, color=theme.TEXT_PRIMARY, font_size=dp(14),
                              halign="center", valign="middle", size_hint_y=None, height=dp(36)))
        root.add_widget(Label(text=msg, color=theme.TEXT_SECONDARY, font_size=dp(12),
                              halign="center", valign="middle"))
        ok_btn = Button(text="完成", background_normal="", background_color=theme.METAL_DARK,
                        color=theme.TEXT_PRIMARY, font_size=dp(14),
                        size_hint_y=None, height=dp(40))
        ok_btn.bind(on_release=lambda _: popup.dismiss())
        root.add_widget(ok_btn)
        popup.add_widget(root)
        popup.open()


def _rgb_hex(color):
    r, g, b = int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
    return f"{r:02x}{g:02x}{b:02x}"
