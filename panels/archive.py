"""Exercise reference archive: browsable grid of catalog exercises with guides."""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.metrics import dp
from kivy.clock import Clock

import database as db
from config import theme
import sounds
from exercise_catalog_ui import ExerciseDetailPopup

_BODY_FILTERS = [
    ("", "全部"),
    ("common", "常用"),
    ("chest", "胸"),
    ("back", "背"),
    ("shoulders", "肩"),
    ("upper arms", "手臂"),
    ("upper legs", "腿"),
    ("lower legs", "小腿"),
    ("waist", "核心"),
]

_EQUIPMENT_LABELS = {
    "barbell": "杠铃", "dumbbell": "哑铃", "cable": "绳索",
    "body weight": "自重", "leverage machine": "器械",
    "smith machine": "史密斯", "sled machine": "腿举机", "assisted": "辅助器械",
}


class ArchiveCard(Widget):
    """Tappable exercise tile showing thumbnail + name, opens the detail popup."""

    def __init__(self, exercise, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(150), dp(150)), **kwargs)
        self._exercise = exercise
        self._pressed = False
        with self.canvas:
            self._bg_color = Color(*theme.METAL_DARK)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            self._edge_color = Color(*theme.BORDER)
            self._edge = Line(rectangle=(*self.pos, *self.size), width=dp(0.8))
        self.bind(pos=self._draw, size=self._draw)

        box = BoxLayout(orientation="vertical", padding=[dp(4), dp(4)], spacing=dp(2))
        self._box = box
        self.add_widget(box)

        thumb_path = db.resolve_media_path(exercise.get("thumbnail_path"))
        if thumb_path:
            img = Image(source=thumb_path, allow_stretch=True, keep_ratio=True,
                        size_hint_y=None, height=dp(104))
            self._img = img
            box.add_widget(img)
        else:
            self._img = None
            box.add_widget(Widget(size_hint_y=None, height=dp(104)))

        name = Label(text=exercise["name_zh"], color=theme.TEXT_PRIMARY,
                     font_size=dp(11), bold=True, halign="left", valign="middle",
                     size_hint_y=None, height=dp(18))
        name.bind(size=name.setter("text_size"))
        box.add_widget(name)

        eq = _EQUIPMENT_LABELS.get(exercise.get("equipment"), exercise.get("equipment") or "—")
        tag = Label(text=eq, color=theme.VFD_CYAN, font_size=dp(9),
                    halign="left", valign="middle", size_hint_y=None, height=dp(14))
        tag.bind(size=tag.setter("text_size"))
        box.add_widget(tag)

    def _draw(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._edge.rectangle = (*self.pos, *self.size)
        self._box.pos = self.pos
        self._box.size = self.size
        if self._pressed:
            self._bg_color.rgba = theme.PANEL_RAISED
            self._edge_color.rgba = theme.VFD_ORANGE
        else:
            self._bg_color.rgba = theme.METAL_DARK
            self._edge_color.rgba = theme.BORDER

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self._pressed = True
            self._draw()
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self._pressed = False
            self._draw()
            if self.collide_point(*touch.pos):
                sounds.play_click()
                ExerciseDetailPopup(exercise_id=self._exercise["id"]).open()
            return True
        return super().on_touch_up(touch)


class ArchivePanel(BoxLayout):
    """Full-page exercise reference library with body-part filter and search."""

    def __init__(self, main_layout, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(8),
                         padding=[dp(theme.PAGE_MARGIN)] * 4, **kwargs)
        self.main_layout = main_layout
        self._active_filter = ""
        self._search_ev = None

        header = BoxLayout(size_hint_y=None, height=dp(26))
        title = Label(text="[color=ff9d24][b]EXERCISE ARCHIVE[/b][/color]  动作资料馆",
                      markup=True, color=theme.TEXT_PRIMARY,
                      font_size=dp(theme.FONT_H3), bold=True,
                      halign="left", valign="middle", size_hint_x=1)
        title.bind(size=title.setter("text_size"))
        header.add_widget(title)
        self._count = Label(text="", color=theme.VFD_CYAN, font_size=dp(theme.FONT_CAPTION),
                            bold=True, halign="right", valign="middle",
                            size_hint_x=None, width=dp(90))
        self._count.bind(size=self._count.setter("text_size"))
        header.add_widget(self._count)
        self.add_widget(header)

        search_row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
        inp = TextInput(text="", hint_text="搜索动作 / 器材 / 目标肌群", multiline=False,
                        font_size=dp(theme.FONT_BODY),
                        background_normal="", background_active="",
                        background_color=theme.DISPLAY_GLASS,
                        foreground_color=theme.TEXT_PRIMARY,
                        hint_text_color=theme.TEXT_MUTED,
                        cursor_color=theme.VFD_CYAN, padding=(dp(10), dp(8)))
        inp.bind(text=self._on_search_text)
        self._search = inp
        search_row.add_widget(inp)
        self.add_widget(search_row)

        filter_bar = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(4))
        self._filter_btns = {}
        for value, label in _BODY_FILTERS:
            btn = self._make_filter_btn(label, value)
            self._filter_btns[value] = btn
            filter_bar.add_widget(btn)
        self.add_widget(filter_bar)

        scroll = ScrollView(do_scroll_x=False)
        self._scroll = scroll
        grid = GridLayout(cols=2, spacing=dp(8), size_hint=(None, None), padding=[dp(2), dp(2)])
        self._grid = grid
        grid.bind(minimum_height=grid.setter("height"))
        scroll.bind(width=self._sync_grid_width)
        scroll.add_widget(grid)
        self.add_widget(scroll)

        self._refresh()

    def _sync_grid_width(self, scroll, width):
        self._grid.width = width

    def _make_filter_btn(self, label, value):
        from kivy.uix.button import Button
        btn = Button(text=label, size_hint_x=1, height=dp(30),
                     background_normal="", background_color=theme.METAL_DARK,
                     color=theme.TEXT_SECONDARY, font_size=dp(theme.FONT_CAPTION), bold=True)
        with btn.canvas.before:
            Color(*theme.BORDER_DIM)
            btn._edge = Line(rectangle=(0, 0, 0, 0), width=dp(0.8))
        btn.bind(pos=lambda w, _: setattr(w._edge, "rectangle", (w.x, w.y, w.width, w.height)),
                 size=lambda w, _: setattr(w._edge, "rectangle", (w.x, w.y, w.width, w.height)))
        btn.bind(on_release=lambda _b, v=value: self._set_filter(v))
        return btn

    def _set_filter(self, value):
        if self._active_filter == value:
            return
        self._active_filter = value
        for v, btn in self._filter_btns.items():
            active = v == value
            btn.background_color = theme.VFD_ORANGE if active else theme.METAL_DARK
            btn.color = theme.CHASSIS if active else theme.TEXT_SECONDARY
        sounds.play_click()
        self._refresh()

    def _on_search_text(self, _instance, _text):
        if self._search_ev:
            Clock.unschedule(self._search_ev)
        self._search_ev = Clock.schedule_once(lambda _dt: self._refresh(), 0.25)

    def _refresh(self):
        query = self._search.text.strip()
        common_only = self._active_filter == "common"
        body_part = "" if common_only else self._active_filter
        rows = db.search_catalog(query=query, body_part=body_part,
                                 limit=500, common_only=common_only)
        self._count.text = f"{len(rows)} ITEMS"
        self._grid.clear_widgets()
        for ex in rows:
            self._grid.add_widget(ArchiveCard(ex))
        if not rows:
            empty = Label(text="NO ENTRIES / 无匹配动作", color=theme.TEXT_MUTED,
                          font_size=dp(theme.FONT_BODY), size_hint_y=None,
                          height=dp(160), halign="center", valign="middle")
            self._grid.add_widget(empty)
