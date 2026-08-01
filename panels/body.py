from datetime import date, timedelta

from kivy.graphics import Color, Rectangle, Line
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

import database as db
from config import theme
import sounds


class BodyPanel(BoxLayout):
    """Compact single-screen body-data entry panel.

    Uses a two-column input grid so the form fits on screen without scrolling,
    and forces light-on-dark text on every field for readability.
    """

    def __init__(self, main_layout, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(6),
                         padding=[dp(theme.PAGE_MARGIN)] * 4, **kwargs)
        self.main_layout = main_layout
        self._view_date = date.today()
        self._input_refs = {}
        with self.canvas.before:
            Color(*theme.CHASSIS)
            self._chassis = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_chassis, size=self._sync_chassis)

        self._build_header()
        self._build_form()
        self._build_records()
        self._refresh_list()

    # ---------- construction ----------

    def _sync_chassis(self, *_):
        self._chassis.pos = self.pos
        self._chassis.size = self.size

    def _make_input(self, text="", is_float=True):
        inp = TextInput(
            text=text, multiline=False, write_tab=False,
            input_filter="float" if is_float else None,
            font_size=dp(theme.FONT_BODY),
            foreground_color=(0.95, 0.96, 0.95, 1),
            background_color=theme.DISPLAY_GLASS,
            background_normal="", background_active="",
            cursor_color=theme.VFD_CYAN,
            hint_text_color=(0.55, 0.57, 0.56, 1),
            padding=(dp(8), dp(8)),
        )
        self._frame_input(inp)
        return inp

    @staticmethod
    def _frame_input(inp):
        with inp.canvas.before:
            Color(*theme.BORDER)
            inp._edge = Line(rectangle=(0, 0, 0, 0), width=dp(1))
            Color(*theme.GLASS_HIGHLIGHT)
            inp._glass = Line(points=[], width=dp(1))

        def sync(*_):
            inp._edge.rectangle = (inp.x, inp.y, inp.width, inp.height)
            inp._glass.points = [inp.x + dp(1), inp.top - dp(1),
                                 inp.right - dp(1), inp.top - dp(1)]
        inp.bind(pos=sync, size=sync)

    def _field_row(self, label_text, key, unit=None):
        row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        lbl = Label(text=label_text, color=theme.TEXT_SECONDARY,
                    font_size=dp(theme.FONT_BODY), halign="left", valign="middle",
                    size_hint_x=None, width=dp(72))
        lbl.bind(size=lbl.setter("text_size"))
        row.add_widget(lbl)
        inp = self._make_input(is_float=True)
        self._input_refs[key] = inp
        row.add_widget(inp)
        if unit:
            u = Label(text=unit, color=theme.TEXT_MUTED,
                      font_size=dp(theme.FONT_CAPTION), halign="left", valign="middle",
                      size_hint_x=None, width=dp(34))
            u.bind(size=u.setter("text_size"))
            row.add_widget(u)
        return row

    def _build_header(self):
        header = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        title = Label(text="[color=ff9d24][b]BODY DATA[/b][/color]  身体数据",
                      markup=True, color=theme.TEXT_PRIMARY,
                      font_size=dp(theme.FONT_H3), bold=True,
                      halign="left", valign="middle", size_hint_x=1)
        title.bind(size=title.setter("text_size"))
        header.add_widget(title)
        self.add_widget(header)

        date_bar = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        for arrow, delta in [("\u2039", -1), ("\u203a", 1)]:
            btn = Button(text=arrow, size_hint=(None, None), size=(dp(40), dp(30)),
                         background_normal="", background_color=theme.METAL_DARK,
                         font_size=dp(18), color=theme.TEXT_SECONDARY, bold=True)
            btn.bind(on_release=lambda _, d=delta: self._shift_date(d))
            sounds.bind_feedback(btn, bg_color=theme.METAL_DARK)
            date_bar.add_widget(btn)
        self._date_label = Label(text=self._view_date.isoformat(),
                                 font_size=dp(theme.FONT_H3), color=theme.VFD_CYAN,
                                 size_hint_x=1, bold=True, halign="center", valign="middle")
        self._date_label.bind(size=self._date_label.setter("text_size"))
        date_bar.add_widget(self._date_label)
        today_btn = Button(text="今天", size_hint=(None, None), size=(dp(56), dp(30)),
                           background_normal="", background_color=theme.VFD_ORANGE,
                           font_size=dp(theme.FONT_LABEL), color=theme.CHASSIS, bold=True)
        today_btn.bind(on_release=lambda _: self._goto_today())
        sounds.bind_feedback(today_btn, bg_color=theme.VFD_ORANGE)
        date_bar.add_widget(today_btn)
        self.add_widget(date_bar)

    def _build_form(self):
        grid = GridLayout(cols=2, size_hint_y=None, spacing=(dp(8), dp(6)))
        grid.bind(minimum_height=grid.setter("height"))
        grid.add_widget(self._field_row("体重", "weight", "kg"))
        grid.add_widget(self._field_row("体脂率", "body_fat", "%"))
        grid.add_widget(self._field_row("胸围", "chest", "cm"))
        grid.add_widget(self._field_row("腰围", "waist", "cm"))
        grid.add_widget(self._field_row("臂围", "arm", "cm"))
        date_inp = self._make_input(self._view_date.isoformat(), is_float=False)
        self._input_refs["date"] = date_inp
        date_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        d_lbl = Label(text="日期", color=theme.TEXT_SECONDARY,
                      font_size=dp(theme.FONT_BODY), halign="left", valign="middle",
                      size_hint_x=None, width=dp(72))
        d_lbl.bind(size=d_lbl.setter("text_size"))
        date_row.add_widget(d_lbl)
        date_row.add_widget(date_inp)
        grid.add_widget(date_row)
        self.add_widget(grid)

        notes = self._make_input(is_float=False)
        self._input_refs["notes"] = notes
        notes_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        n_lbl = Label(text="备注", color=theme.TEXT_SECONDARY,
                      font_size=dp(theme.FONT_BODY), halign="left", valign="middle",
                      size_hint_x=None, width=dp(72))
        n_lbl.bind(size=n_lbl.setter("text_size"))
        notes_box.add_widget(n_lbl)
        notes_box.add_widget(notes)
        self.add_widget(notes_box)

        save_btn = Button(text="SAVE / 保存", size_hint_y=None, height=dp(40),
                          background_normal="", background_color=theme.VFD_ORANGE,
                          color=theme.CHASSIS, font_size=dp(theme.FONT_H3), bold=True)
        save_btn.bind(on_release=lambda _: self._save())
        sounds.bind_feedback(save_btn, bg_color=theme.VFD_ORANGE)
        self.add_widget(save_btn)

    def _build_records(self):
        list_label = Label(text="记录", color=theme.TEXT_MUTED,
                           font_size=dp(theme.FONT_CAPTION), bold=True,
                           size_hint_y=None, height=dp(16), halign="left", valign="middle")
        list_label.bind(size=list_label.setter("text_size"))
        self.add_widget(list_label)

        scroll = ScrollView(do_scroll_x=False)
        self.record_list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self.record_list.bind(minimum_height=self.record_list.setter("height"))
        scroll.add_widget(self.record_list)
        self.add_widget(scroll)

    # ---------- actions ----------

    def _shift_date(self, delta):
        self._view_date = self._view_date + timedelta(days=delta)
        self._date_label.text = self._view_date.isoformat()
        self._input_refs["date"].text = self._view_date.isoformat()
        self._refresh_list()

    def _goto_today(self):
        self._view_date = date.today()
        self._date_label.text = self._view_date.isoformat()
        self._input_refs["date"].text = self._view_date.isoformat()
        self._refresh_list()

    def _save(self):
        try:
            db.add_body(
                weight=self._to_float("weight"),
                body_fat=self._to_float("body_fat"),
                chest=self._to_float("chest"),
                waist=self._to_float("waist"),
                arm=self._to_float("arm"),
                record_date=self._input_refs["date"].text.strip() or self._view_date.isoformat(),
                notes=self._input_refs["notes"].text.strip(),
            )
            for key in ("weight", "body_fat", "chest", "waist", "arm"):
                self._input_refs[key].text = ""
            self._refresh_list()
            self.main_layout.refresh_heatmap()
        except (ValueError, Exception) as e:
            self._show_error(str(e))

    def _to_float(self, key):
        text = self._input_refs[key].text.strip()
        return float(text) if text else None

    def _refresh_list(self):
        self.record_list.clear_widgets()
        target = self._view_date.isoformat()
        for r in db.get_body_records():
            if r["record_date"] != target:
                continue
            parts = []
            if r["weight"]: parts.append(f"{r['weight']}kg")
            if r["body_fat"]: parts.append(f"体脂{r['body_fat']}%")
            if r["chest"]: parts.append(f"胸{r['chest']}cm")
            if r["waist"]: parts.append(f"腰{r['waist']}cm")
            if r["arm"]: parts.append(f"臂{r['arm']}cm")
            self.record_list.add_widget(
                self._make_record_row("  ".join(parts), r["id"]))

    def _make_record_row(self, text, record_id):
        row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8),
                        padding=[dp(12), 0])
        with row.canvas.before:
            Color(*theme.PANEL)
            bg = Rectangle(pos=row.pos, size=row.size)
            Color(*theme.BORDER)
            border = Line(rectangle=(row.x, row.y, row.width, row.height), width=dp(1))
        row._bg_rect = bg
        row._border_line = border
        row.bind(pos=self._redraw_row, size=self._redraw_row)
        lbl = Label(text=text, font_size=dp(theme.FONT_LABEL),
                    color=theme.TEXT_PRIMARY, size_hint_x=1,
                    halign="left", valign="middle")
        lbl.bind(size=lbl.setter("text_size"))
        row.add_widget(lbl)
        del_btn = Button(text="×", size_hint=(None, None), size=(dp(28), dp(28)),
                         background_normal="", background_color=(0, 0, 0, 0),
                         color=theme.DANGER, font_size=dp(16), bold=True)
        del_btn.bind(on_release=lambda _, rid=record_id: self._delete(rid))
        sounds.bind_feedback(del_btn, text_color=theme.DANGER)
        row.add_widget(del_btn)
        return row

    @staticmethod
    def _redraw_row(row, *_):
        if hasattr(row, "_bg_rect"):
            row._bg_rect.pos = row.pos
            row._bg_rect.size = row.size
        if hasattr(row, "_border_line"):
            row._border_line.rectangle = (row.x, row.y, row.width, row.height)

    def _delete(self, rid):
        db.delete_body(rid)
        self._refresh_list()
        self.main_layout.refresh_heatmap()

    def _show_error(self, msg):
        from kivy.uix.popup import Popup
        popup = Popup(title="错误", title_color=theme.TEXT_PRIMARY,
                      content=Label(text=msg, color=theme.TEXT_PRIMARY),
                      size_hint=(0.6, 0.25), background_color=theme.PANEL)
        popup.open()
