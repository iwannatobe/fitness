from kivy.uix.button import Button
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.properties import BooleanProperty, NumericProperty
from kivy.metrics import dp
import math
from datetime import date
import theme
import database as db
import sounds

_BG_NORMAL = (0.10, 0.11, 0.14, 1)
_BG_NUKED = (0.18, 0.08, 0.06, 1)
_ICON_NORMAL = theme.GOLD
_ICON_NUKED = theme.GOLD_DARK

class NukeButton(Button):
    nuked_today = BooleanProperty(False)
    _glow = NumericProperty(0.15)

    def __init__(self, **kwargs):
        super().__init__(background_normal="", background_color=(0,0,0,0), **kwargs)
        self._bg = _BG_NORMAL
        self._icon = _ICON_NORMAL
        self.bind(pos=self._draw, size=self._draw, _glow=self._draw)
        self.bind(nuked_today=self._on_nuked_changed)
        self.nuked_today = db.is_date_nuked(date.today().isoformat())
        Clock.schedule_once(lambda dt: self._start_glow(), 0.5)

    def _start_glow(self):
        anim = (Animation(_glow=0.32, duration=2.0, transition="linear") +
                Animation(_glow=0.05, duration=2.0, transition="linear"))
        anim.repeat = True
        anim.start(self)

    def _on_nuked_changed(self, *_):
        if self.nuked_today:
            self._bg = _BG_NUKED
            self._icon = _ICON_NUKED
        else:
            self._bg = _BG_NORMAL
            self._icon = _ICON_NORMAL
        self._draw()

    def on_press(self):
        sounds.play_explosion()
        if self.nuked_today:
            self._bg = sounds.lighten(_BG_NUKED)
            self._icon = sounds.lighten(_ICON_NUKED)
        else:
            self._bg = sounds.lighten(_BG_NORMAL)
            self._icon = sounds.lighten(_ICON_NORMAL)
        self._draw()

    def on_release(self):
        self._on_nuked_changed()

    def _draw(self, *args):
        self.canvas.before.clear()
        self.canvas.after.clear()
        x, y = self.x, self.y
        w, h = self.width, self.height
        cx, cy = self.center_x, self.center_y
        bg, icon = self._bg, self._icon
        s = min(w, h) * 0.40
        radius = [min(w, h) * 0.14]

        with self.canvas.before:
            Color(*bg)
            RoundedRectangle(pos=(x, y), size=(w, h), radius=radius)
            Color(icon[0], icon[1], icon[2], self._glow)
            glow_r = s * 1.55
            Ellipse(pos=(cx - glow_r, cy - glow_r), size=(glow_r * 2, glow_r * 2))

        with self.canvas.after:
            Color(*icon)
            Line(circle=(cx, cy, s), width=2.5)

            for i in range(6):
                start = i * 60 - 90
                a = math.radians(start)
                tip_r = s * 0.15
                tip_dist = s - tip_r * 0.6
                tx = cx + math.cos(a) * tip_dist
                ty = cy + math.sin(a) * tip_dist
                Ellipse(pos=(tx - tip_r, ty - tip_r), size=(tip_r * 2, tip_r * 2))

            Color(*bg)
            hub = s * 0.32
            Ellipse(pos=(cx - hub, cy - hub), size=(hub * 2, hub * 2))

            Color(*icon)
            Line(circle=(cx, cy, hub), width=1.5)
            dot = s * 0.07
            Ellipse(pos=(cx - dot, cy - dot), size=(dot * 2, dot * 2))
