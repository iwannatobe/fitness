# 核弹按钮重构实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 main_layout.py 中 ~360 行核弹按钮耦合代码拆分为三个独立模块

**Architecture:** nuke_button.py (组件)、nuke_effects.py (视觉特效)、battle_report.py (战报弹窗)，main_layout.py 仅保留 ~15 行编排逻辑

**Tech Stack:** Python 3.12, Kivy 2.3.1, SQLite

---

### Task 1: 创建 nuke_button.py

**Files:**
- Create: `nuke_button.py`
- Modify: `main_layout.py:25-131` (删除 NukeButton 类)

**Step 1: 创建 `nuke_button.py`**

```python
from kivy.uix.button import Button
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.properties import BooleanProperty, NumericProperty
from math import cos, sin, radians
from datetime import date

import theme
import database as db
import sounds


class NukeButton(Button):
    """Radiation-trefoil button with nuke-today state."""

    _bg_normal = (0.10, 0.08, 0.00, 1)
    _bg_nuked = (0.06, 0.05, 0.02, 1)
    _icon_normal = theme.GOLD
    _icon_nuked = theme.GOLD_DARK

    nuked_today = BooleanProperty(False)
    _glow = NumericProperty(0.15)

    def __init__(self, **kwargs):
        super().__init__(
            background_normal="",
            background_color=(0, 0, 0, 0),
            **kwargs,
        )
        self._bg = self._bg_normal
        self._icon = self._icon_normal
        self.bind(pos=self._draw, size=self._draw, _glow=self._draw)
        self.bind(nuked_today=self._on_nuked_changed)
        self.nuked_today = db.is_date_nuked(date.today().isoformat())
        Clock.schedule_once(lambda dt: self._start_glow(), 0.5)

    def _start_glow(self):
        anim = (
            Animation(_glow=0.30, duration=2.0, transition="linear")
            + Animation(_glow=0.03, duration=2.0, transition="linear")
        )
        anim.repeat = True
        anim.start(self)

    def _on_nuked_changed(self, *_):
        if self.nuked_today:
            self._bg = self._bg_nuked
            self._icon = self._icon_nuked
        else:
            self._bg = self._bg_normal
            self._icon = self._icon_normal
        self._draw()

    def on_press(self):
        sounds.play_explosion()
        if not self.nuked_today:
            self._bg = sounds.lighten(self._bg_normal)
            self._icon = sounds.lighten(self._icon_normal)
        else:
            self._bg = sounds.lighten(self._bg_nuked)
            self._icon = sounds.lighten(self._icon_nuked)
        self._draw()

    def on_release(self):
        self._on_nuked_changed()

    def _draw(self, *args):
        self.canvas.before.clear()
        self.canvas.after.clear()

        x, y = self.x, self.y
        w, h = self.width, self.height
        cx, cy = self.center_x, self.center_y

        bg = self._bg
        icon = self._icon

        s = min(w, h) * 0.42

        with self.canvas.before:
            Color(*bg)
            Rectangle(pos=(x, y), size=(w, h))
            Color(icon[0], icon[1], icon[2], self._glow)
            glow_r = s * 1.6
            Ellipse(pos=(cx - glow_r, cy - glow_r), size=(glow_r * 2, glow_r * 2))

        with self.canvas.after:
            Color(*icon)
            Line(circle=(cx, cy, s), width=2.5)

            for i in range(3):
                start = i * 120 - 90
                Ellipse(
                    pos=(cx - s, cy - s), size=(s * 2, s * 2),
                    angle_start=start, angle_end=start + 60,
                )

            for i in range(3):
                a = radians(i * 120 - 90)
                tip_r = s * 0.15
                tip_dist = s - tip_r * 0.6
                tx = cx + cos(a) * tip_dist
                ty = cy + sin(a) * tip_dist
                Ellipse(pos=(tx - tip_r, ty - tip_r),
                        size=(tip_r * 2, tip_r * 2))

            Color(*bg)
            hub = s * 0.32
            Ellipse(pos=(cx - hub, cy - hub), size=(hub * 2, hub * 2))

            Color(*icon)
            Line(circle=(cx, cy, hub), width=1.5)

            dot = s * 0.07
            Ellipse(pos=(cx - dot, cy - dot), size=(dot * 2, dot * 2))
```

**Step 2: 步骤 2: 在 main_layout.py 中，把 `from nuke_button import NukeButton` 加到 import 区域，并删除第 25-131 行的 NukeButton 类定义。**

**Step 3: 验证应用可正常启动**

Run: `.venv312/Scripts/python main.py`
Expected: App 窗口正常启动，核弹按钮可见，点击有音效

**Step 4: Commit**

```bash
git add nuke_button.py main_layout.py
git commit -m "refactor: extract NukeButton to nuke_button.py"
```

---

### Task 2: 创建 nuke_effects.py

**Files:**
- Create: `nuke_effects.py`
- Modify: `main_layout.py:312-405` (删除 _shake_screen, _flash_screen, _explode_particles)

**Step 1: 创建 `nuke_effects.py`**

```python
import random
from math import cos, sin

from kivy.uix.floatlayout import FloatLayout
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, Ellipse, Rectangle


def shake_widget(widget):
    orig_x = widget.x
    shake_seq = Animation(x=orig_x + dp(10), duration=0.04)
    for _ in range(6):
        shake_seq += Animation(x=orig_x - dp(10), duration=0.04)
        shake_seq += Animation(x=orig_x + dp(10), duration=0.04)
    shake_seq += Animation(x=orig_x - dp(7), duration=0.03)
    shake_seq += Animation(x=orig_x + dp(7), duration=0.03)
    shake_seq += Animation(x=orig_x - dp(3), duration=0.02)
    shake_seq += Animation(x=orig_x, duration=0.02)
    shake_seq.start(widget)


def flash_screen(parent):
    flash = FloatLayout(
        size_hint=(1, 1), pos_hint={"x": 0, "y": 0},
        opacity=0,
    )
    flash_rect = Rectangle(pos=(0, 0), size=(1, 1))
    with flash.canvas.before:
        Color(1, 1, 1, 1)
        flash.canvas.before.add(flash_rect)
    flash.bind(
        pos=lambda _, p: setattr(flash_rect, 'pos', p),
        size=lambda _, s: setattr(flash_rect, 'size', s),
    )

    def fade_in(dt):
        flash.opacity = 0.7

    def fade_out(dt):
        anim = Animation(opacity=0, duration=0.25)
        anim.bind(on_complete=lambda *_: parent.remove_widget(flash))
        anim.start(flash)

    parent.add_widget(flash)
    Clock.schedule_once(fade_in, 0.02)
    Clock.schedule_once(fade_out, 0.3)


def explode_particles(parent, cx, cy):
    particles = []
    for _ in range(40):
        a = random.uniform(0, 2 * 3.14159)
        spd = random.uniform(80, 300)
        particles.append({
            'x': cx, 'y': cy,
            'vx': cos(a) * spd,
            'vy': sin(a) * spd,
            'size': random.uniform(3, 10),
            'r': random.uniform(0.1, 0.35),
            'g': random.uniform(0.55, 1.0),
            'b': random.uniform(0.0, 0.25),
            'life': random.uniform(0.5, 1.2),
        })

    class ParticleCanvas(FloatLayout):
        pass

    pwidget = ParticleCanvas()
    parent.add_widget(pwidget)

    def update(dt):
        pwidget.canvas.clear()
        alive = False
        for p in particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] -= 300 * dt
            p['size'] *= 0.985
            p['life'] -= dt
            if p['life'] > 0 and p['size'] > 0.5:
                alive = True
                alpha = max(0, p['life'] / 1.2)
                sz = p['size']
                with pwidget.canvas:
                    Color(p['r'], p['g'], p['b'], alpha)
                    Ellipse(
                        pos=(p['x'] - sz / 2, p['y'] - sz / 2),
                        size=(sz, sz),
                    )
        if not alive:
            parent.remove_widget(pwidget)
            return False

    Clock.schedule_interval(update, 1 / 60)
```

**Step 2: 在 main_layout.py 中：加 import，删除 _shake_screen/_flash_screen/_explode_particles 三个方法。更新 _do_nuke 中调用为独立函数。**

**Step 3: 验证特效正常**

Run: `.venv312/Scripts/python main.py`
Expected: 点击核弹按钮后，震动+白闪+粒子爆炸均正常

**Step 4: Commit**

```bash
git add nuke_effects.py main_layout.py
git commit -m "refactor: extract nuke effects to nuke_effects.py"
```

---

### Task 3: 创建 battle_report.py

**Files:**
- Create: `battle_report.py`
- Modify: `main_layout.py:407-496` (删除 _show_battle_report, _find_nuke_btn)

**Step 1: 创建 `battle_report.py`**

```python
from datetime import date

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, RoundedRectangle

import theme
import database as db


def show_battle_report(parent, date_str=None):
    if date_str is None:
        date_str = date.today().isoformat()
    s_rows, c_rows = db.get_date_detail(date_str)

    lines = ["[font=Symbols]☢[/font] [b]今日战报[/b]\n"]

    if s_rows:
        for r in s_rows:
            lines.append(f"  {r['exercise_name']}  {r['sets']}x{r['reps']}  {r['weight']}kg")
    else:
        lines.append("  力量训练：--")

    if c_rows:
        if s_rows:
            lines.append("")
        for r in c_rows:
            lines.append(f"  {r['exercise_type']}  {r['distance']}km  {r['duration']}min")
    else:
        lines.append("  有氧运动：--")

    if not s_rows and not c_rows:
        lines.append("\n今天还没练！按完核弹就快去！")

    overlay = FloatLayout(size_hint=(1, 1))

    with overlay.canvas.before:
        Color(0, 0, 0, 0.55)
        Rectangle(pos=(0, 0), size=(10000, 10000))

    label = Label(
        text="\n".join(lines),
        color=theme.TEXT_PRIMARY,
        font_size=dp(14),
        markup=True,
        halign="center", valign="top",
        padding=(dp(16), dp(12)),
        size_hint_y=None,
    )
    label.bind(texture_size=lambda _, s: setattr(label, 'height', s[1]))

    card = BoxLayout(orientation="vertical", padding=dp(12))
    card.size_hint = (0.78, None)
    card.pos_hint = {"center_x": 0.5, "center_y": 0.5}
    card.add_widget(label)
    card.bind(minimum_height=card.setter("height"))

    def set_text_size(_, w):
        label.text_size = (w - dp(24), None)
    card.bind(width=set_text_size)

    with card.canvas.before:
        Color(*theme.SURFACE)
        card._card_bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
    card.bind(pos=lambda _, p: setattr(card._card_bg, 'pos', p),
              size=lambda _, s: setattr(card._card_bg, 'size', s))

    overlay.add_widget(card)
    overlay.opacity = 0
    parent.add_widget(overlay)
    Animation(opacity=1, duration=0.2).start(overlay)

    def dismiss(*_):
        if overlay.parent:
            a = Animation(opacity=0, scale=0.5, duration=0.15)
            a.bind(on_complete=lambda *_: parent.remove_widget(overlay))
            a.start(overlay)
    overlay.bind(on_touch_down=lambda _, t: (dismiss() if overlay.collide_point(*t.pos) else None))
```

**Step 2: 在 main_layout.py 中：加 import，删除 _show_battle_report 和 _find_nuke_btn。更新 _do_nuke 用 `show_battle_report(self)`。**

**Step 3: 验证战报弹窗**

Run: `.venv312/Scripts/python main.py`
Expected: 核弹爆炸 0.9 秒后战报卡片弹出，点击可 dismiss

**Step 4: Commit**

```bash
git add battle_report.py main_layout.py
git commit -m "refactor: extract battle report to battle_report.py"
```

---

### Task 4: 清理 main_layout.py

**Files:**
- Modify: `main_layout.py`

**Step 1: 精简 import 区域，移除不再需要的导入（random, cos, sin, radians, Label, Popup, Animation, Color, Ellipse, Line, Rectangle, RoundedRectangle 等）**

**Step 2: 最终 _do_nuke 编排函数**

```python
def _do_nuke(self, btn):
    is_first = not btn.nuked_today
    if is_first:
        db.add_nuke_marker(date.today().isoformat())
        btn.nuked_today = True
        self.refresh_heatmap()

    shake_widget(self.sm)
    flash_screen(self)
    explode_particles(self, btn.center_x, btn.center_y)
    Clock.schedule_once(lambda dt: show_battle_report(self), 0.9)
```

**Step 3: 最终验证完整流程**

Run: `.venv312/Scripts/python main.py`
Expected: 全部功能正常 — 核弹按钮渲染、打卡、震动、白闪、粒子、战报、日历刷新

**Step 4: Commit**

```bash
git add main_layout.py
git commit -m "cleanup: remove dead imports and methods from main_layout.py"
```
