# 核弹作战计划系统 — 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 核弹按钮从打卡改为作战计划系统 — 按核弹→选计划→任务卡→逐个完成→自动写库

**Architecture:** plan_popup.py (计划弹窗) + task_card.py (任务卡) + database.py 扩展 (模板/每日计划 CRUD) + battle_report.py 增强 (计划vs实际)

**Tech Stack:** Python 3.12, Kivy 2.3.1, SQLite

---

### Task 1: 扩展 database.py — 新表 + 模板/计划 CRUD

**Files:**
- Modify: `database.py`

**Step 1: 在 `init_db` 中添加新表**

在 `nuke_markers` 建表后、三引号结束前，追加：

```sql
CREATE TABLE IF NOT EXISTS workout_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    items TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_date DATE NOT NULL,
    item_type TEXT NOT NULL,
    exercise_name TEXT NOT NULL,
    target_sets INTEGER,
    target_reps INTEGER,
    target_weight REAL,
    target_distance REAL,
    target_duration INTEGER,
    completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Step 2: 在 database.py 末尾追加模板 CRUD**（append 到文件末尾）

```python
# --- Workout Templates ---

def add_template(name, items):
    """items is a list of dicts, stored as JSON string."""
    import json
    conn = get_db()
    conn.execute(
        "INSERT INTO workout_templates (name, items) VALUES (?, ?)",
        (name, json.dumps(items, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def get_templates():
    import json
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM workout_templates ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["items"] = json.loads(d["items"])
        result.append(d)
    return result


def delete_template(template_id):
    conn = get_db()
    conn.execute("DELETE FROM workout_templates WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()


def update_template(template_id, name, items):
    import json
    conn = get_db()
    conn.execute(
        "UPDATE workout_templates SET name = ?, items = ? WHERE id = ?",
        (name, json.dumps(items, ensure_ascii=False), template_id),
    )
    conn.commit()
    conn.close()


# --- Daily Plan ---

def clear_today_plan():
    today = date.today().isoformat()
    conn = get_db()
    conn.execute("DELETE FROM daily_plan WHERE plan_date = ?", (today,))
    conn.commit()
    conn.close()


def add_plan_item(item_type, exercise_name, target_sets=None,
                  target_reps=None, target_weight=None,
                  target_distance=None, target_duration=None):
    today = date.today().isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO daily_plan (plan_date, item_type, exercise_name, "
        "target_sets, target_reps, target_weight, target_distance, target_duration) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (today, item_type, exercise_name,
         target_sets, target_reps, target_weight, target_distance, target_duration),
    )
    conn.commit()
    conn.close()


def get_today_plan():
    today = date.today().isoformat()
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM daily_plan WHERE plan_date = ? ORDER BY id ASC",
        (today,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def complete_plan_item(plan_id):
    conn = get_db()
    conn.execute(
        "UPDATE daily_plan SET completed = 1 WHERE id = ?", (plan_id,))
    conn.commit()
    conn.close()


def delete_plan_item(plan_id):
    conn = get_db()
    conn.execute("DELETE FROM daily_plan WHERE id = ?", (plan_id,))
    conn.commit()
    conn.close()
```

**Step 3: seed 三个默认模板（仅在为空时）**

在 `init_db` 末尾、`conn.close()` 之前加入：

```python
import json
existing = conn.execute("SELECT COUNT(*) FROM workout_templates").fetchone()[0]
if existing == 0:
    defaults = [
        ("推胸日", [
            {"type": "strength", "name": "卧推", "sets": 4, "reps": 8, "weight": 0},
            {"type": "strength", "name": "上斜哑铃", "sets": 3, "reps": 10, "weight": 0},
            {"type": "strength", "name": "绳索飞鸟", "sets": 3, "reps": 12, "weight": 0},
        ]),
        ("拉背日", [
            {"type": "strength", "name": "引体向上", "sets": 4, "reps": 8, "weight": 0},
            {"type": "strength", "name": "杠铃划船", "sets": 3, "reps": 10, "weight": 0},
            {"type": "strength", "name": "高位下拉", "sets": 3, "reps": 12, "weight": 0},
        ]),
        ("腿日", [
            {"type": "strength", "name": "深蹲", "sets": 4, "reps": 8, "weight": 0},
            {"type": "strength", "name": "硬拉", "sets": 3, "reps": 6, "weight": 0},
            {"type": "strength", "name": "腿举", "sets": 3, "reps": 12, "weight": 0},
        ]),
    ]
    for name, items in defaults:
        conn.execute(
            "INSERT INTO workout_templates (name, items) VALUES (?, ?)",
            (name, json.dumps(items, ensure_ascii=False)),
        )
```

**Step 4: 验证**

```bash
cd "F:/项目文件/CurserProject/pytest" && .venv312/Scripts/python -c "
import database as db
db.init_db()
t = db.get_templates()
print(f'Templates: {len(t)}')
for x in t: print(f'  {x[\"name\"]}: {len(x[\"items\"])} items')
db.add_plan_item('strength', '卧推', target_sets=3, target_reps=8, target_weight=60)
p = db.get_today_plan()
print(f'Plan items: {len(p)}')
db.complete_plan_item(p[0]['id'])
p2 = db.get_today_plan()
print(f'Completed: {p2[0][\"completed\"]}')
db.clear_today_plan()
print('OK')
"
```

Expected: 3 templates, 1 plan item created, completed=1, cleared.

**Step 5: Commit**

```bash
git add database.py
git commit -m "feat: add workout_templates + daily_plan tables and CRUD"
```

---

### Task 2: 创建 plan_popup.py — 计划弹窗

**Files:**
- Create: `plan_popup.py`

**Step 1: 创建 `plan_popup.py`**

弹窗组件 `PlanPopup`，继承 `FloatLayout`，包含：

- 模板快捷区：水平滚动按钮 `[推胸日] [拉背日] [腿日] [+添加当前为模板]`，长按编辑/删除
- 动作池：力量/有氧动作按钮网格（预设动作列表 + 自定义输入框）
- 已选区：`BoxLayout` 垂直列表，每项显示 `名称 | 组数输入 | 次数输入 | 重量输入 | [移除]`
- 力量项：sets/reps/weight 输入
- 有氧项：distance/duration 输入
- 底部 `[确认部署 ☢]` 按钮 → 调 `db.clear_today_plan()` + 逐条 `db.add_plan_item()` → 回调通知 `main_layout`

```python
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, RoundedRectangle

import theme
import database as db

# Predefined exercise lists
STRENGTH_EXERCISES = ["卧推", "上斜哑铃", "绳索飞鸟", "深蹲", "硬拉", "腿举",
                       "引体向上", "杠铃划船", "高位下拉", "推举", "弯举", "臂屈伸"]

CARDIO_EXERCISES = ["跑步", "骑行", "游泳", "划船", "跳绳", "椭圆机"]


class PlanPopup(FloatLayout):
    def __init__(self, on_confirm=None, **kwargs):
        super().__init__(size_hint=(1, 1), **kwargs)
        self._on_confirm = on_confirm
        self._selected = []  # list of item dicts
        self._build_ui()

    def _build_ui(self):
        # Semi-transparent background
        with self.canvas.before:
            Color(0, 0, 0, 0.85)
            self._bg = Rectangle(pos=(0, 0), size=(1, 1))
        self.bind(pos=lambda _, p: setattr(self._bg, 'pos', p),
                  size=lambda _, s: setattr(self._bg, 'size', s))

        # Main content card
        card = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(8),
                         size_hint=(0.9, 0.95), pos_hint={"center_x": 0.5, "center_y": 0.5})

        with card.canvas.before:
            Color(*theme.SURFACE)
            card._bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
        card.bind(pos=lambda _, p: setattr(card._bg, 'pos', p),
                  size=lambda _, s: setattr(card._bg, 'size', s))

        # Title
        card.add_widget(Label(
            text="[font=Symbols]☢[/font]  部署今日任务",
            markup=True, color=theme.GOLD, font_size=dp(18),
            size_hint_y=None, height=dp(40),
        ))

        # Template bar
        template_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        templates = db.get_templates()
        for t in templates:
            btn = Button(text=t["name"], size_hint_x=None, width=dp(80),
                         background_color=theme.SURFACE_LIGHT, color=theme.TEXT_PRIMARY)
            btn.bind(on_press=lambda _, items=t["items"]: self._load_template(items))
            template_bar.add_widget(btn)

        add_tmpl_btn = Button(text="+模板", size_hint_x=None, width=dp(70),
                              background_color=theme.GOLD_DARK, color=theme.TEXT_PRIMARY)
        add_tmpl_btn.bind(on_press=lambda _: self._save_current_as_template())
        template_bar.add_widget(add_tmpl_btn)
        card.add_widget(template_bar)

        # Exercise pool
        pool = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(160), spacing=dp(4))
        pool.add_widget(Label(text="力量训练", color=theme.STRENGTH_ORANGE,
                              font_size=dp(12), size_hint_y=None, height=dp(20)))
        strength_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4))
        for ex in STRENGTH_EXERCISES:
            btn = self._make_exercise_btn(ex, "strength")
            strength_row.add_widget(btn)
        scroll1 = ScrollView(size_hint_y=None, height=dp(50))
        scroll1.add_widget(strength_row)
        pool.add_widget(scroll1)

        pool.add_widget(Label(text="有氧运动", color=theme.CARDIO_BLUE,
                              font_size=dp(12), size_hint_y=None, height=dp(20)))
        cardio_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4))
        for ex in CARDIO_EXERCISES:
            btn = self._make_exercise_btn(ex, "cardio")
            cardio_row.add_widget(btn)
        scroll2 = ScrollView(size_hint_y=None, height=dp(50))
        scroll2.add_widget(cardio_row)
        pool.add_widget(scroll2)

        card.add_widget(pool)

        # Selected items
        card.add_widget(Label(text="已选：", color=theme.TEXT_SECONDARY,
                              font_size=dp(14), size_hint_y=None, height=dp(24)))
        self._selected_box = BoxLayout(orientation="vertical", spacing=dp(4))
        self._selected_scroll = ScrollView()
        self._selected_scroll.add_widget(self._selected_box)
        card.add_widget(self._selected_scroll)

        # Confirm button
        confirm_btn = Button(text="确认部署 ☢", size_hint_y=None, height=dp(48),
                             background_color=theme.GOLD, color=(0, 0, 0, 1))
        confirm_btn.bind(on_press=self._confirm)
        card.add_widget(confirm_btn)

        self.add_widget(card)

    def _make_exercise_btn(self, name, ex_type):
        btn = Button(text=name, size_hint_x=None, width=dp(72),
                     background_color=theme.SURFACE_LIGHT, color=theme.TEXT_PRIMARY)
        btn.bind(on_press=lambda _: self._add_to_selected(ex_type, name))
        return btn

    def _add_to_selected(self, ex_type, name):
        item = {"type": ex_type, "name": name}
        if ex_type == "strength":
            item.update({"sets": 3, "reps": 8, "weight": 0})
        else:
            item.update({"distance": 0, "duration": 0})
        self._selected.append(item)
        self._refresh_selected()

    def _load_template(self, items):
        self._selected = list(items)
        self._refresh_selected()

    def _refresh_selected(self):
        self._selected_box.clear_widgets()
        for i, item in enumerate(self._selected):
            row = self._make_selected_row(i, item)
            self._selected_box.add_widget(row)

    def _make_selected_row(self, idx, item):
        row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))

        label_text = f"{item['name']}"
        row.add_widget(Label(text=label_text, color=theme.TEXT_PRIMARY,
                             size_hint_x=0.25))

        if item["type"] == "strength":
            sets_inp = TextInput(text=str(item.get("sets", 3)),
                                 size_hint_x=0.12, multiline=False,
                                 input_filter="int", halign="center")
            sets_inp.bind(text=lambda _, v, i=idx: self._update_item(i, "sets", int(v or 0)))
            row.add_widget(sets_inp)
            row.add_widget(Label(text="x", color=theme.TEXT_MUTED, size_hint_x=0.04))

            reps_inp = TextInput(text=str(item.get("reps", 8)),
                                 size_hint_x=0.12, multiline=False,
                                 input_filter="int", halign="center")
            reps_inp.bind(text=lambda _, v, i=idx: self._update_item(i, "reps", int(v or 0)))
            row.add_widget(reps_inp)

            wgt_inp = TextInput(text=str(item.get("weight", 0)),
                                size_hint_x=0.14, multiline=False,
                                input_filter="float", halign="center")
            wgt_inp.bind(text=lambda _, v, i=idx: self._update_item(i, "weight",
                            float(v or 0)))
            row.add_widget(wgt_inp)
            row.add_widget(Label(text="kg", color=theme.TEXT_MUTED, size_hint_x=0.08))
        else:
            dist_inp = TextInput(text=str(item.get("distance", 0)),
                                 size_hint_x=0.12, multiline=False,
                                 input_filter="float", halign="center")
            dist_inp.bind(text=lambda _, v, i=idx: self._update_item(i, "distance",
                           float(v or 0)))
            row.add_widget(dist_inp)
            row.add_widget(Label(text="km", color=theme.TEXT_MUTED, size_hint_x=0.06))

            dur_inp = TextInput(text=str(item.get("duration", 0)),
                                size_hint_x=0.12, multiline=False,
                                input_filter="int", halign="center")
            dur_inp.bind(text=lambda _, v, i=idx: self._update_item(i, "duration",
                           int(v or 0)))
            row.add_widget(dur_inp)
            row.add_widget(Label(text="min", color=theme.TEXT_MUTED, size_hint_x=0.08))

        remove_btn = Button(text="X", size_hint_x=0.08,
                            background_color=theme.DANGER, color=theme.TEXT_PRIMARY)
        row.add_widget(remove_btn)
        return row

    def _update_item(self, idx, key, value):
        if idx < len(self._selected):
            self._selected[idx][key] = value

    def _confirm(self, *_):
        db.clear_today_plan()
        for item in self._selected:
            if item["type"] == "strength":
                db.add_plan_item("strength", item["name"],
                                 target_sets=item.get("sets", 3),
                                 target_reps=item.get("reps", 8),
                                 target_weight=item.get("weight", 0))
            else:
                db.add_plan_item("cardio", item["name"],
                                 target_distance=item.get("distance", 0),
                                 target_duration=item.get("duration", 0))
        if self._on_confirm:
            self._on_confirm()

    def _save_current_as_template(self):
        if not self._selected:
            return
        name = f"自定义{len(db.get_templates()) + 1}"
        db.add_template(name, self._selected)
        # dismiss popup 由父容器处理
```

**Step 2: 验证导入**

```bash
cd "F:/项目文件/CurserProject/pytest" && .venv312/Scripts/python -c "from plan_popup import PlanPopup; print('OK')"
```

Expected: Import OK.

**Step 3: Commit**

```bash
git add plan_popup.py
git commit -m "feat: add PlanPopup for workout planning"
```

---

### Task 3: 创建 task_card.py — 今日任务卡

**Files:**
- Create: `task_card.py`

**Step 1: 创建 `task_card.py`**

主页日历上方显示的今日任务卡组件：

```python
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle

import theme
import database as db


class TaskCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(6),
                         size_hint_y=None, **kwargs)
        self.bind(minimum_height=self.setter("height"))

        with self.canvas.before:
            Color(*theme.SURFACE)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=lambda _, p: setattr(self._bg, 'pos', p),
                  size=lambda _, s: setattr(self._bg, 'size', s))

        self._build()

    def _build(self):
        self.clear_widgets()
        plan = db.get_today_plan()

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(30))
        completed_count = sum(1 for p in plan if p["completed"])
        total = len(plan)
        header.add_widget(Label(
            text=f"[font=Symbols]☢[/font] 今日作战清单  {completed_count}/{total}",
            markup=True, color=theme.GOLD, font_size=dp(14),
            halign="left", valign="middle",
        ))
        self.add_widget(header)

        if not plan:
            self.add_widget(Label(
                text="暂无计划，按核弹部署", color=theme.TEXT_MUTED,
                font_size=dp(12), size_hint_y=None, height=dp(30),
            ))
            return

        for item in plan:
            row = self._make_item_row(item)
            self.add_widget(row)

    def _make_item_row(self, item):
        row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(6))

        # Checkbox / status icon
        done = item["completed"]
        check_text = "☑" if done else "☐"
        check_btn = Button(text=check_text, size_hint_x=None, width=dp(32),
                           background_color=(0, 0, 0, 0),
                           color=theme.GOLD if done else theme.TEXT_MUTED,
                           font_size=dp(18))
        if not done:
            check_btn.bind(on_press=lambda _, p=item:
                           self._complete_item(p["id"]))
        row.add_widget(check_btn)

        # Label
        if item["item_type"] == "strength":
            label_text = (f"{item['exercise_name']}  "
                          f"{item['target_sets']}x{item['target_reps']} "
                          f"@{item['target_weight']}kg")
        else:
            label_text = (f"{item['exercise_name']}  "
                          f"{item['target_distance']}km / {item['target_duration']}min")

        lbl = Label(text=label_text, color=theme.TEXT_SECONDARY if not done else theme.TEXT_MUTED,
                    font_size=dp(13), halign="left", valign="middle")
        row.add_widget(lbl)

        # Quick finish button
        if not done:
            finish_btn = Button(text="→", size_hint_x=None, width=dp(36),
                                background_color=theme.SURFACE_LIGHT,
                                color=theme.GOLD)
            finish_btn.bind(on_press=lambda _, p=item: self._quick_finish(p))
            row.add_widget(finish_btn)

        return row

    def _complete_item(self, plan_id):
        db.complete_plan_item(plan_id)
        # Write to training records
        plan = [p for p in db.get_today_plan() if p["id"] == plan_id]
        if plan:
            item = plan[0]
            from datetime import date
            today = date.today().isoformat()
            if item["item_type"] == "strength":
                db.add_strength(item["exercise_name"],
                                item["target_sets"],
                                item["target_reps"],
                                item["target_weight"],
                                today)
            else:
                db.add_cardio(item["exercise_name"],
                              item["target_distance"],
                              item["target_duration"],
                              today)
        self._build()

    def _quick_finish(self, item):
        # TODO: pop a confirm dialog allowing value adjustment
        # For now, complete directly
        self._complete_item(item["id"])

    def refresh(self):
        self._build()
```

**Step 2: 验证导入**

```bash
cd "F:/项目文件/CurserProject/pytest" && .venv312/Scripts/python -c "from task_card import TaskCard; print('OK')"
```

Expected: Import OK.

**Step 3: Commit**

```bash
git add task_card.py
git commit -m "feat: add TaskCard for daily workout tracking"
```

---

### Task 4: 修改 main_layout.py — 接入新流程

**Files:**
- Modify: `main_layout.py`

**Step 1: 添加导入**

在 `from battle_report import show_battle_report` 后加入：
```python
from plan_popup import PlanPopup
from task_card import TaskCard
```

**Step 2: 修改 `_build_home` — 在 nuke_btn 和 heatmap 之间插入 TaskCard**

将 Home screen builder 改为：
```python
def _build_home(self):
    box = BoxLayout(orientation="vertical")

    nuke_btn = NukeButton(size_hint_y=None, height=dp(100))
    nuke_btn.bind(on_release=lambda instance: self._do_nuke(instance))
    box.add_widget(nuke_btn)

    self._task_card = TaskCard()
    box.add_widget(self._task_card)

    self._heatmap = CalendarHeatmap()
    box.add_widget(self._heatmap)
    return box
```

**Step 3: 修改 `_do_nuke` — 核弹按下打开计划弹窗**

```python
def _do_nuke(self, btn):
    is_first = not btn.nuked_today
    if is_first:
        db.add_nuke_marker(date.today().isoformat())
        btn.nuked_today = True

    # Show planning popup
    popup = PlanPopup(on_confirm=lambda: self._on_plan_confirmed())
    self.add_widget(popup)
```

**Step 4: 添加 `_on_plan_confirmed`**

```python
def _on_plan_confirmed(self):
    self.refresh_heatmap()
    self._task_card.refresh()
    shake_widget(self.sm)
    flash_screen(self)
    Clock.schedule_once(lambda dt: show_battle_report(self), 0.9)
```

**Step 5: 更新 `refresh_heatmap`**

在 `refresh_heatmap` 中也刷新 task_card：
```python
def refresh_heatmap(self):
    if hasattr(self, "_heatmap"):
        self._heatmap.refresh()
    if hasattr(self, "_task_card"):
        self._task_card.refresh()
```

**Step 6: 验证完整流程**

```bash
cd "F:/项目文件/CurserProject/pytest" && .venv312/Scripts/python main.py
```

Expected: App 启动 → 按核弹 → 弹出 PlanPopup → 选动作确认 → 任务卡出现在主页 → 勾掉 → 数据写入 DB → 战报显示


**Step 7: Commit**

```bash
git add main_layout.py
git commit -m "feat: wire nuke button to planning popup + task card"
```

---

### Task 5: 更新 battle_report.py — 计划 vs 实际

**Files:**
- Modify: `battle_report.py`

**Step 1: 在战报中增加"今日计划完成情况"区块**

在现有 `show_battle_report` 函数中，数据查询后、构建 lines 前插入：

```python
plan = db.get_today_plan()
if plan:
    plan_done = sum(1 for p in plan if p["completed"])
    plan_total = len(plan)
    lines.append(f"\n[font=Symbols]☢[/font] [b]任务完成: {plan_done}/{plan_total}[/b]")
    for p in plan:
        status = "✓" if p["completed"] else "○"
        lines.append(f"  {status} {p['exercise_name']}")
```

(在 `lines` 定义后、现有力量/有氧区块前插入)

**Step 2: 验证**

启动 App，完成几个任务后按核弹查看战报。

**Step 3: Commit**

```bash
git add battle_report.py
git commit -m "feat: add plan completion status to battle report"
```
