from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, RoundedRectangle
from datetime import date

import theme
import database as db
from topbar import TopBar
from calendar_widget import CalendarHeatmap
from panels import StrengthPanel, CardioPanel, BodyPanel, StatsPanel
from nuke_button import NukeButton
from nuke_effects import shake_widget, flash_screen, explode_particles
from battle_report import show_battle_report
from plan_popup import PlanPopup
from warmup_widget import WarmupWidget
from task_card import TaskCard
from ai_chat import AIChatPanel
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

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos): return False
        self._touch_start = (touch.x, touch.y); self._dragging = False
        try: self._drag_cur = self._names.index(self.sm.current)
        except ValueError: self._drag_cur = 0
        touch.grab(self)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self or self._touch_start is None: return False
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
        if touch.grab_current is not self: return False
        touch.ungrab(self)
        self._touch_start = None; self._dragging = False
        return True

    def _pos_to_idx(self, y):
        n = len(self._names); margin = dp(16)
        track_h = self.height - margin * 2; segment = track_h / (n - 1)
        track_y = self.y + margin
        return max(0, min(n - 1, round((y - track_y) / segment)))


class MainLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def init_ui(self):
        self.sm = ScreenManager(transition=SlideTransition())
        self._screen_order = ["home", "strength", "cardio", "body", "stats", "ai"]

        screens = [
            ("home", "CALENDAR\n日历", self._build_home),
            ("strength", "STRENGTH\n力量训练", self._build_strength),
            ("cardio", "CARDIO\n有氧运动", self._build_cardio),
            ("body", "BODY DATA\n身体数据", self._build_body),
            ("stats", "STATISTICS\n统计数据", self._build_stats),
            ("ai", "AI ASSISTANT\nAI 助手", self._build_ai),
        ]
        for name, title, builder in screens:
            s = Screen(name=name)
            box = BoxLayout(orientation="vertical")
            box.add_widget(TopBar(title))
            box.add_widget(builder())
            s.add_widget(box)
            self.sm.add_widget(s)

        self.add_widget(self.sm)
        self._page_bar = PageBar(self._screen_order, self.sm)
        self.add_widget(self._page_bar)

    def _build_home(self):
        root = BoxLayout(orientation="vertical",
                         padding=[dp(theme.PAGE_MARGIN), dp(theme.PAGE_MARGIN),
                                  dp(theme.PAGE_MARGIN), dp(theme.PAGE_MARGIN)],
                         spacing=dp(theme.CARD_SPACING))

        top_row = BoxLayout(orientation="horizontal",
                            size_hint_y=None, height=dp(220),
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
    def _build_ai(self): return AIChatPanel()

    def _do_nuke(self, btn):
        is_first = not btn.nuked_today
        if is_first:
            db.add_nuke_marker(date.today().isoformat())
            btn.nuked_today = True
        popup = PlanPopup(on_confirm=lambda tid: self._on_plan_confirmed(btn, tid))
        self.add_widget(popup)

    def _on_plan_confirmed(self, btn, template_id=None):
        self._nuke_template_id = template_id
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
        # 全部完成 → 把当前训练量同步回模板
        self._sync_to_template_if_all_done()

    def _sync_to_template_if_all_done(self):
        tid = getattr(self, "_nuke_template_id", None)
        if tid is None:
            return
        plan = db.get_today_plan()
        if not plan or not all(p["completed"] for p in plan):
            return
        tmpls = db.get_templates()
        tmpl = next((t for t in tmpls if t["id"] == tid), None)
        if not tmpl:
            self._nuke_template_id = None
            return
        updated_items = []
        for tp_item in tmpl["items"]:
            plan_item = next(
                (p for p in plan
                 if ((p.get("exercise_id") and p.get("exercise_id") == tp_item.get("exercise_id"))
                     or p["exercise_name"] == tp_item.get("name"))
                 and p["item_type"] == tp_item.get("type")), None)
            if plan_item:
                new_item = dict(tp_item)
                if plan_item["item_type"] == "strength":
                    new_item["sets"] = plan_item.get("target_sets") or tp_item.get("sets", 0)
                    new_item["reps"] = plan_item.get("target_reps") or tp_item.get("reps", 0)
                    new_item["weight"] = plan_item.get("target_weight") or tp_item.get("weight", 0)
                    new_item["weight_step"] = int(plan_item.get("target_weight_step") or tp_item.get("weight_step", 0))
                    new_item["rep_step"] = int(plan_item.get("target_rep_step") or tp_item.get("rep_step", 0))
                else:
                    new_item["distance"] = plan_item.get("target_distance") or tp_item.get("distance", 0)
                    new_item["duration"] = int(plan_item.get("target_duration") or tp_item.get("duration", 0))
                updated_items.append(new_item)
            else:
                updated_items.append(tp_item)
        db.update_template(tid, tmpl["name"], updated_items)
        self._nuke_template_id = None

    def refresh_heatmap(self):
        if hasattr(self, "_heatmap"): self._heatmap.refresh()
        if hasattr(self, "_task_card"): self._task_card.refresh()
