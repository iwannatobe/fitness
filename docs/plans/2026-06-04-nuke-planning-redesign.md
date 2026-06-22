# 核弹按钮功能重构设计 — 作战计划系统

日期: 2026-06-04

## 设计隐喻

核弹不是庆祝，是**警示**。按下去 = 宣战，必须先部署兵力（计划），否则后果自负。

## 用户流程

```
按核弹 → 计划弹窗 → 选模板/自由搭配 → 确认部署 → 今日任务卡 → 逐个完成 → 自动写库
```

## 计划弹窗

弹窗三个区域：

| 区域 | 功能 |
|---|---|
| 模板快捷区 | 预存模板按钮，一键加载到已选区。长按编辑/删除模板 |
| 动作池 | 力量动作 + 有氧动作，按钮点选加入已选。可新增自定义动作 |
| 已选计划区 | 当前已选清单，每项设目标（力量：组数/次数/重量；有氧：距离/时长），可移除 |

## 今日任务卡

核弹确认后，主页日历上方渲染任务卡片：

- 列出当日计划项，每项带 `☐` 勾选框
- 勾选 → 直接写 `strength_records`/`cardio_records` → 项变 `☑` 灰色
- 「→」按钮 → 弹出确认框允许微调实际值后写库
- 全部完成后底部显示「🎖 全部完成」

## 数据模型

### workout_templates — 模板库

```sql
CREATE TABLE workout_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    items TEXT NOT NULL,  -- JSON 数组
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

items JSON 格式：
```json
[
  {"type": "strength", "name": "卧推", "sets": 3, "reps": 8, "weight": 60},
  {"type": "cardio",  "name": "跑步", "distance": 5, "duration": 30}
]
```

### daily_plan — 每日计划

```sql
CREATE TABLE daily_plan (
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

## 文件变更

| 文件 | 动作 | 说明 |
|---|---|---|
| `plan_popup.py` | 新建 | 计划弹窗组件 |
| `task_card.py` | 新建 | 今日任务卡组件 |
| `database.py` | 修改 | 新增模板 CRUD + daily_plan CRUD |
| `battle_report.py` | 修改 | 战报增加计划 vs 实际对比 |
| `main_layout.py` | 修改 | 核弹绑定新流程，主页加任务卡 |

## 界面草图

### 计划弹窗
```
+------------------------------------------+
| ☢  部署今日任务                          |
+------------------------------------------+
| [推胸日] [拉背日] [腿日] [+ 添加模板]      |
+------------------------------------------+
| 力量                                    |
| [卧推] [飞鸟] [双杠] [深蹲] [硬拉] ...     |
|                                         |
| 有氧                                    |
| [跑步] [骑行] [游泳] [划船] ...           |
+------------------------------------------+
| 已选：                                  |
| ☑ 卧推  3 x 8  @ 60 kg   [移除]         |
| ☐ 跑步  5km  30min       [移除]         |
+------------------------------------------+
|           [确认部署 ☢]                  |
+------------------------------------------+
```

### 今日任务卡
```
+------------------------------------------+
| ☢ 今日作战清单          2026-06-04       |
| ──────────────────────────────────────  |
| ☐ 卧推  目标 3x8 @60kg   [→ 完成]       |
| ☐ 飞鸟  目标 3x12@15kg   [→ 完成]       |
| ☐ 跑步  目标 5km/30min   [→ 完成]       |
| ──────────────────────────────────────  |
| 0/3 已完成  [🎖 全部完成]                |
+------------------------------------------+
```
