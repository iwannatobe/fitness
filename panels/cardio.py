from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp

import database as db
import theme
from panels.base import FormPanel
from panels.preset_grid import PresetGrid

CARDIO_PRESETS = ["跑步", "游泳", "骑行", "椭圆机", "跳绳", "爬楼", "快走", "HIIT", "划船机", "登山", "滑雪", "瑜伽"]

class CardioPanel(FormPanel):
    def _build_form(self):
        presets = list(CARDIO_PRESETS)
        for name in db.get_custom_exercises("cardio"):
            if name not in presets: presets.append(name)
        self._preset_grid = PresetGrid(presets, on_tap=self._on_preset,
                                       on_custom=self._on_custom,
                                       on_delete=lambda name: self._on_delete_preset(name, "cardio"),
                                       size_hint_y=None)
        self.form_area.add_widget(self._preset_grid)

    def _on_delete_preset(self, name, ex_type):
        db.delete_custom_exercise(ex_type, name)

    def _on_preset(self, name):
        last = db.get_last_cardio(name)
        self._show_popup(name, last)

    def _on_custom(self):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(16))
        inp = TextInput(text="", multiline=False, font_size=dp(theme.FONT_BODY),
                        background_normal="", background_active="",
                        background_color=theme.DISPLAY_GLASS, foreground_color=theme.TEXT_PRIMARY,
                        cursor_color=theme.VFD_CYAN, padding=(dp(10), dp(10)))
        self._frame_input(inp)
        content.add_widget(Label(text="输入运动名称", color=theme.TEXT_SECONDARY, font_size=dp(theme.FONT_BODY)))
        content.add_widget(inp)
        def on_ok(_):
            name = inp.text.strip()
            if name:
                popup.dismiss()
                db.add_custom_exercise("cardio", name)
                self._preset_grid.add_preset(name)
                self._on_preset(name)
        ok_btn = Button(text="确定", size_hint_y=None, height=dp(44),
                        background_normal="", background_color=theme.VFD_ORANGE,
                        color=theme.CHASSIS, font_size=dp(theme.FONT_H3), bold=True)
        self._frame_command(ok_btn)
        ok_btn.bind(on_release=on_ok)
        content.add_widget(ok_btn)
        popup = Popup(title="自定义运动", title_color=theme.TEXT_PRIMARY,
                       content=content, size_hint=(0.75, 0.32), background_color=theme.PANEL)
        popup.open()

    def _show_popup(self, name, last):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(16))
        fields = {}
        for label, key, default in [
            ("距离 (km)", "distance", str(last["distance"]) if last else ""),
            ("时长 (min)", "duration", str(last["duration"]) if last else ""),
            ("备注", "notes", last["notes"] if last else ""),
        ]:
            row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
            lbl = Label(text=label, size_hint_x=0.28, font_size=dp(theme.FONT_BODY),
                        color=theme.TEXT_SECONDARY, halign="right", valign="middle")
            lbl.bind(size=lbl.setter("text_size"))
            row.add_widget(lbl)
            inp = TextInput(text=default, multiline=False, font_size=dp(theme.FONT_BODY),
                            input_filter=None if key == "notes" else "float",
                            background_normal="", background_active="",
                             background_color=theme.DISPLAY_GLASS, foreground_color=theme.TEXT_PRIMARY,
                             cursor_color=theme.VFD_CYAN, padding=(dp(10), dp(10)))
            self._frame_input(inp)
            fields[key] = inp
            row.add_widget(inp)
            content.add_widget(row)
        save_btn = Button(text="保存", size_hint_y=None, height=dp(44),
                           background_normal="", background_color=theme.VFD_ORANGE,
                           color=theme.CHASSIS, font_size=dp(theme.FONT_H3), bold=True)
        self._frame_command(save_btn)
        popup_ref = []
        saved_scroll_y = self.form_scroll.scroll_y
        def on_save(_):
            try:
                db.add_cardio(exercise_type=name,
                              distance=float(fields["distance"].text or 0),
                              duration=int(float(fields["duration"].text or 0)),
                              record_date=self._view_date.isoformat(),
                              notes=fields["notes"].text.strip())
                if popup_ref: popup_ref[0].dismiss()
                self._refresh_list()
                self.main_layout.refresh_heatmap()
                Clock.schedule_once(lambda dt: setattr(self.form_scroll, 'scroll_y', saved_scroll_y), 0.05)
            except (ValueError, Exception) as e:
                self._show_error(str(e))
        save_btn.bind(on_release=on_save)
        content.add_widget(save_btn)
        popup = Popup(title=name, title_color=theme.TEXT_PRIMARY,
                      content=content, size_hint=(0.82, 0.40),
                       background_color=theme.PANEL, separator_color=theme.BORDER)
        popup_ref.append(popup)
        popup.open()

    def _do_refresh_list(self):
        self.record_list.clear_widgets()
        target = self._view_date.isoformat()
        for r in db.get_cardio_records():
            if r["record_date"] != target: continue
            txt = f"{r['exercise_type']}  {r['distance']}km  {r['duration']}min"
            self.record_list.add_widget(self._make_record_row(txt, r["id"], self._delete))
        self._refresh_presets()

    def _refresh_presets(self):
        if hasattr(self, "_preset_grid") and self._preset_grid.parent:
            self._preset_grid.parent.remove_widget(self._preset_grid)
        presets = list(CARDIO_PRESETS)
        for name in db.get_custom_exercises("cardio"):
            if name not in presets:
                presets.append(name)
        self._preset_grid = PresetGrid(presets, on_tap=self._on_preset,
                                        on_custom=self._on_custom,
                                        on_delete=lambda name: self._on_delete_preset(name, "cardio"),
                                        size_hint_y=None)
        self.form_area.add_widget(self._preset_grid, index=0)

    def _delete(self, rid):
        db.delete_cardio(rid)
        self._refresh_list()
        self.main_layout.refresh_heatmap()
