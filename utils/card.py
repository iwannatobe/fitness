from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle, Line
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
            self._outer_rect = Rectangle(pos=self.pos, size=self.size)
            Color(*self._bg)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
            if self._border:
                Color(*theme.BORDER)
                self._border_line = Line(
                    rectangle=(self.x, self.y, self.width, self.height),
                    width=dp(1),
                )
            Color(*theme.METAL_LIGHT)
            self._top_edge = Rectangle(pos=self.pos, size=(self.width, dp(1)))
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self._outer_rect.pos = self.pos
        self._outer_rect.size = self.size
        inset = dp(2)
        self._bg_rect.pos = (self.x + inset, self.y + inset)
        self._bg_rect.size = (max(0, self.width - inset * 2), max(0, self.height - inset * 2))
        self._top_edge.pos = (self.x + dp(1), self.top - dp(2))
        self._top_edge.size = (max(0, self.width - dp(2)), dp(1))
        if self._border:
            self._border_line.rectangle = (self.x, self.y, self.width, self.height)


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
            self._outer_rect = Rectangle(pos=self.pos, size=self.size)
            Color(*self._bg)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
            if self._border:
                Color(*theme.BORDER)
                self._border_line = Line(
                    rectangle=(self.x, self.y, self.width, self.height),
                    width=dp(1),
                )
            Color(*theme.METAL_LIGHT)
            self._top_edge = Rectangle(pos=self.pos, size=(self.width, dp(1)))
        self.bind(pos=self._redraw, size=self._redraw)
        self._child = child
        child.pos_hint = {}
        child.size_hint = (None, None)
        self.add_widget(child)
        self.bind(pos=self._layout_child, size=self._layout_child)

    def _redraw(self, *_):
        self._outer_rect.pos = self.pos
        self._outer_rect.size = self.size
        inset = dp(2)
        self._bg_rect.pos = (self.x + inset, self.y + inset)
        self._bg_rect.size = (max(0, self.width - inset * 2), max(0, self.height - inset * 2))
        self._top_edge.pos = (self.x + dp(1), self.top - dp(2))
        self._top_edge.size = (max(0, self.width - dp(2)), dp(1))
        if self._border:
            self._border_line.rectangle = (self.x, self.y, self.width, self.height)

    def _layout_child(self, *_):
        p = self._pad
        self._child.x = self.x + p
        self._child.y = self.y + p
        self._child.width = self.width - p * 2
        self._child.height = self.height - p * 2
