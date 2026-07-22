import random
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, Line
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
    lines = ["[color=#ff4b3e][b]MISSION COMPLETE / 核爆完成[/b][/color]" if nuked else
             "[color=#ff9d24][b]SESSION REPORT / 训练报告[/b][/color]"]
    if len(s_rows): lines.append(f"STRENGTH  {len(s_rows):02d} / 力量项目")
    if len(c_rows): lines.append(f"CARDIO    {len(c_rows):02d} / 有氧项目")
    lines.append(f"OUTPUT    {total_cal:.0f} KCAL / 训练消耗")
    lines.append(""); lines.append("[color=#ff5d5d][b]RECOVERY NOTICE[/b][/color]")
    lines.append(msg)
    content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(16))
    with content.canvas.before:
        Color(*theme.CHASSIS)
        report_bg = Rectangle(pos=content.pos, size=content.size)
        Color(*theme.METAL_LIGHT)
        report_border = Line(rectangle=(content.x, content.y, content.width, content.height), width=dp(1))
    content.bind(
        pos=lambda _, p: (setattr(report_bg, "pos", p),
                          setattr(report_border, "rectangle", (p[0], p[1], content.width, content.height))),
        size=lambda _, s: (setattr(report_bg, "size", s),
                           setattr(report_border, "rectangle", (content.x, content.y, s[0], s[1]))),
    )
    report = Label(text="\n".join(lines), markup=True, color=theme.TEXT_PRIMARY,
                   font_size=dp(13), halign="center", valign="middle")
    report.bind(size=report.setter("text_size"))
    content.add_widget(report)
    close_btn = Button(text="ACKNOWLEDGE / 继续", size_hint_y=None, height=dp(42),
                       background_normal="", background_color=theme.VFD_ORANGE,
                       color=(0.05,0.05,0.08,1), font_size=dp(13), bold=True)
    popup = Popup(title="", content=content, size_hint=(0.82, 0.55), background="",
                  background_color=(0, 0, 0, 0), separator_color=(0,0,0,0),
                  title_color=theme.TEXT_PRIMARY)
    close_btn.bind(on_release=popup.dismiss)
    content.add_widget(close_btn)
    sounds.play_explosion()
    popup.open()
