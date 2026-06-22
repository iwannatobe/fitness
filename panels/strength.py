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

STRENGTH_PRESETS = [
    "卧推", "深蹲", "硬拉", "引体向上",
    "杠铃划船", "推举", "哑铃弯举", "臂屈伸",
    "俯卧撑", "卷腹", "腿举", "飞鸟",
    "杠铃平板卧推", "哑铃上斜卧推", "哑铃侧平举",
    "绳索三头下压", "面拉", "坐姿杠铃肩推", "窄距卧推",
    "高位下拉", "坐姿绳索划船", "杠铃弯举", "锤式弯举",
    "单臂哑铃划船", "T杆划船", "上斜哑铃弯举", "反握弯举",
    "杠铃深蹲", "罗马尼亚硬拉", "坐姿腿弯举", "站姿提踵",
    "传统硬拉", "保加利亚分腿蹲", "俯卧腿弯举", "高脚杯深蹲", "坐姿提踵",
]

class StrengthPanel(FormPanel):
    def _build_form(self):
        presets = list(STRENGTH_PRESETS)
        for name in db.get_custom_exercises("strength"):
            if name not in presets: presets.append(name)
        self._preset_grid = PresetGrid(presets, on_tap=self._on_preset,
                                       on_custom=self._on_custom,
                                       on_delete=lambda name: self._on_delete_preset(name, "strength"),
                                       size_hint_y=None)
        self.form_area.add_widget(self._preset_grid)

    def _on_delete_preset(self, name, ex_type):
        db.delete_custom_exercise(ex_type, name)

    def _on_preset(self, name):
        last = db.get_last_strength(name)
        self._show_popup(name, last)

    def _on_custom(self):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(16))
        inp = TextInput(text="", multiline=False, font_size=dp(theme.FONT_BODY),
                        background_normal="", background_active="",
                        background_color=theme.SURFACE_HIGH, foreground_color=theme.TEXT_PRIMARY,
                        cursor_color=theme.GOLD, padding=(dp(10), dp(10)))
        content.add_widget(Label(text="输入动作名称", color=theme.TEXT_SECONDARY, font_size=dp(theme.FONT_BODY)))
        content.add_widget(inp)
        def on_ok(_):
            name = inp.text.strip()
            if name:
                popup.dismiss()
                db.add_custom_exercise("strength", name)
                self._preset_grid.add_preset(name)
                self._on_preset(name)
        ok_btn = Button(text="确定", size_hint_y=None, height=dp(44),
                        background_normal="", background_color=theme.GOLD,
                        color=(0.05, 0.05, 0.08, 1), font_size=dp(theme.FONT_H3), bold=True)
        ok_btn.bind(on_release=on_ok)
        content.add_widget(ok_btn)
        popup = Popup(title="自定义动作", title_color=theme.TEXT_PRIMARY,
                      content=content, size_hint=(0.75, 0.32), background_color=theme.SURFACE)
        popup.open()

    def _show_popup(self, name, last):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(16))
        fields = {}
        for label, key, default in [
            ("组数", "sets", str(last["sets"]) if last else ""),
            ("次数", "reps", str(last["reps"]) if last else ""),
            ("重量 (kg)", "weight", str(last["weight"]) if last else ""),
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
                            background_color=theme.SURFACE_HIGH,
                            foreground_color=theme.TEXT_PRIMARY,
                            cursor_color=theme.GOLD, padding=(dp(10), dp(10)))
            fields[key] = inp
            row.add_widget(inp)
            content.add_widget(row)
        save_btn = Button(text="保存", size_hint_y=None, height=dp(44),
                          background_normal="", background_color=theme.GOLD,
                          color=(0.05, 0.05, 0.08, 1), font_size=dp(theme.FONT_H3), bold=True)
        popup_ref = []
        saved_scroll_y = self.form_scroll.scroll_y
        def on_save(_):
            try:
                db.add_strength(exercise_name=name,
                                sets=int(float(fields["sets"].text or 0)),
                                reps=int(float(fields["reps"].text or 0)),
                                weight=float(fields["weight"].text or 0),
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
                      content=content, size_hint=(0.82, 0.48),
                      background_color=theme.SURFACE, separator_color=theme.BORDER)
        popup_ref.append(popup)
        popup.open()

    def _do_refresh_list(self):
        self.record_list.clear_widgets()
        target = self._view_date.isoformat()
        for r in db.get_strength_records():
            if r["record_date"] != target: continue
            txt = f"{r['exercise_name']}  {r['sets']}x{r['reps']}  {r['weight']}kg"
            self.record_list.add_widget(self._make_record_row(txt, r["id"], self._delete))

    def _delete(self, rid):
        db.delete_strength(rid)
        self._refresh_list()
        self.main_layout.refresh_heatmap()
