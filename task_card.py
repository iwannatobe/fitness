from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from config import theme
import database as db


class TaskCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical",
                         size_hint_y=None, height=dp(88),
                         padding=[dp(theme.CARD_PADDING), dp(12)],
                         spacing=dp(6), **kwargs)
        self._radius = dp(theme.CARD_RADIUS)
        with self.canvas.before:
            Color(*theme.SURFACE)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
            Color(*theme.BORDER)
            self._border = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, self._radius),
                width=dp(1),
            )
        self.bind(pos=self._redraw, size=self._redraw)

        header = BoxLayout(size_hint_y=None, height=dp(18), spacing=dp(6))
        self._title = Label(text="[b]今日任务[/b]", markup=True,
                            color=theme.TEXT_PRIMARY, font_size=dp(theme.FONT_H3),
                            halign="left", valign="middle", size_hint_x=1)
        self._title.bind(size=self._title.setter("text_size"))
        header.add_widget(self._title)
        self._count = Label(text="0/0", color=theme.GOLD, font_size=dp(theme.FONT_H3),
                            bold=True, halign="right", valign="middle",
                            size_hint_x=None, width=dp(56))
        self._count.bind(size=self._count.setter("text_size"))
        header.add_widget(self._count)
        self.add_widget(header)

        self._track = BoxLayout(size_hint_y=None, height=dp(6), padding=0)
        self._progress_ratio = 0.0
        with self._track.canvas.before:
            Color(*theme.SURFACE_HIGH)
            self._track_bg = RoundedRectangle(pos=self._track.pos, size=self._track.size,
                                               radius=[dp(3)])
            Color(*theme.GOLD)
            self._track_fill = RoundedRectangle(pos=self._track.pos, size=(0, dp(6)),
                                                 radius=[dp(3)])
        self._track.bind(pos=self._redraw_track, size=self._redraw_track)
        self.add_widget(self._track)

        self._sub = Label(text="点击核爆按钮生成计划", color=theme.TEXT_MUTED,
                          font_size=dp(theme.FONT_CAPTION), halign="left", valign="middle",
                          markup=True, size_hint_y=None, height=dp(14))
        self._sub.bind(size=self._sub.setter("text_size"))
        self.add_widget(self._sub)
        self.refresh()

    def _redraw(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._border.rounded_rectangle = (self.x, self.y, self.width, self.height, self._radius)

    def _redraw_track(self, *_):
        self._track_bg.pos = self._track.pos
        self._track_bg.size = self._track.size
        fill_w = max(0, self._track.width * self._progress_ratio)
        if fill_w > 0 and fill_w < dp(6):
            fill_w = dp(6)
        self._track_fill.pos = (self._track.x, self._track.y)
        self._track_fill.size = (fill_w, dp(6))

    def refresh(self):
        plan = db.get_today_plan()
        if not plan:
            self._progress_ratio = 0.0
            self._title.text = "[b]今日任务[/b]"
            self._count.text = "—"
            self._count.color = theme.TEXT_MUTED
            self._sub.text = "点击核爆按钮生成计划"
            self._redraw_track()
            return
        total = len(plan)
        done = sum(1 for p in plan if p["completed"])
        self._progress_ratio = done / total if total else 0
        self._count.text = f"{done}/{total}"
        self._count.color = theme.GOLD if done < total else theme.ACCENT_CYAN
        self._title.text = "[b]今日任务[/b]"
        gold_hex = "ffb400"
        muted_hex = "8588a0"
        parts = []
        for p in plan[:6]:
            if p["completed"]:
                parts.append(f"[color={gold_hex}]{p['exercise_name']}[/color]")
            else:
                parts.append(f"[color={muted_hex}]{p['exercise_name']}[/color]")
        self._sub.text = "  ".join(parts) + (" …" if len(plan) > 6 else "")
        self._redraw_track()
