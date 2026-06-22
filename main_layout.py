from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import BooleanProperty
from kivy.graphics import Color, Rectangle, RoundedRectangle
from datetime import date

import theme
import database as db
from topbar import TopBar
from sidebar import Sidebar
from calendar_widget import CalendarHeatmap
from panels import StrengthPanel, CardioPanel, BodyPanel, StatsPanel
from nuke_button import NukeButton
from nuke_effects import shake_widget, flash_screen, explode_particles
from battle_report import show_battle_report
from plan_popup import PlanPopup
from warmup_widget import WarmupWidget
from task_card import TaskCard
from utils.card import CardHolder


class PageBar(FloatLayout):
    def __init__(self, names, sm, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(44), dp(200)), pos_hint={"x": 0, "y": 0.08}, **kwargs)
        self._names = names; self.sm = sm
        self._touch_start = None; self._dragging = False; self._drag_cur = 0
        self.bind(pos=self._draw, size=self._draw)
        sm.bind(current=self._on_screen_changed)

    def _on_screen_changed(self, *_): self._draw()

    def _draw(self, *_):
        self.canvas.before.clear()
        n = len(self._names)
        if n < 2: return
        try: cur = self._names.index(self.sm.current)
        except ValueError: cur = 0
        margin = dp(16); track_w = dp(4); track_h = self.height - margin * 2
        track_x = self.center_x - track_w / 2; track_y = self.y + margin
        pill_w = dp(18); pill_h = dp(36)
        segment = track_h / (n - 1); pill_cx = self.center_x; pill_cy = track_y + cur * segment
        with self.canvas.before:
            Color(*theme.SURFACE_LIGHT)
            Rectangle(pos=(track_x, track_y), size=(track_w, track_h))
            Color(*theme.GOLD)
            Rectangle(pos=(pill_cx - pill_w / 2, pill_cy - pill_h / 2), size=(pill_w, pill_h))

    def _pos_to_idx(self, y):
        n = len(self._names); margin = dp(16)
        track_h = self.height - margin * 2; segment = track_h / (n - 1)
        track_y = self.y + margin
        return max(0, min(n - 1, round((y - track_y) / segment)))

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos): return False
        self._touch_start = (touch.x, touch.y); self._dragging = False
        try: self._drag_cur = self._names.index(self.sm.current)
        except ValueError: self._drag_cur = 0
        return True

    def on_touch_move(self, touch):
        if self._touch_start is None: return False
        dy = abs(touch.y - self._touch_start[1])
        if dy > dp(10): self._dragging = True
        if self._dragging:
            idx = self._pos_to_idx(touch.y)
            if idx != self._drag_cur:
                self._drag_cur = idx
                self.sm.transition.direction = 'up' if touch.y < self._touch_start[1] else 'down'
                self.sm.current = self._names[idx]
        return True

    def on_touch_up(self, touch):
        if self._touch_start is None: return False
        if not self._dragging:
            try: idx = self._names.index(self.sm.current)
            except ValueError: idx = 0
            new_idx = (idx + 1) % len(self._names)
            self.sm.current = self._names[new_idx]
        self._touch_start = None; self._dragging = False
        return True


class MainLayout(FloatLayout):
    sidebar_open = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def init_ui(self):
        self.sidebar = Sidebar(self)
        self.sidebar.x = -dp(220)
        self.add_widget(self.sidebar)

        self.sm = ScreenManager(transition=SlideTransition())
        self._screen_order = ["home", "strength", "cardio", "body", "stats"]

        screens = [
            ("home", "CALENDAR", self._build_home),
            ("strength", "STRENGTH", self._build_strength),
            ("cardio", "CARDIO", self._build_cardio),
            ("body", "BODY", self._build_body),
            ("stats", "STATS", self._build_stats),
        ]
        for name, title, builder in screens:
            s = Screen(name=name)
            box = BoxLayout(orientation="vertical")
            box.add_widget(TopBar(title, on_menu=self.toggle_sidebar))
            box.add_widget(builder())
            s.add_widget(box)
            self.sm.add_widget(s)

        self.add_widget(self.sm)
        self._page_bar = PageBar(self._screen_order, self.sm)
        self.add_widget(self._page_bar)
        self.sm.bind(current=lambda *_: self.sidebar._sync_selection())

    def _build_home(self):
        root = BoxLayout(orientation="vertical",
                         padding=[dp(theme.PAGE_MARGIN), dp(theme.PAGE_MARGIN),
                                  dp(theme.PAGE_MARGIN), dp(theme.PAGE_MARGIN)],
                         spacing=dp(theme.CARD_SPACING))

        top_row = BoxLayout(orientation="horizontal",
                            size_hint_y=None, height=dp(180),
                            spacing=dp(theme.CARD_SPACING))
        nuke_btn = NukeButton(size_hint=(1, 1))
        nuke_btn.bind(on_release=lambda instance: self._do_nuke(instance))
        nuke_box = BoxLayout(orientation="vertical", spacing=dp(2))
        nuke_box.add_widget(nuke_btn)
        nuke_lbl = Label(text="[b]NUKE[/b]", markup=True, color=theme.TEXT_MUTED,
                         font_size=dp(theme.FONT_CAPTION), bold=True,
                         halign="center", valign="middle",
                         size_hint_y=None, height=dp(12))
        nuke_lbl.bind(size=nuke_lbl.setter("text_size"))
        nuke_box.add_widget(nuke_lbl)
        nuke_holder = CardHolder(nuke_box, padding=dp(8), bg=theme.SURFACE)
        nuke_holder.size_hint_x = 0.32
        top_row.add_widget(nuke_holder)
        self._warmup = WarmupWidget(size_hint=(1, 1),
                                    on_complete=self._on_task_completed)
        warmup_holder = CardHolder(self._warmup, padding=dp(12), bg=theme.SURFACE)
        warmup_holder.size_hint_x = 0.68
        top_row.add_widget(warmup_holder)
        root.add_widget(top_row)

        self._task_card = TaskCard()
        root.add_widget(self._task_card)

        self._heatmap = CalendarHeatmap()
        heatmap_holder = CardHolder(self._heatmap, padding=dp(6), bg=theme.SURFACE)
        root.add_widget(heatmap_holder)
        return root

    def _build_strength(self):
        self._strength_panel = StrengthPanel(self)
        return self._strength_panel
    def _build_cardio(self):
        self._cardio_panel = CardioPanel(self)
        return self._cardio_panel
    def _build_body(self): return BodyPanel(self)
    def _build_stats(self): return StatsPanel()

    def _do_nuke(self, btn):
        is_first = not btn.nuked_today
        if is_first:
            db.add_nuke_marker(date.today().isoformat())
            btn.nuked_today = True
        popup = PlanPopup(on_confirm=lambda: self._on_plan_confirmed(btn))
        self.add_widget(popup)

    def _on_plan_confirmed(self, btn):
        self.refresh_heatmap(); self._task_card.refresh()
        if hasattr(self, "_warmup"): self._warmup.show_warmups_for(db.get_today_plan())
        shake_widget(self.sm); flash_screen(self)
        win_x, win_y = btn.to_window(*btn.center)
        local_x, local_y = self.to_widget(win_x, win_y)
        explode_particles(self, local_x, local_y)
        Clock.schedule_once(lambda dt: show_battle_report(self), 0.9)

    def _on_task_completed(self):
        self.refresh_heatmap()
        if hasattr(self, "_task_card"): self._task_card.refresh()
        if hasattr(self, "_strength_panel"): self._strength_panel._refresh_list()
        if hasattr(self, "_cardio_panel"): self._cardio_panel._refresh_list()

    def on_touch_down(self, touch):
        if self.sidebar_open and touch.x > dp(220):
            self.close_sidebar(); return True
        return super().on_touch_down(touch)

    def toggle_sidebar(self):
        if self.sidebar_open: self.close_sidebar()
        else: self.open_sidebar()

    def open_sidebar(self):
        self.sidebar_open = True
        self.remove_widget(self.sidebar); self.add_widget(self.sidebar)
        Animation(x=0, duration=0.25).start(self.sidebar)

    def close_sidebar(self):
        self.sidebar_open = False
        Animation(x=-dp(220), duration=0.25).start(self.sidebar)

    def refresh_heatmap(self):
        if hasattr(self, "_heatmap"): self._heatmap.refresh()
        if hasattr(self, "_task_card"): self._task_card.refresh()
