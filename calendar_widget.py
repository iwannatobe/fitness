
import calendar as cal
from datetime import date
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
import theme
import database as db
import sounds

class RoundedButton(Button):
    def __init__(self, text="", bg_color=(0.1,0.1,0.1,1), color=(1,1,1,1),
                 size_hint=(None,None), size=(40,40), font_size=12,
                 bold=False, markup=False, radius=None, **kwargs):
        super().__init__(text=text, size_hint=size_hint, size=size,
                         font_size=font_size, bold=bold, markup=markup,
                         background_normal="", background_color=(0,0,0,0),
                         color=color, **kwargs)
        self._radius = radius if radius is not None else min(size) * 0.15
        self._orig_color = bg_color
        self._bg_color = bg_color
        self.bind(pos=self._draw, size=self._draw)
        self.bind(on_press=self._on_down, on_release=self._on_up)
    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
    def set_color(self, bg_color):
        self._bg_color = bg_color
        self._draw()
    def _on_down(self, *_):
        sounds.play_click()
        self._bg_color = sounds.lighten(self._orig_color)
        self._draw()
    def _on_up(self, *_):
        self._bg_color = self._orig_color
        self._draw()

class CalendarHeatmap(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.active_dates = db.get_active_dates()
        self.nuked_dates = db.get_nuke_dates()
        self._current_date = date.today()
        self._rebuild_trigger = None
        self._touch_start = None
        self._swipe_threshold = 50
        self._animating = False
        self._grid_area = None
        self._grid = None
        self.bind(size=self._on_resize)
        Clock.schedule_once(lambda dt: self._build(), 0)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self._animating:
            self._touch_start = touch.pos
            return super().on_touch_down(touch)
        return False

    def on_touch_up(self, touch):
        if self._touch_start:
            dx = touch.pos[0] - self._touch_start[0]
            if abs(dx) > self._swipe_threshold:
                if dx > 0: self._prev_month()
                else: self._next_month()
                self._touch_start = None
                return True
            self._touch_start = None
        return super().on_touch_up(touch)

    def _on_resize(self, *_):
        if self._rebuild_trigger:
            Clock.unschedule(self._rebuild_trigger)
        self._rebuild_trigger = Clock.schedule_once(lambda dt: self._build(), 0.08)

    def _scale(self, base, ratio):
        return max(1, int(base * ratio))

    def _make_grid(self, year, month, w, cell_size, spacing, cols, font_size):
        cal_obj = cal.Calendar(firstweekday=0)
        month_days = cal_obj.monthdayscalendar(year, month)
        total_rows = 7 + len(month_days)
        grid_w = cell_size * cols + spacing * (cols - 1)
        grid_h = cell_size * total_rows + spacing * (total_rows - 1)
        grid = GridLayout(cols=cols, spacing=spacing, size_hint=(None,None), size=(grid_w, grid_h))
        for day_name in ["一","二","三","四","五","六","日"]:
            lbl = Label(text=day_name, font_size=font_size, color=theme.TEXT_MUTED,
                        size_hint=(None,None), size=(cell_size,cell_size),
                        halign="center", valign="middle", bold=True)
            lbl.bind(size=lbl.setter("text_size"))
            grid.add_widget(lbl)
        today = date.today()
        for week in month_days:
            for day_num in week:
                if day_num == 0:
                    grid.add_widget(BoxLayout(size_hint=(None,None), size=(cell_size,cell_size)))
                    continue
                d = date(year, month, day_num)
                d_str = d.isoformat()
                info = self.active_dates.get(d_str)
                if d > today:
                    clr = (0.05, 0.05, 0.07, 0.25)
                    tclr = theme.TEXT_MUTED
                elif info:
                    has_s = info.get("strength", False)
                    has_c = info.get("cardio", False)
                    if has_s and has_c:
                        clr = theme.ACCENT; tclr = (0.05, 0.05, 0.08, 1)
                    elif has_s:
                        clr = theme.STRENGTH_ORANGE; tclr = (0.05, 0.05, 0.08, 1)
                    else:
                        clr = theme.CARDIO_BLUE; tclr = (0.05, 0.05, 0.08, 1)
                else:
                    clr = theme.SURFACE_LIGHT; tclr = theme.TEXT_SECONDARY
                if d == today:
                    if info:
                        has_s = info.get("strength", False)
                        has_c = info.get("cardio", False)
                        if has_s and has_c: clr = theme.ACCENT
                        elif has_s: clr = theme.STRENGTH_ORANGE
                        else: clr = theme.CARDIO_BLUE
                    else:
                        clr = theme.TODAY_RING
                    tclr = theme.TEXT_PRIMARY
                is_nuked = d_str in self.nuked_dates
                if is_nuked:
                    display_text = "[font=Symbols]☢[/font]" + str(day_num)
                else:
                    display_text = str(day_num)
                cell = RoundedButton(text=display_text, bg_color=clr, color=tclr,
                                     size_hint=(None,None), size=(cell_size,cell_size),
                                     font_size=font_size, bold=(d == today), markup=is_nuked)
                cell.bind(on_release=lambda _, ds=d_str: self._show_day(ds))
                grid.add_widget(cell)
        return grid

    def _build(self, *args):
        self.clear_widgets()
        year = self._current_date.year
        month = self._current_date.month
        w, h = self.size
        if w < 10 or h < 10: return
        ref = 400.0
        scale = w / ref if w > 0 else 1.0
        pad_h = self._scale(10, scale)
        pad_v = self._scale(10, scale)
        spacing = max(1, self._scale(2, scale))
        cols = 7
        bottom_h = max(1, int(h * 0.03))
        gap = max(1, self._scale(4, scale))
        grid_area_h = h - bottom_h - pad_v - gap
        cal_obj = cal.Calendar(firstweekday=0)
        month_days = cal_obj.monthdayscalendar(year, month)
        total_rows = 7 + len(month_days)
        cell_w = (w - pad_h * 2 - spacing * (cols - 1)) // cols
        cell_h = (grid_area_h - spacing * (total_rows - 1)) // total_rows if total_rows > 0 else 0
        cell_size = max(1, min(cell_w, cell_h))
        font_size = max(1, int(cell_size * 0.38))
        self._grid_area = FloatLayout(size_hint_y=None, height=grid_area_h)
        grid = self._make_grid(year, month, w, cell_size, spacing, cols, font_size)
        grid.x = (w - grid.width) / 2
        grid.y = (grid_area_h - grid.height) / 2
        self._grid_area.add_widget(grid)
        self._grid = grid
        self.add_widget(self._grid_area)
        bar = BoxLayout(size_hint_y=None, height=bottom_h,
                        spacing=self._scale(4, scale),
                        padding=[self._scale(8, scale), 0, self._scale(8, scale), 0])
        with bar.canvas.before:
            Color(0.10, 0.105, 0.13, 0.9)
            self._bar_bg = Rectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda _, p: setattr(self._bar_bg, "pos", p),
                 size=lambda _, s: setattr(self._bar_bg, "size", s))
        arrow_fs = max(1, int(font_size * 1.3))
        prev_btn = Button(text="<", size_hint=(None, None),
                          size=(self._scale(24, scale), bottom_h),
                          background_normal="", background_color=(0,0,0,0),
                          font_size=arrow_fs, color=theme.TEXT_SECONDARY, bold=True)
        sounds.bind_feedback(prev_btn, text_color=theme.TEXT_SECONDARY)
        prev_btn.bind(on_release=lambda _: self._prev_month())
        bar.add_widget(prev_btn)
        bar.add_widget(BoxLayout(size_hint_x=None, width=self._scale(6, scale)))
        bar.add_widget(Label(text=f"{year}/{month:02d}",
                             font_size=max(1, int(font_size * 0.8)),
                             color=theme.TEXT_PRIMARY,
                             size_hint_x=None, width=self._scale(70, scale)))
        bar.add_widget(BoxLayout(size_hint_x=None, width=self._scale(6, scale)))
        next_btn = Button(text=">", size_hint=(None, None),
                          size=(self._scale(24, scale), bottom_h),
                          background_normal="", background_color=(0,0,0,0),
                          font_size=arrow_fs, color=theme.TEXT_SECONDARY, bold=True)
        sounds.bind_feedback(next_btn, text_color=theme.TEXT_SECONDARY)
        next_btn.bind(on_release=lambda _: self._next_month())
        bar.add_widget(next_btn)
        lf = max(1, int(font_size * 0.75))
        sq = max(1, bottom_h - 2)
        for lbl_text, shade in [("力量", theme.STRENGTH_ORANGE), ("有氧", theme.CARDIO_BLUE), ("两者", theme.ACCENT)]:
            bar.add_widget(Label(text=lbl_text, font_size=lf, size_hint_x=None,
                                 width=self._scale(28, scale), color=theme.TEXT_MUTED))
            bar.add_widget(RoundedButton(bg_color=shade, color=(1,1,1,0),
                                         size_hint=(None, None), size=(sq, sq),
                                         radius=sq / 2))
        bar.add_widget(BoxLayout())
        self.add_widget(bar)

    def _show_day(self, d_str):
        s_rows, c_rows = db.get_date_detail(d_str)
        lines = []
        if s_rows:
            lines.append("[b]力量训练[/b]")
            for r in s_rows:
                lines.append("  %s  %sx%s  %skg" % (r["exercise_name"], r["sets"], r["reps"], r["weight"]))
        if c_rows:
            if lines: lines.append("")
            lines.append("[b]有氧运动[/b]")
            for r in c_rows:
                lines.append("  %s  %skm  %smin" % (r["exercise_type"], r["distance"], r["duration"]))
        if not lines:
            lines.append("无记录")
        content = Label(text="\n".join(lines), color=theme.TEXT_PRIMARY,
                        font_size=dp(14), markup=True, halign="left", valign="top",
                        padding=(dp(16), dp(12)))
        content.bind(size=content.setter("text_size"))
        popup = Popup(title=d_str, title_color=theme.TEXT_PRIMARY,
                      content=content, size_hint=(0.65, 0.35),
                      background="", background_color=theme.SURFACE, border=(0,0,0,0))
        popup.open()

    def _animate_switch(self, direction):
        if self._animating or not self._grid_area or not self._grid: return
        self._animating = True
        w, h = self.size
        scale = w / 400.0 if w > 0 else 1.0
        pad_h = self._scale(10, scale)
        spacing = max(1, self._scale(2, scale))
        cols = 7
        grid_area_h = self._grid_area.height
        year = self._current_date.year
        month = self._current_date.month
        cal_obj = cal.Calendar(firstweekday=0)
        month_days = cal_obj.monthdayscalendar(year, month)
        total_rows = 7 + len(month_days)
        cell_w = (w - pad_h * 2 - spacing * (cols - 1)) // cols
        cell_h = (grid_area_h - spacing * (total_rows - 1)) // total_rows if total_rows > 0 else 0
        cell_size = max(1, min(cell_w, cell_h))
        font_size = max(1, int(cell_size * 0.38))
        old_grid = self._grid
        new_grid = self._make_grid(year, month, w, cell_size, spacing, cols, font_size)
        center_x = (w - new_grid.width) / 2
        center_y = (grid_area_h - new_grid.height) / 2
        offset = w if direction == -1 else -w
        new_grid.x = center_x + offset
        new_grid.y = center_y
        self._grid_area.add_widget(new_grid)
        anim_old = Animation(x=old_grid.x - offset, duration=0.25, transition="out_quart")
        anim_new = Animation(x=center_x, duration=0.25, transition="out_quart")
        def on_complete(*_):
            self._grid_area.remove_widget(old_grid)
            self._grid = new_grid
            self._animating = False
        anim_new.bind(on_complete=on_complete)
        anim_old.start(old_grid)
        anim_new.start(new_grid)

    def _prev_month(self):
        if self._animating: return
        y, m = self._current_date.year, self._current_date.month
        self._current_date = date(y-1, 12, 1) if m == 1 else date(y, m-1, 1)
        self._animate_switch(1)

    def _next_month(self):
        if self._animating: return
        y, m = self._current_date.year, self._current_date.month
        self._current_date = date(y+1, 1, 1) if m == 12 else date(y, m+1, 1)
        self._animate_switch(-1)

    def refresh(self):
        self.active_dates = db.get_active_dates()
        self.nuked_dates = db.get_nuke_dates()
        self._build()
