import random
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.metrics import dp
import theme
import database as db
import sounds
from config.constants import ENCOURAGEMENTS
from datetime import date

def show_battle_report(layout):
    today = date.today().isoformat()
    s_rows, c_rows = db.get_date_detail(today)
    bw = db.get_user_weight()
    total_cal = 0
    for r in s_rows:
        total_cal += db.calc_strength_calories(r["exercise_name"], r["sets"], r["reps"], r["weight"], bw)
    for r in c_rows:
        total_cal += db.calc_cardio_calories(r["exercise_type"], r["duration"], bw)
    msg = random.choice(ENCOURAGEMENTS)
    nuked = db.is_date_nuked(today)
    lines = ["[color=#ff5555][b]核 爆 完 成[/b][/color]" if nuked else "[b]训练报告[/b]"]
    if len(s_rows): lines.append(f"力量: {len(s_rows)} 项")
    if len(c_rows): lines.append(f"有氧: {len(c_rows)} 项")
    lines.append(f"消耗: {total_cal:.0f} 大卡")
    lines.append(""); lines.append(msg)
    content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(16))
    content.add_widget(Label(text="\n".join(lines), markup=True, color=theme.TEXT_PRIMARY, font_size=dp(13), halign="center", valign="middle"))
    close_btn = Button(text="继续", size_hint_y=None, height=dp(42), background_color=theme.ACCENT, color=(0.05,0.05,0.08,1), font_size=dp(14), bold=True)
    popup = Popup(title="", content=content, size_hint=(0.82, 0.55), background_color=theme.SURFACE, separator_color=(0,0,0,0), title_color=theme.TEXT_PRIMARY)
    close_btn.bind(on_release=popup.dismiss)
    content.add_widget(close_btn)
    sounds.play_explosion()
    popup.open()
