from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from config import theme


class Card(BoxLayout):
    def __init__(self, radius=None, padding=None, bg=None, border=True, **kwargs):
        if padding is None:
            padding = (dp(theme.CARD_PADDING), dp(theme.CARD_PADDING))
        super().__init__(padding=padding, **kwargs)
        self._radius = dp(radius if radius is not None else theme.CARD_RADIUS)
        self._bg = bg or theme.SURFACE
        self._border = border
        with self.canvas.before:
            Color(*self._bg)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
            if self._border:
                Color(*theme.BORDER)
                self._border_line = Line(
                    rounded_rectangle=(self.x, self.y, self.width, self.height, self._radius),
                    width=dp(1),
                )
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        if self._border:
            self._border_line.rounded_rectangle = (
                self.x, self.y, self.width, self.height, self._radius
            )


class CardHolder(FloatLayout):
    """透明壳，用于把任意 widget 包成卡片（不侵入 widget 内部布局）。"""

    def __init__(self, child, radius=None, padding=0, bg=None, border=True, **kwargs):
        super().__init__(**kwargs)
        self._radius = dp(radius if radius is not None else theme.CARD_RADIUS)
        self._bg = bg or theme.SURFACE
        self._border = border
        self._pad = dp(padding)
        with self.canvas.before:
            Color(*self._bg)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
            if self._border:
                Color(*theme.BORDER)
                self._border_line = Line(
                    rounded_rectangle=(self.x, self.y, self.width, self.height, self._radius),
                    width=dp(1),
                )
        self.bind(pos=self._redraw, size=self._redraw)
        self._child = child
        child.pos_hint = {}
        child.size_hint = (None, None)
        self.add_widget(child)
        self.bind(pos=self._layout_child, size=self._layout_child)

    def _redraw(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        if self._border:
            self._border_line.rounded_rectangle = (
                self.x, self.y, self.width, self.height, self._radius
            )

    def _layout_child(self, *_):
        p = self._pad
        self._child.x = self.x + p
        self._child.y = self.y + p
        self._child.width = self.width - p * 2
        self._child.height = self.height - p * 2
