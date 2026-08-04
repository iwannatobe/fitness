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

        # back face: red circular eject key with orange inner ring.
        # 用 widget opacity 控制显隐（Kivy 可靠地按 opacity 整体隐藏）
        self._eject_size = dp(26)
        self._back = BoxLayout(size_hint=(None, None), size=(dp(26), dp(26)),
                               pos_hint={"center_x": 0.5, "center_y": 0.5})
        with self._back.canvas:
            Color(*theme.LED_RED)
            self._back_bg = Ellipse(pos=self._back.pos, size=self._back.size)
            Color(1.0, 0.45, 0.0, 1)  # 橙色内圈
            self._back_ring = Line(width=dp(2))
        self._back.bind(pos=self._sync_back, size=self._sync_back)
        self._back.opacity = 0
        self.add_widget(self._back)

        # touch handling on the whole widget
        self.bind(on_touch_down=self._on_touch)

    def _sync_back(self, w, *_):
        self._back_bg.pos = w.pos
        self._back_bg.size = w.size
        cx = w.center_x
        cy = w.center_y
        ring_r = w.width * 0.38
        pts = []
        for i in range(24):
            a = 6.2831853 * i / 24.0
            pts.extend([cx + ring_r * _cos(a), cy + ring_r * _sin(a)])
        self._back_ring.points = pts

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
        # red key 淡入
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
