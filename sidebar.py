from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.core.text import Label as CoreLabel
from kivy.metrics import dp
from kivy.clock import Clock
from config import theme
from utils.platform import get_app_version
import sounds

_MENU = [
    ("CALENDAR\n日历", "home", "\u25cf"),
    ("ARCHIVE\n资料馆", "archive", "\u25b2"),
    ("CARDIO\n有氧运动", "cardio", "\u266b"),
    ("BODY DATA\n身体数据", "body", "\u2605"),
    ("STATISTICS\n统计数据", "stats", "\u25c6"),
    ("AI ASSISTANT\nAI 助手", "ai", "\u2726"),
]


class _MenuButton(Button):
    def __init__(self, label, icon, screen_name, on_select, **kwargs):
        super().__init__(text="", size_hint_y=None, height=dp(58),
                         background_normal="", background_color=(0, 0, 0, 0),
                         **kwargs)
        self._label_text = label
        self._icon_char = icon
        self._screen = screen_name
        self._on_select = on_select
        self._selected = False
        self.bind(pos=self._draw, size=self._draw)
        self.bind(on_release=lambda _: self._on_select(self._screen))
        sounds.bind_feedback(self, text_color=theme.TEXT_SECONDARY)
        self._draw()

    def set_selected(self, sel):
        self._selected = sel
        self._draw()

    def _draw(self, *args):
        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            if self._selected:
                Color(0.16, 0.165, 0.21, 1)
                RoundedRectangle(pos=(self.x + dp(8), self.y + dp(6)),
                                 size=(self.width - dp(16), self.height - dp(12)),
                                  radius=[dp(theme.CONTROL_RADIUS)])
            pad = dp(20)
            icon_clr = theme.GOLD if self._selected else theme.TEXT_MUTED
            lbl_clr = theme.TEXT_PRIMARY if self._selected else theme.TEXT_SECONDARY
            cl = CoreLabel(text=self._icon_char, font_size=dp(14),
                           color=icon_clr, font_name="Symbols")
            cl.refresh()
            if cl.texture:
                Color(*icon_clr)
                Rectangle(texture=cl.texture,
                          pos=(self.x + pad, self.y + (self.height - cl.texture.size[1]) / 2),
                          size=cl.texture.size)
            cl2 = CoreLabel(text=self._label_text, font_size=dp(theme.FONT_LABEL),
                            color=lbl_clr, font_name="Roboto")
            cl2.refresh()
            if cl2.texture:
                Color(*lbl_clr)
                tx = self.x + pad + dp(28)
                Rectangle(texture=cl2.texture,
                          pos=(tx, self.y + (self.height - cl2.texture.size[1]) / 2),
                          size=cl2.texture.size)


class Sidebar(BoxLayout):
    def __init__(self, main_layout, **kwargs):
        super().__init__(orientation="vertical", size_hint=(None, 1),
                         width=dp(240), spacing=dp(4),
                         padding=[0, dp(16), 0, dp(12)], **kwargs)
        self.main_layout = main_layout
        with self.canvas.before:
            Color(*theme.SURFACE)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            Color(*theme.BORDER)
            self._right_line = Rectangle(pos=(self.right - dp(1), self.y), size=(dp(1), self.height))
        self.bind(size=self._update_rect, pos=self._update_rect)

        header = BoxLayout(size_hint_y=None, height=dp(56), padding=[dp(20), 0, 0, 0])
        title = Label(text="FITNESS", font_size=dp(20), color=theme.GOLD, bold=True,
                      halign="left", valign="middle", size_hint_x=1)
        title.bind(size=title.setter("text_size"))
        header.add_widget(title)
        self.add_widget(header)

        sub = Label(text=f"CONTROL TERMINAL  v{get_app_version()}", color=theme.TEXT_MUTED,
                    font_size=dp(theme.FONT_CAPTION), halign="left", valign="middle",
                    size_hint_y=None, height=dp(18), padding=[dp(20), 0])
        sub.bind(size=sub.setter("text_size"))
        self.add_widget(sub)

        self.add_widget(BoxLayout(size_hint_y=None, height=dp(10)))

        self._menu_btns = {}
        for label, screen_name, icon in _MENU:
            btn = _MenuButton(label, icon, screen_name, self._nav)
            self.add_widget(btn)
            self._menu_btns[screen_name] = btn
        self.add_widget(BoxLayout())
        self._sync_selection()

    def _update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos
        self._right_line.pos = (self.right - dp(1), self.y)
        self._right_line.size = (dp(1), self.height)

    def _nav(self, screen_name):
        self.main_layout.sm.current = screen_name
        self.main_layout.close_sidebar()
        self._sync_selection()

    def _sync_selection(self):
        sm = getattr(self.main_layout, "sm", None)
        cur = getattr(sm, "current", None)
        for name, btn in self._menu_btns.items():
            btn.set_selected(name == cur)
