"""Logo eject button: tap the logo to flip it open, revealing a red
EMERGENCY EJECT key that exports the fitness data as a backup file.
"""

import os
from datetime import datetime

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
        self._eject_visible = False

        # front face: the app logo
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "icons", "icon.png")
        self._logo = Image(source=logo_path, allow_stretch=True, keep_ratio=True,
                           size_hint=(1, 1), pos_hint={"center_x": 0.5, "center_y": 0.5})
        self.add_widget(self._logo)

        # back face: red circular eject key with parachute icon (hidden by default)
        # 图形画在 eject 自身的 canvas.after（避开 Button.canvas.before 的属性丢失问题）
        self._eject_size = dp(26)
        self._eject_g = {"bg": None, "edge": None, "parachute": None, "jumper": None}
        with self.canvas.after:
            Color(*theme.LED_RED)
            self._eject_g["bg"] = Ellipse()
            Color(0.95, 0.97, 0.95, 1)
            self._eject_g["edge"] = Line(width=dp(1))
            Color(1, 1, 1, 1)
            self._eject_g["parachute"] = Line(width=dp(1.2))
            self._eject_g["jumper"] = Ellipse()
        self._back = Button(text="", background_normal="", background_color=(0, 0, 0, 0),
                            size_hint=(None, None), size=(dp(26), dp(26)),
                            pos_hint={"center_x": 0.5, "center_y": 0.5})
        self._back.opacity = 0
        self.add_widget(self._back)
        self.bind(pos=self._sync_eject_g, size=self._sync_eject_g)
        self._sync_eject_g()

        # touch handling on the whole widget
        self.bind(on_touch_down=self._on_touch)

    def _sync_eject_g(self, *_):
        g = self._eject_g
        visible = getattr(self, "_eject_visible", False)
        if not visible:
            g["bg"].pos = (-1000, -1000)
            g["bg"].size = (0, 0)
            g["edge"].ellipse = (-1000, -1000, 0, 0)
            g["parachute"].points = []
            g["jumper"].pos = (-1000, -1000)
            g["jumper"].size = (0, 0)
            return
        cx = self.center_x
        cy = self.center_y
        r = self._eject_size / 2.0
        g["bg"].pos = (cx - r, cy - r)
        g["bg"].size = (r * 2, r * 2)
        g["edge"].ellipse = (cx - r, cy - r, r * 2, r * 2)
        top = cy + r * 0.55
        bottom = cy - r * 0.6
        pr = r * 0.72
        # canopy: upward arc
        pts = []
        for i in range(9):
            t = i / 8.0
            px = cx - pr + 2 * pr * t
            py = top + (pr * 0.35) * ((t * 2 - 1) ** 2)
            pts.extend([px, py])
        # shroud lines
        pts.extend([cx - pr, top, cx - pr * 0.5, bottom])
        pts.extend([cx + pr, top, cx + pr * 0.5, bottom])
        pts.extend([cx, top, cx, bottom])
        g["parachute"].points = pts
        jr = r * 0.22
        g["jumper"].pos = (cx - jr, bottom - jr)
        g["jumper"].size = (jr * 2, jr * 2)

    def _on_touch(self, widget, touch):
        if not self.collide_point(*touch.pos):
            return False
        if self._busy or self._animating:
            return True
        if self._open:
            # 已翻盖：点红色按钮触发导出确认
            self._on_eject()
        else:
            self._flip_open()
        return True

    def _flip_open(self):
        self._animating = True
        sounds.play_click()
        self._eject_visible = True
        self._sync_eject_g()
        # flip: logo fades out, red key fades in
        anim = Animation(opacity=0, duration=0.10) + \
               Animation(opacity=1, duration=0.16)
        anim.bind(on_start=self._show_back)
        anim.bind(on_complete=lambda *_: self._finish_open())
        anim.start(self._logo)
        self._back_anim = Animation(opacity=0, duration=0.0) + \
                          Animation(opacity=1, duration=0.18)
        self._back_anim.start(self._back)

    def _flip_close(self):
        self._animating = True
        sounds.play_click()
        anim = Animation(opacity=0, duration=0.10) + \
               Animation(opacity=1, duration=0.16)
        anim.bind(on_start=self._show_front)
        anim.bind(on_complete=lambda *_: self._finish_close())
        anim.start(self._back)
        self._logo_anim = Animation(opacity=0, duration=0.0) + \
                          Animation(opacity=1, duration=0.18)
        self._logo_anim.start(self._logo)

    def _show_back(self, *_):
        self._back.opacity = 0

    def _show_front(self, *_):
        self._logo.opacity = 0
        self._eject_visible = False
        self._sync_eject_g()

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
        cancel.bind(on_release=lambda _: (popup.dismiss(), self._flip_close()))
        btn_row.add_widget(cancel)
        confirm = Button(text="导出", background_normal="", background_color=theme.LED_RED,
                         color=(1, 1, 1, 1), font_size=dp(14), bold=True)
        confirm.bind(on_release=lambda _: (popup.dismiss(), self._flip_close(), self._do_export()))
        btn_row.add_widget(confirm)
        root.add_widget(btn_row)
        popup.add_widget(root)
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
