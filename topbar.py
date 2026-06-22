from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Line
from kivy.metrics import dp
from config import theme
import sounds


class HamburgerButton(Button):
    def __init__(self, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(44), dp(44)),
                         background_normal="", background_color=(0, 0, 0, 0), **kwargs)
        self._line_color = theme.TEXT_SECONDARY
        self.bind(pos=self._draw, size=self._draw)
        self.bind(on_press=self._on_down, on_release=self._on_up)

    def _on_down(self, *_):
        sounds.play_click()
        self._line_color = sounds.lighten(theme.TEXT_SECONDARY)
        self._draw()

    def _on_up(self, *_):
        self._line_color = theme.TEXT_SECONDARY
        self._draw()

    def _draw(self, *args):
        self.canvas.after.clear()
        x = self.x + self.width * 0.18
        w = self.width * 0.64
        h = dp(2)
        gap = dp(5)
        cy = self.y + self.height / 2
        with self.canvas.after:
            Color(*self._line_color)
            for i in range(3):
                Rectangle(pos=(x, cy + (i - 1) * (h + gap)), size=(w, h))


class TopBar(BoxLayout):
    def __init__(self, title_text, on_menu, **kwargs):
        super().__init__(size_hint_y=None, height=dp(52), **kwargs)
        with self.canvas.before:
            Color(*theme.SURFACE)
            self._rect = Rectangle(size=self.size, pos=self.pos)
            Color(*theme.HAIRLINE)
            self._line = Rectangle(pos=(self.x, self.y), size=(self.width, dp(1)))
        self.bind(size=self._update_rect, pos=self._update_rect)
        burger = HamburgerButton()
        burger.bind(on_release=lambda _: on_menu())
        self.add_widget(burger)
        self.add_widget(Label(text=title_text, font_size=dp(theme.FONT_H2),
                              color=theme.TEXT_PRIMARY, bold=True,
                              halign="left", valign="middle"))
        spacer = BoxLayout(size_hint=(None, None), size=(dp(44), dp(44)))
        self.add_widget(spacer)

    def _update_rect(self, *args):
        self._rect.size = self.size
        self._rect.pos = self.pos
        self._line.pos = (self.x, self.y)
        self._line.size = (self.width, dp(1))
