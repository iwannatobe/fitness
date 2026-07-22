from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, RoundedRectangle
import theme
import database as db
from panels.strength import STRENGTH_PRESETS
from panels.cardio import CARDIO_PRESETS
from panels.preset_grid import EXERCISE_ICONS, EXERCISE_COLORS, _rgba_hex
from config.constants import TEMPLATE_ICONS, TEMPLATE_COLORS

class _WheelLabel(Label):
    def __init__(self, plan_popup, idx, key, min_val, max_val, signed=False, **kwargs):
        super().__init__(**kwargs)
        self.pp = plan_popup
        self.idx = idx
        self.key = key
        self.min_val = min_val
        self.max_val = max_val
        self.signed = signed
        self._last_y = None

    def _format(self, val):
        if not self.signed:
            return str(int(val))
        if val > 0:
            return f"+{int(val)}"
        return str(int(val))

    def _color_for(self, val):
        if not self.signed:
            return theme.TEXT_PRIMARY
        if val > 0:
            return (0.92, 0.26, 0.26, 1)
        if val < 0:
            return theme.ACCENT_CYAN
        return theme.TEXT_MUTED

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self._last_y = touch.y
            self.color = theme.GOLD
            return True
        return False

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            dy = touch.y - self._last_y
            if abs(dy) > dp(4):
                delta = 1 if dy > 0 else -1
                item = self.pp._selected[self.idx]
                cur = int(float(item.get(self.key, 0)))
                new_val = max(self.min_val, min(self.max_val, cur + delta))
                self.pp._update_item(self.idx, self.key, new_val)
                self.text = self._format(new_val)
                self._last_y = touch.y
            return True
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            item = self.pp._selected[self.idx]
            cur = int(float(item.get(self.key, 0)))
            self.color = self._color_for(cur)
            return True
        return False

class PlanPopup(FloatLayout):
    def __init__(self, on_confirm, **kwargs):
        super().__init__(size_hint=(1, 1), **kwargs)
        self._on_confirm = on_confirm
        self._selected = []
        self._current_tmpl_id = None
        self._preview_labels = {}
        self._build_ui()

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        return True

    def on_touch_move(self, touch):
        super().on_touch_move(touch)
        return True

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        return True

    def _build_ui(self):
        self.clear_widgets()
        with self.canvas.before:
            Color(0, 0, 0, 0.85)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda _, p: setattr(self._bg, "pos", p),
                  size=lambda _, s: setattr(self._bg, "size", s))

        card = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10),
                         size_hint=(0.92, 0.95), pos_hint={"center_x": 0.5, "center_y": 0.5})
        with card.canvas.before:
            Color(*theme.SURFACE)
            self._card_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(theme.CARD_RADIUS)])
        card.bind(pos=lambda _, p: setattr(self._card_rect, "pos", p),
                  size=lambda _, s: setattr(self._card_rect, "size", s))
        self.add_widget(card)

        hdr = BoxLayout(size_hint_y=None, height=dp(36))
        hdr.add_widget(Label(text="[font=Symbols]☢[/font]  部署今日任务",
                             markup=True, color=theme.GOLD, font_size=dp(18),
                             halign="left", valign="middle"))
        close_btn = Button(text="[font=Symbols]✕[/font]", size_hint_x=None, width=dp(36),
                           background_normal="", background_color=(0,0,0,0),
                           color=theme.TEXT_MUTED, font_size=dp(18), markup=True)
        close_btn.bind(on_press=lambda _: self._dismiss())
        hdr.add_widget(close_btn)
        card.add_widget(hdr)

        card.add_widget(Label(text="选择训练模板", color=theme.TEXT_MUTED,
                              font_size=dp(11), size_hint_y=None, height=dp(18)))

        # Template grid — 固定六个预设模板，3列2行
        template_grid = GridLayout(cols=3, size_hint_y=None, spacing=dp(6))
        template_grid.bind(minimum_height=template_grid.setter("height"))
        self._tmpl_id = {}
        self._tmpl_name = {}
        self._tmpl_items = {}
        self._tmpl_press = {}
        for tmpl in db.get_templates():
            name = tmpl["name"]
            tid = tmpl["id"]
            items = tmpl["items"]
            self._tmpl_id[name] = tid
            self._tmpl_name[name] = name
            self._tmpl_items[name] = items
            icon = TEMPLATE_ICONS.get(name, "")
            clr = TEMPLATE_COLORS.get(name, theme.GOLD)
            if icon:
                hex_clr = _rgba_hex(clr)
                display = f"[color={hex_clr}][font=Symbols]{icon}[/font][/color] {name}"
            else:
                display = name
            btn = Button(text=display, markup=bool(icon), size_hint=(1, None), height=dp(40),
                         background_normal="", background_color=theme.SURFACE_LIGHT,
                         color=theme.TEXT_PRIMARY, font_size=dp(13))
            btn.bind(on_release=lambda _, b=btn: self._tmpl_release(b))
            self._tmpl_press[btn] = {"name": name}
            template_grid.add_widget(btn)
        card.add_widget(template_grid)


        # Exercise grid (strength + cardio) — 缩小
        scroll = ScrollView(size_hint_y=None, height=dp(150), do_scroll_x=False, do_scroll_y=True)
        ex_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        ex_box.bind(minimum_height=ex_box.setter("height"))

        ex_box.add_widget(Label(text="力量训练", color=theme.STRENGTH_ORANGE,
                                font_size=dp(12), size_hint_y=None, height=dp(18)))
        presets = list(STRENGTH_PRESETS)
        for name in db.get_custom_exercises("strength"):
            if name not in presets: presets.append(name)
        self._strength_grid = GridLayout(cols=4, size_hint_y=None, spacing=dp(3))
        self._strength_grid.bind(minimum_height=self._strength_grid.setter("height"))
        for name in presets:
            self._strength_grid.add_widget(self._make_exercise_btn(name, "strength"))
        ex_box.add_widget(self._strength_grid)

        ex_box.add_widget(Label(text="有氧运动", color=theme.CARDIO_BLUE,
                                font_size=dp(12), size_hint_y=None, height=dp(18)))
        presets = list(CARDIO_PRESETS)
        for name in db.get_custom_exercises("cardio"):
            if name not in presets: presets.append(name)
        self._cardio_grid = GridLayout(cols=4, size_hint_y=None, spacing=dp(3))
        self._cardio_grid.bind(minimum_height=self._cardio_grid.setter("height"))
        for name in presets:
            self._cardio_grid.add_widget(self._make_exercise_btn(name, "cardio"))
        ex_box.add_widget(self._cardio_grid)

        scroll.add_widget(ex_box)
        card.add_widget(scroll)

        # Selected items — 放大
        card.add_widget(Label(text="已选动作", color=theme.GOLD,
                              font_size=dp(13), size_hint_y=None, height=dp(20), bold=True))
        self._selected_box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self._selected_box.bind(minimum_height=self._selected_box.setter("height"))
        self._selected_scroll = ScrollView(size_hint_y=None, height=dp(200),
                                            do_scroll_x=False, do_scroll_y=True)
        self._selected_scroll.add_widget(self._selected_box)
        card.add_widget(self._selected_scroll)

        # Confirm button
        confirm_btn = Button(text="确认部署 [font=Symbols]☢[/font]",
                             size_hint_y=None, height=dp(46),
                             background_normal="", background_color=theme.ACCENT,
                             color=(0,0,0,1), font_size=dp(15), markup=True)
        confirm_btn.bind(on_release=lambda _: self._confirm())
        card.add_widget(confirm_btn)

    def _make_exercise_btn(self, name, ex_type):
        icon = EXERCISE_ICONS.get(name, "•")
        clr = EXERCISE_COLORS.get(name, theme.TEXT_MUTED)
        hex_clr = _rgba_hex(clr)
        display = "[color=" + hex_clr + "][font=Symbols]" + icon + "[/font][/color] " + name
        btn = Button(text=display, markup=True, size_hint=(1, None), height=dp(36),
                     background_normal="", background_color=theme.SURFACE_LIGHT,
                     color=theme.TEXT_PRIMARY, font_size=dp(11))
        btn.bind(on_press=lambda _, n=name, t=ex_type: self._add_to_selected(t, n))
        return btn

    def _add_to_selected(self, ex_type, name):
        self._current_tmpl_id = None
        item = {"type": ex_type, "name": name}
        if ex_type == "strength":
            item.update({"sets": 3, "reps": 10, "weight": 0})
        else:
            item.update({"distance": 0, "duration": 30})
        self._selected.append(item)
        self._refresh_selected()

    def _tmpl_release(self, btn):
        import copy
        info = self._tmpl_press[btn]
        name = info["name"]
        self._current_tmpl_id = self._tmpl_id[name]
        self._selected = copy.deepcopy(self._tmpl_items[name])
        self._refresh_selected()

    def _refresh_selected(self):
        self._selected_box.clear_widgets()
        for idx, item in enumerate(self._selected):
            self._selected_box.add_widget(self._make_selected_row(idx, item))

    def _make_selected_row(self, idx, item):
        row = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(70),
                        spacing=dp(2), padding=[dp(6), dp(2)])
        with row.canvas.before:
            Color(*theme.SURFACE_LIGHT)
            RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(8)])
        row._bg_rect = None

        def redraw(*_):
            for instr in row.canvas.before.children:
                if isinstance(instr, RoundedRectangle):
                    instr.pos = row.pos
                    instr.size = row.size
        row.bind(pos=redraw, size=redraw)

        line1 = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(4))
        line1.add_widget(Label(text=item["name"], color=theme.TEXT_PRIMARY,
                               size_hint_x=0.30, font_size=dp(12), bold=True,
                               halign="left", valign="middle"))
        if item.get("type") == "strength":
            line1.add_widget(self._make_stepper(idx, "sets", item.get("sets", 3), 1, 20))
            line1.add_widget(Label(text="组", color=theme.TEXT_MUTED,
                                   size_hint_x=0.04, font_size=dp(12)))
            line1.add_widget(self._make_stepper(idx, "reps", item.get("reps", 10), 1, 50))
            line1.add_widget(Label(text="次", color=theme.TEXT_MUTED,
                                   size_hint_x=0.04, font_size=dp(12)))
            line1.add_widget(self._make_stepper(idx, "weight", item.get("weight", 0), 0, 300))
            line1.add_widget(Label(text="kg", color=theme.TEXT_MUTED,
                                   size_hint_x=0.04, font_size=dp(12)))
        else:
            line1.add_widget(self._make_stepper(idx, "distance", item.get("distance", 0), 0, 100))
            line1.add_widget(Label(text="km", color=theme.TEXT_MUTED,
                                   size_hint_x=0.04, font_size=dp(12)))
            line1.add_widget(self._make_stepper(idx, "duration", item.get("duration", 30), 1, 300))
            line1.add_widget(Label(text="min", color=theme.TEXT_MUTED,
                                   size_hint_x=0.04, font_size=dp(12)))
        del_btn = Button(text="×", size_hint_x=0.08,
                         background_normal="", background_color=(0, 0, 0, 0),
                         color=theme.DANGER, font_size=dp(14), bold=True)
        del_btn.bind(on_press=lambda _, i=idx: self._remove_item(i))
        line1.add_widget(del_btn)
        row.add_widget(line1)

        if item.get("type") == "strength":
            line2 = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(4))
            line2.add_widget(Label(text="递增减", color=theme.TEXT_MUTED,
                                   size_hint_x=0.16, font_size=dp(11),
                                   halign="right", valign="middle"))
            line2.add_widget(self._make_stepper(idx, "weight_step", item.get("weight_step", 0), -50, 50, signed=True))
            line2.add_widget(Label(text="kg/组", color=theme.TEXT_MUTED,
                                   size_hint_x=0.08, font_size=dp(11)))
            line2.add_widget(self._make_stepper(idx, "rep_step", item.get("rep_step", 0), -20, 20, signed=True))
            line2.add_widget(Label(text="次/组", color=theme.TEXT_MUTED,
                                   size_hint_x=0.08, font_size=dp(11)))
            self._preview_labels[idx] = None
            preview = Label(text="", color=theme.ACCENT_CYAN, font_size=dp(10),
                            size_hint_x=0.40, halign="left", valign="middle")
            preview.bind(size=preview.setter("text_size"))
            self._preview_labels[idx] = preview
            line2.add_widget(preview)
            row.add_widget(line2)
            self._update_preview(idx, item)
        return row

    def _make_stepper(self, idx, key, initial, min_val, max_val, signed=False):
        box = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(34), spacing=dp(0))
        up = Label(text="▲", color=theme.TEXT_MUTED, font_size=dp(10),
                   halign="center", valign="middle", size_hint_y=0.15)
        box.add_widget(up)
        init_val = int(initial)
        if signed:
            init_text = (f"+{init_val}" if init_val > 0 else str(init_val))
            init_color = ((0.92, 0.26, 0.26, 1) if init_val > 0
                          else theme.ACCENT_CYAN if init_val < 0
                          else theme.TEXT_MUTED)
        else:
            init_text = str(init_val)
            init_color = theme.TEXT_PRIMARY
        wheel = _WheelLabel(plan_popup=self, idx=idx, key=key, min_val=min_val, max_val=max_val,
                            signed=signed, text=init_text, color=init_color,
                            font_size=dp(14), bold=True, halign="center", valign="middle",
                            size_hint_y=0.7)
        wheel.bind(size=wheel.setter("text_size"))
        box.add_widget(wheel)
        down = Label(text="▼", color=theme.TEXT_MUTED, font_size=dp(10),
                     halign="center", valign="middle", size_hint_y=0.15)
        box.add_widget(down)
        return box

    def _update_item(self, idx, key, value):
        if idx < len(self._selected):
            self._selected[idx][key] = value
            self._update_preview(idx, self._selected[idx])

    def _update_preview(self, idx, item):
        if idx not in self._preview_labels:
            return
        lbl = self._preview_labels[idx]
        if lbl is None:
            return
        sets = int(item.get("sets", 0) or 0)
        reps = int(item.get("reps", 0) or 0)
        w = float(item.get("weight", 0) or 0)
        ws = float(item.get("weight_step", 0) or 0)
        rs = int(item.get("rep_step", 0) or 0)
        if sets <= 0:
            lbl.text = ""
            return
        per_group = []
        for s in range(sets):
            gw = w + ws * s
            gr = reps + rs * s
            per_group.append(f"{int(gw)}/{int(gr)}")
        lbl.text = "  ".join(per_group)

    def _remove_item(self, idx):
        if idx < len(self._selected):
            self._selected.pop(idx)
            self._refresh_selected()

    def _confirm(self):
        if not self._selected: return
        db.clear_today_plan()
        for item in self._selected:
            if item.get("type") == "strength":
                db.add_plan_item(item_type="strength", exercise_name=item["name"],
                                 target_sets=item.get("sets"), target_reps=item.get("reps"),
                                 target_weight=item.get("weight", 0),
                                 target_weight_step=item.get("weight_step", 0),
                                 target_rep_step=item.get("rep_step", 0),
                                 exercise_id=item.get("exercise_id"))
            else:
                db.add_plan_item(item_type="cardio", exercise_name=item["name"],
                                 target_distance=item.get("distance"),
                                 target_duration=item.get("duration"),
                                 exercise_id=item.get("exercise_id"))
        if self._current_tmpl_id is not None:
            tmpl = next((t for t in db.get_templates() if t["id"] == self._current_tmpl_id), None)
            if tmpl:
                db.update_template(self._current_tmpl_id, tmpl["name"], self._selected)
        self._on_confirm(self._current_tmpl_id)
        self._dismiss()

    def _dismiss(self):
        if self.parent:
            self.parent.remove_widget(self)
