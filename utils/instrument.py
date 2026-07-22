"""Reusable hardware-style controls for the V1.8 instrument interface."""

from kivy.animation import Animation
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from config import theme


class InstrumentPanel(BoxLayout):
    """Black-titanium equipment module with a narrow engraved header."""

    def __init__(self, label="MODULE", accent=None, **kwargs):
        self.label = label
        self.accent = accent or theme.VFD_ORANGE
        super().__init__(orientation="vertical", **kwargs)
        with self.canvas.before:
            Color(*theme.METAL_DARK)
            self._outer = Rectangle(pos=self.pos, size=self.size)
            Color(*theme.PANEL)
            self._inner = Rectangle(pos=self.pos, size=self.size)
            Color(*theme.METAL)
            self._border = Line(rectangle=(*self.pos, *self.size), width=dp(1))
            Color(*theme.METAL_LIGHT)
            self._highlight = Rectangle(pos=self.pos, size=(self.width, dp(1)))
        self.bind(pos=self._draw_frame, size=self._draw_frame)

    def _draw_frame(self, *_):
        self._outer.pos = self.pos
        self._outer.size = self.size
        inset = dp(2)
        self._inner.pos = (self.x + inset, self.y + inset)
        self._inner.size = (max(0, self.width - inset * 2), max(0, self.height - inset * 2))
        self._border.rectangle = (self.x, self.y, self.width, self.height)
        self._highlight.pos = (self.x + dp(1), self.top - dp(2))
        self._highlight.size = (max(0, self.width - dp(2)), dp(1))


class SmokedDisplay(BoxLayout):
    """Inset smoked-glass data window with a restrained optical reflection."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*theme.METAL_DARK)
            self._recess = Rectangle(pos=self.pos, size=self.size)
            Color(*theme.DISPLAY_GLASS)
            self._glass = Rectangle(pos=self.pos, size=self.size)
            Color(*theme.VFD_CYAN_DIM)
            self._edge = Line(rectangle=(*self.pos, *self.size), width=dp(0.8))
            Color(*theme.GLASS_HIGHLIGHT)
            self._reflection = Rectangle(pos=self.pos, size=(self.width, dp(1)))
        self.bind(pos=self._draw_display, size=self._draw_display)

    def _draw_display(self, *_):
        self._recess.pos = self.pos
        self._recess.size = self.size
        inset = dp(2)
        self._glass.pos = (self.x + inset, self.y + inset)
        self._glass.size = (max(0, self.width - inset * 2), max(0, self.height - inset * 2))
        self._edge.rectangle = (self.x + inset, self.y + inset,
                                max(0, self.width - inset * 2), max(0, self.height - inset * 2))
        self._reflection.pos = (self.x + dp(4), self.top - dp(5))
        self._reflection.size = (max(0, self.width - dp(8)), dp(1))


class MechanicalButton(Button):
    """Physical command key. Kind can be inset, command, danger, or system."""

    glow_color = ListProperty(theme.VFD_ORANGE)
    kind = StringProperty("inset")

    def __init__(self, kind="inset", glow_color=None, **kwargs):
        self.kind = kind
        if glow_color is not None:
            self.glow_color = glow_color
        super().__init__(background_normal="", background_down="",
                         background_color=(0, 0, 0, 0), **kwargs)
        self._pressed = False
        with self.canvas.before:
            self._shadow_color = Color(*theme.METAL_DARK)
            self._shadow = Rectangle(pos=self.pos, size=self.size)
            self._face_color = Color(*theme.PANEL_RAISED)
            self._face = Rectangle(pos=self.pos, size=self.size)
            self._edge_color = Color(*theme.METAL)
            self._edge = Line(rectangle=(*self.pos, *self.size), width=dp(1))
            self._lamp_color = Color(*self.glow_color)
            self._lamp = Rectangle(pos=self.pos, size=(dp(3), self.height))
        self.bind(pos=self._draw_key, size=self._draw_key, state=self._state_changed,
                  glow_color=self._draw_key, kind=self._draw_key)
        self._draw_key()

    def _state_changed(self, _, state):
        self._pressed = state == "down"
        self._draw_key()

    def _draw_key(self, *_):
        offset = 0 if self._pressed else dp(2) if self.kind in ("command", "system") else dp(1)
        if self.kind == "command":
            face = (0.30, 0.095, 0.025, 1)
            edge = self.glow_color
        elif self.kind == "danger":
            face = (0.20, 0.035, 0.025, 1)
            edge = theme.LED_RED
        elif self.kind == "system":
            face = (0.025, 0.10, 0.14, 1)
            edge = theme.VFD_BLUE
        else:
            face = theme.PANEL_RAISED
            edge = theme.METAL
        self._shadow_color.rgba = theme.METAL_DARK
        self._shadow.pos = (self.x, self.y)
        self._shadow.size = self.size
        self._face_color.rgba = face
        self._face.pos = (self.x, self.y + offset)
        self._face.size = (self.width, max(0, self.height - offset))
        self._edge_color.rgba = edge
        self._edge.rectangle = (self.x, self.y + offset, self.width, max(0, self.height - offset))
        self._lamp_color.rgba = self.glow_color
        self._lamp.pos = (self.x + dp(3), self.y + dp(4) + offset)
        self._lamp.size = (dp(2), max(0, self.height - dp(8) - offset))


class StatusLamp(Widget):
    """Small rectangular hardware LED with optional restrained breathing."""

    color = ListProperty(theme.VFD_BLUE)
    _alpha = NumericProperty(1.0)

    def __init__(self, breathe=False, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(12), dp(4)))
        super().__init__(**kwargs)
        self._alpha = 1.0
        with self.canvas:
            self._color = Color(*self.color)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._draw, size=self._draw, color=self._draw, _alpha=self._draw)
        if breathe:
            self._breathe_down()

    def _draw(self, *_):
        self._color.rgba = (*self.color[:3], self._alpha)
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _breathe_down(self, *_):
        animation = Animation(_alpha=0.35, duration=1.1)
        animation.bind(on_complete=self._breathe_up)
        animation.start(self)

    def _breathe_up(self, *_):
        animation = Animation(_alpha=1.0, duration=1.1)
        animation.bind(on_complete=self._breathe_down)
        animation.start(self)

    def on_parent(self, _widget, parent):
        if parent is None:
            self.stop()

    def stop(self):
        Animation.cancel_all(self, "_alpha")


def machine_label(text, color=None, **kwargs):
    """Create a compact uppercase equipment label."""
    label = Label(text=text.upper(), color=color or theme.TEXT_MUTED,
                  font_size=dp(theme.FONT_CAPTION), halign="left", valign="middle", **kwargs)
    label.bind(size=label.setter("text_size"))
    return label
