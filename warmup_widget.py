from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from config import theme
import database as db


def _hex(c):
    r, g, b = int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)
    return f"{r:02x}{g:02x}{b:02x}"


def _fit_text(label, max_width, max_font=dp(14), min_font=dp(9)):
    """Reduce font size until text fits on one line at max_width."""
    if max_width <= 0:
        return
    label.text_size = (max_width, None)
    font = max_font
    while font >= min_font:
        label.font_size = font
        if label.texture_size[0] <= max_width:
            return
        font -= dp(1)
    label.font_size = min_font


class WarmupWidget(BoxLayout):
    def __init__(self, on_complete=None, **kwargs):
        super().__init__(orientation="vertical",
                         padding=[dp(2), dp(2)], spacing=dp(4), **kwargs)
        self._on_complete = on_complete
        self._current_pid = None

        hdr = BoxLayout(size_hint_y=None, height=dp(16))
        self._title = Label(text="当前目标", color=theme.GOLD,
                            font_size=dp(theme.FONT_H3), bold=True,
                            halign="left", valign="middle", size_hint_x=1)
        self._title.bind(size=self._title.setter("text_size"))
        hdr.add_widget(self._title)
        self._count = Label(text="0/0", color=theme.TEXT_MUTED,
                            font_size=dp(theme.FONT_CAPTION), bold=True,
                            halign="right", valign="middle", size_hint_x=None, width=dp(44))
        self._count.bind(size=self._count.setter("text_size"))
        hdr.add_widget(self._count)
        self.add_widget(hdr)

        self._body = BoxLayout(orientation="vertical", size_hint=(1, 1))
        self.add_widget(self._body)
        self.refresh()

    def show_warmups_for(self, plan):
        self.refresh()

    def refresh(self):
        self._body.clear_widgets()
        plan = db.get_today_plan()
        if not plan:
            self._title.text = "当前目标"
            self._count.text = "—"
            self._body.add_widget(Label(text="点击核爆按钮部署任务", color=theme.TEXT_MUTED,
                                        font_size=dp(theme.FONT_CAPTION),
                                        halign="center", valign="middle"))
            return
        total = len(plan)
        done = sum(1 for p in plan if p["completed"])
        self._count.text = f"{done}/{total}"
        current = next((p for p in plan if not p["completed"]), None)
        if current is None:
            self._title.text = "全部完成"
            self._body.add_widget(Label(text="[b]\u2713  训练完成[/b]", markup=True,
                                        color=theme.ACCENT_CYAN, font_size=dp(theme.FONT_H2),
                                        halign="center", valign="middle", bold=True))
            return
        self._title.text = "当前目标"
        self._current_pid = current["id"]
        self._body.add_widget(self._make_card(current))

    def _make_card(self, p):
        card = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(4),
                         size_hint=(1, 1))
        with card.canvas.before:
            Color(*theme.SURFACE_HIGH)
            RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(10)])
            Color(*theme.BORDER)
            Line(rounded_rectangle=(card.x, card.y, card.width, card.height, dp(10)), width=dp(1))
        card._bg_rect = None
        card._border_line = None

        def redraw(*_):
            for instr in card.canvas.before.children:
                if isinstance(instr, RoundedRectangle):
                    instr.pos = card.pos
                    instr.size = card.size
                elif isinstance(instr, Line):
                    instr.rounded_rectangle = (card.x, card.y, card.width, card.height, dp(10))
        card.bind(pos=redraw, size=redraw)

        name = p["exercise_name"]
        if p["item_type"] == "strength":
            sets = int(p.get("target_sets") or 0)
            reps = int(p.get("target_reps") or 0)
            weight = float(p.get("target_weight") or 0)
            ws = float(p.get("target_weight_step") or 0)
            rs = int(p.get("target_rep_step") or 0)
            if (ws or rs) and sets > 1:
                end_w = weight + ws * (sets - 1)
                end_r = int(reps + rs * (sets - 1))
                w_lo = f"{weight:.0f}" if weight == int(weight) else f"{weight:.1f}"
                w_hi = f"{end_w:.0f}" if end_w == int(end_w) else f"{end_w:.1f}"
                r_lo = int(reps)
                r_hi = end_r
                if r_lo == r_hi:
                    target = f"{sets}组 × {r_lo}次  {w_lo}→{w_hi}kg"
                else:
                    target = f"{sets}组 {r_lo}→{r_hi}次  {w_lo}→{w_hi}kg"
            else:
                parts = [f"{sets}组", f"{reps}次"]
                if weight:
                    parts.append(f"{weight:.0f}kg" if weight == int(weight) else f"{weight:.1f}kg")
                target = " × ".join(parts)
            tag = "力量"
            tag_clr = theme.STRENGTH_ORANGE
        else:
            target = f"{p.get('target_distance') or 0}km × {p.get('target_duration') or 0}min"
            tag = "有氧"
            tag_clr = theme.CARDIO_BLUE

        tag_row = BoxLayout(size_hint_y=None, height=dp(14))
        tag_lbl = Label(text=f"[color={_hex(tag_clr)}][b]{tag}[/b][/color]",
                        markup=True, font_size=dp(theme.FONT_CAPTION),
                        halign="left", valign="middle", size_hint_x=1)
        tag_lbl.bind(size=tag_lbl.setter("text_size"))
        tag_row.add_widget(tag_lbl)
        card.add_widget(tag_row)

        name_lbl = Label(text=name, color=theme.TEXT_PRIMARY,
                         font_size=dp(14), bold=True,
                         halign="left", valign="middle",
                         size_hint_y=None, height=dp(22))
        name_lbl.bind(width=lambda i, w: _fit_text(i, w, max_font=dp(14), min_font=dp(10)))
        card.add_widget(name_lbl)

        target_lbl = Label(text=target, color=theme.TEXT_SECONDARY,
                           font_size=dp(12),
                           halign="left", valign="middle",
                           size_hint_y=None, height=dp(18))
        target_lbl.bind(width=lambda i, w: _fit_text(i, w, max_font=dp(12), min_font=dp(9)))
        card.add_widget(target_lbl)

        done_btn = Button(text="[b]\u2713  完成此项[/b]", markup=True,
                          size_hint=(1, None), height=dp(36),
                          background_normal="", background_color=theme.GOLD,
                          color=(0.05, 0.05, 0.08, 1), font_size=dp(theme.FONT_LABEL))
        done_btn.bind(on_release=lambda _: self._toggle(self._current_pid))
        card.add_widget(done_btn)
        return card

    def _toggle(self, pid):
        if pid is None:
            return
        plan = db.get_today_plan()
        item = next((p for p in plan if p["id"] == pid), None)
        if item and not item["completed"]:
            self._write_record(item)
        db.complete_plan_item(pid)
        self.refresh()
        if self._on_complete:
            self._on_complete()

    def _write_record(self, item):
        from datetime import date
        today = date.today().isoformat()
        if item["item_type"] == "strength":
            sets = int(item.get("target_sets") or 0)
            reps = int(item.get("target_reps") or 0)
            weight = float(item.get("target_weight") or 0)
            ws = float(item.get("target_weight_step") or 0)
            rs = int(item.get("target_rep_step") or 0)
            if sets <= 0:
                return
            for s in range(sets):
                db.add_strength(
                    exercise_name=item["exercise_name"],
                    sets=1,
                    reps=reps + rs * s,
                    weight=weight + ws * s,
                    record_date=today,
                    notes="",
                )
        else:
            db.add_cardio(
                exercise_type=item["exercise_name"],
                distance=item.get("target_distance") or 0,
                duration=item.get("target_duration") or 0,
                record_date=today,
                notes="",
            )
