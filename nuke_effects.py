import random
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, Ellipse, Rectangle

def shake_widget(widget, intensity=6, duration=0.3):
    orig_x = widget.x
    steps = int(duration / 0.03)
    dt = duration / steps
    def step(i):
        if i > steps: widget.x = orig_x; return
        offset = random.randint(-intensity, intensity) * dp(1)
        widget.x = orig_x + offset
        Clock.schedule_once(lambda _: step(i + 1), dt)
    step(0)

def flash_screen(layout):
    flash = BoxLayout(size_hint=(1, 1), opacity=1)
    with flash.canvas.before:
        Color(1, 1, 1, 1)
        Rectangle(size=flash.size, pos=flash.pos)
    layout.add_widget(flash)
    anim = Animation(opacity=0, duration=0.25)
    anim.bind(on_complete=lambda *_: layout.remove_widget(flash))
    anim.start(flash)

def explode_particles(layout, cx, cy, count=30):
    for _ in range(count):
        angle = random.uniform(0, 6.28); speed = random.uniform(80, 250)
        size = random.uniform(3, 8)
        r, g, b = random.uniform(0.8, 1.0), random.uniform(0.1, 0.5), random.uniform(0.1, 0.3)
        p = BoxLayout(size_hint=(None, None), size=(dp(size), dp(size)), pos=(cx - dp(size / 2), cy - dp(size / 2)))
        with p.canvas.before:
            Color(r, g, b, 1)
            Ellipse(pos=(0, 0), size=(dp(size), dp(size)))
        layout.add_widget(p)
        anim = Animation(x=cx + dp(angle * 0.8 * speed) - dp(size / 2), y=cy + dp(angle * 0.8 * speed) - dp(size / 2), duration=0.6)
        anim.bind(on_complete=lambda *_, particle=p: layout.remove_widget(particle))
        anim.start(p)
