"""Mechanical-panel popup for viewing SQLite-backed exercise guidance."""

from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView

import database as db
from config import theme

_BODY_LABELS = {
    "chest": "胸", "back": "背", "upper legs": "腿", "lower legs": "小腿",
    "shoulders": "肩", "upper arms": "手臂", "waist": "核心",
}
_EQUIPMENT_LABELS = {
    "barbell": "杠铃", "dumbbell": "哑铃", "cable": "绳索",
    "body weight": "自重", "leverage machine": "器械",
    "smith machine": "史密斯", "sled machine": "腿举机", "assisted": "辅助器械",
}


class ExerciseDetailPopup(ModalView):
    def __init__(self, exercise_id=None, exercise_name=None, **kwargs):
        super().__init__(size_hint=(0.94, 0.92), **kwargs)
        self.background = ""
        self.background_color = theme.OVERLAY
        self._exercise = db.find_catalog_exercise(exercise_id, exercise_name)
        self._animation_event = None
        self._frame_index = 0
        self._build()

    def _build(self):
        ex = self._exercise
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        title = BoxLayout(size_hint_y=None, height=dp(34))
        title.add_widget(Label(
            text=f"[b]EXERCISE DATA[/b]\n{ex['name_zh']}" if ex else "动作资料不可用",
            markup=True, color=theme.GOLD, font_size=dp(theme.FONT_LABEL), halign="left", valign="middle"))
        close = Button(text="×", size_hint_x=None, width=dp(38), background_normal="",
                       background_color=(0, 0, 0, 0), color=theme.TEXT_MUTED, font_size=dp(20))
        close.bind(on_release=lambda _: self.dismiss())
        title.add_widget(close)
        root.add_widget(title)
        if not ex:
            self.add_widget(root)
            return
        frame_paths = [
            db.resolve_media_path(path) for path in ex.get("animation_frames", [])
        ]
        self._frames = [path for path in frame_paths if path]
        media = self._frames[0] if self._frames else db.resolve_media_path(ex["thumbnail_path"])
        if media:
            self._media = Image(source=media, size_hint_y=None, height=dp(180))
            root.add_widget(self._media)
            if len(self._frames) > 1:
                interval = max(0.04, float(ex.get("animation_interval") or 0.12))
                self._animation_event = Clock.schedule_interval(self._next_frame, interval)
        meta = Label(
            text=(f"部位: {_BODY_LABELS.get(ex['body_part'], ex['body_part'])}    "
                  f"器械: {_EQUIPMENT_LABELS.get(ex['equipment'], ex['equipment'])}\n"
                  f"目标: {ex['target']}    协同: {', '.join(ex['secondary_muscles'])}"),
            color=theme.TEXT_SECONDARY, font_size=dp(theme.FONT_CAPTION),
            size_hint_y=None, height=dp(42), halign="left", valign="middle")
        meta.bind(size=meta.setter("text_size"))
        root.add_widget(meta)
        scroll = ScrollView(do_scroll_x=False)
        steps = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8))
        steps.bind(minimum_height=steps.setter("height"))
        for index, step in enumerate(ex["steps_zh"], 1):
            row = Label(text=f"[color=ffcc33]{index:02d}[/color]  {step}", markup=True,
                        color=theme.TEXT_PRIMARY, font_size=dp(theme.FONT_BODY),
                        size_hint_y=None, halign="left", valign="top")
            row.bind(width=lambda widget, width: setattr(widget, "text_size", (width, None)))
            row.bind(texture_size=lambda widget, size: setattr(widget, "height", max(dp(28), size[1] + dp(6))))
            steps.add_widget(row)
        scroll.add_widget(steps)
        root.add_widget(scroll)
        attribution = Label(text=ex["attribution"], color=theme.TEXT_MUTED,
                            font_size=dp(10), size_hint_y=None, height=dp(16))
        root.add_widget(attribution)
        self.add_widget(root)

    def _next_frame(self, _dt):
        if not self._frames or not hasattr(self, "_media"):
            return False
        self._frame_index = (self._frame_index + 1) % len(self._frames)
        self._media.source = self._frames[self._frame_index]
        self._media.reload()
        return True

    def on_dismiss(self):
        if self._animation_event is not None:
            self._animation_event.cancel()
            self._animation_event = None
