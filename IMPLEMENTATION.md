# Fitness Tracker App — 完整实现文档

## 1. 技术栈与版本

| 组件 | 推荐版本 | 说明 |
|------|---------|------|
| Python | 3.10 或 3.12 | 不要用 3.14，Kivy 无预编译包 |
| Kivy | 2.1.0 或 2.3.1 | 2.1.0 打包最稳定 |
| p4a (python-for-android) | v2023.09.16 | 匹配 Kivy 2.1.0 |
| NDK | 23c (r23c) | 必须用 r23c |
| Android API | 31 | |
| 数据库 | SQLite (Python 内置) | 无额外依赖 |
| 其他 PyPI 包 | 无 | 仅 Kivy |

## 2. 项目文件结构

```
fitness-app/
├── main.py                  # App 入口
├── main_layout.py           # 主布局 + 屏幕管理 + 页面切换栏
├── theme.py                 # 从 config.theme 重导出
├── database.py              # 从 models 重导出所有数据库函数
├── sounds.py                # 音效 + bind_feedback 工具
├── sidebar.py               # 左侧抽屉菜单
├── topbar.py                # 顶部标题栏 + 汉堡按钮
├── buildozer.spec            # Android 打包配置
│
├── config/
│   ├── __init__.py
│   ├── constants.py         # 所有常量：预设、MET值、颜色映射、模板、鼓励语
│   └── theme.py             # 颜色主题（暗黑兰博基尼风格）
│
├── models/
│   ├── __init__.py          # 重导出
│   ├── database.py          # get_db, init_db (建表 + 种子数据)
│   ├── strength_model.py    # 力量训练 CRUD
│   ├── cardio_model.py      # 有氧训练 CRUD
│   ├── body_model.py        # 身体数据 CRUD
│   ├── plan_model.py        # 每日训练计划 CRUD
│   ├── template_model.py    # 训练模板 CRUD
│   ├── calendar_model.py    # 日历视图数据查询
│   ├── metrics_model.py     # 体重记录 + 卡路里计算
│   ├── nuke_model.py        # 核爆标记 CRUD
│   └── exercise_model.py    # 自定义动作 CRUD
│
├── panels/
│   ├── __init__.py          # 重导出
│   ├── base.py              # FormPanel 基类（日期导航、表单、记录列表）
│   ├── preset_grid.py       # PresetGrid — 2列动作按钮网格 + 长按编辑
│   ├── strength.py          # 力量训练面板
│   ├── cardio.py            # 有氧训练面板
│   ├── body.py              # 身体数据面板
│   └── stats.py             # 统计面板 + ChartWidget 柱状图
│
├── widgets/
│   ├── calendar_widget.py   # 日历热力图（月视图，滑动切换月份，颜色标签）
│   ├── plan_popup.py        # 训练计划选择弹窗（模板选择 + 自定义动作 + 滚轮调节）
│   ├── task_card.py         # 今日任务卡片（显示计划完成进度）
│   ├── nuke_button.py       # 核爆按钮（红色圆形齿轮图标 + 辉光动画）
│   ├── nuke_effects.py      # 核爆特效（震动、闪屏、粒子爆炸）
│   └── battle_report.py     # 战斗报告弹窗（训练总结 + 鼓励语）
│
├── utils/
│   ├── __init__.py
│   ├── platform.py          # 平台路径 + 字体检测
│   └── graphics.py          # lighten, rgba_hex 工具
│
├── views/                   # 空目录（预留）
├── controllers/             # 空目录（预留）
│
├── assets/
│   ├── fonts/               # roboto_regular.ttf, symbols.ttf
│   ├── icons/               # 24个动作图标 PNG + icon.png + nuke.png
│   ├── strings/zh_cn.py     # 中文字符串
│   └── icon_map.py          # 动作名 → PNG 文件名映射
│
└── fitness.db               # SQLite 数据库文件
```

## 3. 数据库设计 (SQLite)

### 3.1 表结构

```sql
-- 力量训练记录
CREATE TABLE strength_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_name TEXT NOT NULL,
    sets INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    weight REAL NOT NULL,
    record_date DATE NOT NULL,
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 有氧训练记录
CREATE TABLE cardio_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_type TEXT NOT NULL,
    distance REAL NOT NULL,       -- 公里
    duration INTEGER NOT NULL,    -- 分钟
    record_date DATE NOT NULL,
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 身体测量记录
CREATE TABLE body_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    weight REAL,           -- kg
    body_fat REAL,         -- 百分比
    chest REAL,            -- cm
    waist REAL,            -- cm
    arm REAL,              -- cm
    record_date DATE NOT NULL,
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 核爆标记（每天一次训练完成标记）
CREATE TABLE nuke_markers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_date DATE NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 训练模板
CREATE TABLE workout_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    items TEXT NOT NULL,    -- JSON 字符串：动作列表
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 每日训练计划
CREATE TABLE daily_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_date DATE NOT NULL,
    item_type TEXT NOT NULL,     -- 'strength' | 'cardio'
    exercise_name TEXT NOT NULL,
    target_sets INTEGER,
    target_reps INTEGER,
    target_weight REAL,
    target_weight_step REAL DEFAULT 0,
    target_rep_step REAL DEFAULT 0,
    target_distance REAL,
    target_duration INTEGER,
    completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 自定义动作
CREATE TABLE custom_exercises (
    exercise_name TEXT NOT NULL,
    ex_type TEXT NOT NULL,
    PRIMARY KEY (exercise_name, ex_type)
);

-- 用户体重记录
CREATE TABLE user_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_date DATE UNIQUE,
    weight_kg REAL NOT NULL
);
```

### 3.2 种子数据

首次运行时，`init_db()` 自动插入 6 个默认训练模板：

- **推A**：杠铃平板卧推(4×5)、哑铃上斜卧推(3×8)、哑铃侧平举(3×12)、绳索三头下压(3×10)、面拉(3×15)
- **推B**：哑铃上斜卧推(4×6)、坐姿杠铃肩推(3×8)、哑铃侧平举(3×12)、窄距卧推(3×8)、面拉(3×15)
- **拉A**：杠铃划船(4×5)、高位下拉(3×8)、坐姿绳索划船(3×8)、杠铃弯举(3×10)、锤式弯举(2×10)
- **拉B**：引体向上(4×5)、单臂哑铃划船(3×8)、T杆划船(3×8)、上斜哑铃弯举(3×10)、反握弯举(2×12)
- **腿A**：杠铃深蹲(4×5)、罗马尼亚硬拉(3×8)、腿举(3×10)、坐姿腿弯举(3×12)、站姿提踵(3×12)
- **腿B**：传统硬拉(4×5)、保加利亚分腿蹲(3×8)、俯卧腿弯举(3×10)、高脚杯深蹲(3×10)、坐姿提踵(3×12)

## 4. 主题颜色系统

暗黑兰博基尼风格，所有颜色为 (R, G, B, A) 0-1 范围：

| 变量 | 值 | 用途 |
|------|-----|------|
| BG | (0, 0, 0, 1) | 主背景 |
| SURFACE | (0.125, 0.125, 0.125, 1) | 卡片/面板背景 |
| SURFACE_LIGHT | (0.094, 0.094, 0.094, 1) | 较浅面板背景 |
| GOLD | (1.0, 0.753, 0.0, 1) | 主强调色 |
| GOLD_DARK | (0.569, 0.451, 0.0, 1) | 暗强调色 |
| CYAN | (0.161, 0.671, 0.886, 1) | 有氧蓝色 |
| DANGER | (0.85, 0.20, 0.20, 1) | 删除/危险 |
| TEXT_PRIMARY | (1, 1, 1, 1) | 主文字 |
| TEXT_SECONDARY | (0.961, 0.961, 0.961, 1) | 次要文字 |
| TEXT_MUTED | (0.490, 0.490, 0.490, 1) | 弱化文字 |
| TODAY_RING | (0.192, 0.192, 0.192, 1) | 今日标记环 |

力量训练用红色/橙色系，有氧训练用蓝色系，"推"用红色系，"拉"用金色系，"腿"用紫色系。

## 5. 文件大小估计

| 文件 | 行数 | 说明 |
|------|------|------|
| main.py | ~30 | 入口 |
| main_layout.py | ~250 | 主布局 + PageBar |
| config/constants.py | ~100 | 常量、模板、映射 |
| config/theme.py | ~30 | 颜色定义 |
| models/*.py | ~430 | 10个模型文件 |
| panels/*.py | ~1400 | 6个面板文件（base/preset_grid/strength/cardio/body/stats）|
| widgets/*.py | ~1800 | 6个控件文件 |
| sounds.py | ~50 | 音效 |
| sidebar.py | ~60 | 侧边栏 |
| topbar.py | ~70 | 顶栏 |
| database.py | ~10 | 兼容重导出 |
| theme.py | ~3 | 重导出 |
| **总计** | **~3800** | |

## 6. 主界面布局 (main_layout.py)

### 6.1 整体结构

```
MainLayout (FloatLayout)
├── Sidebar (抽屉菜单, x=-220, 动画滑入)
├── ScreenManager (SlideTransition)
│   ├── Screen "home"     → TopBar + [NukeButton | WarmupWidget] + TaskCard + CalendarHeatmap
│   ├── Screen "strength" → TopBar + StrengthPanel
│   ├── Screen "cardio"   → TopBar + CardioPanel
│   ├── Screen "body"     → TopBar + BodyPanel
│   └── Screen "stats"    → TopBar + StatsPanel
└── PageBar (右侧竖条滑块, 44×200dp, y=0.08)
```

### 6.2 PageBar 实现

- 位置：右下角，pos_hint={"x": 0, "y": 0.08}
- 尺寸：44dp × 200dp
- 竖条滑道：宽 4dp，高自适应
- 滑块：18dp × 36dp，金色(GOLD)
- 交互：点击切换到下一个页面，拖拽滑动切换

### 6.3 首页 (home) 布局

```
Screen "home"
└── BoxLayout (vertical)
    ├── BoxLayout (height=80dp)
    │   ├── NukeButton (0.45 weight) → 大红色核爆按钮
    │   └── WarmupWidget (0.55 weight) → 热身动作显示
    ├── TaskCard (height=72dp) → 今日训练计划进度
    └── CalendarHeatmap (height=220dp) → 月度训练热力图
```

### 6.4 侧边栏菜单项

- 日历 (home)
- 力量训练 (strength)
- 有氧运动 (cardio)
- 身体数据 (body)
- 统计数据在 PageBar 中访问，不在侧边栏

## 7. 核爆按钮 (nuke_button.py)

### 7.1 视觉设计

- 暗色背景矩形 + 红色大圆（外圈齿轮装饰）
- 6 个三角形齿轮齿围绕外圈，间隔 60°
- 内圈（hub）位于正中，覆盖背景色形成环形效果
- 内环细线 + 中心小圆点
- 辉光层（_glow 属性）在背景和前景之间脉动

### 7.2 辉光动画

- NumericProperty `_glow` 默认值 0.15
- 动画序列：(0.03 → 0.3, duration=2.0) + (0.3 → 0.03, duration=2.0)，无限循环
- 辉光圆半径 = s × 1.6（比主圆大 60%）

### 7.3 状态切换

- `nuked_today=False`：背景 _BG_NORMAL(0.1,0.08,0.0,1)，图标色 GOLD
- `nuked_today=True`：背景 _BG_NUKED(0.06,0.05,0.02,1)，图标色 GOLD_DARK
- 初始化时从数据库读取今日是否已核爆

### 7.4 交互

- on_press：播放爆炸音效，提亮图标和背景色
- on_release：调用 _on_nuked_changed 恢复状态

## 8. 日历热力图 (calendar_widget.py)

### 8.1 布局

- FloatLayout，高度 220dp
- 使用 Python `calendar` 模块的 `monthdayscalendar()` 获取月历
- 6行×7列网格布局

### 8.2 颜色编码

| 条件 | 颜色 |
|------|------|
| 无训练记录 | SURFACE_LIGHT (暗灰) |
| 仅力量训练 | COL_STRENGTH (蓝色) |
| 仅有氧训练 | COL_CARDIO (紫色) |
| 力量+有氧 | GOLD (金色) |
| 核爆日 | 红色小圆标记替代色块 |
| 今天 | TODAY_RING 边框高亮 |

### 8.3 交互

- 左右滑动切换月份
- 点击日期弹出当天训练详情 Popup
- `on_touch_down` / `on_touch_up` 检测滑动方向

### 8.4 RoundedButton 子组件

- 自定义 Button 子类，使用 RoundedRectangle 绘制圆角背景
- 内建 click 音效反馈
- `set_color()` 方法动态改变背景色

## 9. 训练计划弹窗 (plan_popup.py)

### 9.1 打开方式

- 点击核爆按钮 → 如果今日未核爆则标记核爆 → 弹出 PlanPopup
- PlanPopup 是全屏覆盖 FloatLayout，背景半透明黑色

### 9.2 界面结构

```
PlanPopup (FloatLayout)
├── 背景遮罩 (Opacity 0.85 黑色)
└── 卡片 (0.9×0.85, SURFACE 背景, RoundedRectangle)
    ├── 标题："[b]选择训练模板[/b]" (GOLD)
    ├── ScrollView
    │   ├── 每个模板一行（RoundedRectangle 行背景, check按钮, 名称+图标, 动作预览）
    │   │   └── 每个动作一行（子行, 单独check选择, 动作名+组数×次数+重量）
    │   └── 自定义动作区（力量预设 + 有氧预设, 2列GridLayout按钮）
    ├── 已选动作列表（selected_box, 每行含 stepper 滚轮+删除按钮）
    └── 底部按钮行
        ├── "取消" → _dismiss
        └── "确认计划" → _confirm
```

### 9.3 _WheelLabel 滚轮组件

- 每个选中动作有独立滚轮调节参数（组数/次数/重量）
- 触摸上下滑动改变值
- 实时更新 selected 列表中对应项的 values
- 使用 grab/ungrab 机制防止触摸冲突

### 9.4 模板操作

- **点击模板** → 全选该模板所有动作
- **长按模板** → 弹出重命名/删除对话框
- **单独勾选/取消** → 每个动作可独立选择
- **"确认计划"** → 清空今日计划 → 逐条 add_plan_item → dismiss → 触发核爆特效

### 9.5 关键数据流

```
db.get_templates() → [{"name": "推A", "items": [...]}, ...]
用户勾选 → self._selected = [{"type":"strength","name":"杠铃平板卧推","sets":4,...}, ...]
_confirm() → db.clear_today_plan() → for item in selected: db.add_plan_item(...)
```

## 10. 任务卡片 (task_card.py)

### 10.1 显示内容

- 标题："[b]今日任务[/b]  done/total 完成"
- 副标题：动作名列表（最多显示 MAX_VISIBLE 个，超出显示 "..."）
- 高度 72dp，SURFACE 背景

### 10.2 列表交互

- ScrollView 包裹的已完成/未完成列表
- 每行显示动作名 + 目标参数 + 完成按钮
- `_complete_item(plan_id)`：标记完成
- `_quick_finish(plan_id)`：快速完成
- `_delete_item(plan_id)`：删除计划项

## 11. 热身组件 (warmup_widget.py) — 可选

- 显示 9 个热身动作列表
- 点击可开始倒计时（timer）
- 每项显示动作名 + 时长/次数

## 12. 核爆特效 (nuke_effects.py)

### 12.1 shake_widget(widget, intensity=6, duration=0.3)

- 随机水平抖动目标控件
- 使用 Clock.schedule_once 递归执行 ~10 步
- 最后一步恢复原始位置

### 12.2 flash_screen(layout)

- 全屏白色 BoxLayout，opacity 1.0
- Animation 淡出 0.25s
- 完成后 remove_widget

### 12.3 explode_particles(layout, cx, cy, count=30)

- 生成 30 个随机颜色小圆点
- 从中心位置向外扩散
- Animation 控制位置偏移
- 完成后 remove_widget

## 13. 战斗报告 (battle_report.py)

### 13.1 触发时机

- 核爆确认后 0.9 秒，Clock.schedule_once 调用

### 13.2 内容

- 标题："核 爆 完 成"（红色）或 "训练报告"
- 统计：力量 X 项、有氧 Y 项
- 消耗：共计 Z 大卡
- 鼓励语：从 ENCOURAGEMENTS 列表（20 条）随机选择一条
- 关闭按钮："继续"

## 14. 面板基类 (panels/base.py)

### 14.1 FormPanel 结构

```
FormPanel (BoxLayout, vertical, spacing=4dp)
├── 日期导航栏 (height=34dp)
│   ├── "<" Button → _shift_date(-1)
│   ├── 日期 Label (YYYY-MM-DD)
│   ├── "今天" Button → _goto_today()
│   └── 空白占位
├── 表单滚动区 (ScrollView)
│   └── form_area (BoxLayout, dynamic height)
│       ├── [子类重写 _build_form() 插入预设网格/字段]
│       ├── [日期字段 _add_date_field()]
│       ├── [备注字段 _add_notes_field()]
│       └── [保存按钮 _add_save_button()]
└── 记录列表 (ScrollView)
    └── record_list (BoxLayout, dynamic height)
        └── _make_record_row() × N
            ├── 记录文本 Label
            └── "X" 删除 Button (DANGER 红色)
```

### 14.2 关键方法

| 方法 | 功能 |
|------|------|
| `_shift_date(delta)` | 切换查看日期 ±1 天 |
| `_goto_today()` | 回到今天 |
| `_make_textinput(is_text)` | 创建标准 TextInput |
| `_add_field(label, key)` | 添加带标签的输入行 |
| `_add_date_field()` | 添加日期输入 |
| `_add_notes_field()` | 添加备注输入 |
| `_add_save_button(callback)` | 添加保存按钮 |
| `_make_record_row(text, id, on_delete)` | 创建一条记录行 |
| `_refresh_list()` | 刷新记录列表（保存滚动位置） |
| `_do_refresh_list()` | 子类重写，实际刷新逻辑 |
| `_show_error(msg)` | 弹出错误提示 |

### 14.3 左右滑动

- `on_touch_down` 记录起始位置
- `on_touch_up` 检测 dx 是否超过阈值 (60dp)，且 dx > dy × 1.3
- 向左滑 → 日期 +1，向右滑 → 日期 -1

## 15. 预设网格 (panels/preset_grid.py)

### 15.1 PresetGrid 结构

- FloatLayout，内含 2 列 GridLayout
- 每个预设动作为一个 Button，左侧有颜色条 (icon_strip)
- 使用 Unicode 符号 (Symbols 字体) 替代 PNG 图标
- "自定义" 按钮在最后（SURFACE 背景）

### 15.2 编辑模式

- **长按** (0.55s) → 进入编辑模式
- 每个按钮右上角出现 "X" 删除按钮 (DANGER 红色)
- 点击 "X" → 从列表移除 → 调用 on_delete 回调
- 点击空白区域 → 退出编辑模式
- 短按 → 退出编辑模式 + 触发 on_tap

### 15.3 自定义动作对话框

- 弹出 Popup，输入动作名称
- "确定" → add_custom_exercise → add_preset → 自动触发 on_tap

## 16. 力量/有氧面板 (panels/strength.py, panels/cardio.py)

### 16.1 共用的 _show_popup 流程

1. 点击预设动作 → 查 `get_last_strength/cardio(name)` 获取上次记录
2. 弹出 Popup (0.78 × 0.42/0.34)，预填上次数据
3. 用户修改 → 保存 → dismiss → refresh_list → refresh_heatmap
4. 保存时使用 `_view_date`（可不同于今天）

### 16.2 力量弹窗字段

- 组数 (sets)、次数 (reps)、重量 kg (weight)、备注 (notes)
- 前三项 input_filter="float"
- 调用 `db.add_strength()`

### 16.3 有氧弹窗字段

- 距离 km (distance)、时长 min (duration)、备注 (notes)
- 前两项 input_filter="float"
- 调用 `db.add_cardio()`

## 17. 身体数据面板 (panels/body.py)

### 17.1 表单字段

- 体重(kg)、体脂率(%)、胸围(cm)、腰围(cm)、臂围(cm)
- 全部 float 类型输入
- 日期字段 + 备注字段
- 保存按钮 → `db.add_body()`

### 17.2 记录列表显示

- 每行格式：日期 体重kg 体脂% 胸cm 腰cm 臂cm
- 空值字段不显示
- 可删除

## 18. 统计面板 (panels/stats.py)

### 18.1 整体结构

```
StatsPanel (BoxLayout, vertical)
├── 体重输入行 (height=34dp)
│   ├── "体重:" Label
│   ├── TextInput (56dp宽, 可编辑, 自动保存到 user_metrics)
│   └── "kg" Label
├── "今日汇总" 标题 (GOLD)
├── 汇总表格 (table_box)
│   ├── 表头: 项目 | 类型 | 热量(大卡) | 训练量
│   └── 每行: _summary_row(name, type, calories, volume_text)
├── 切换按钮行
│   ├── "本周" / "本月" / "上月" (view_mode 切换)
│   └── "热量" / "训练量" (metric_mode 切换)
├── 趋势标签 (chart_label)
└── ChartWidget (height=200dp) → 柱状图
```

### 18.2 ChartWidget 实现

- BoxLayout，绑定 pos/size 触发 _draw
- **坐标轴**：左边距 42dp，底边距 22dp，顶部边距 22dp
- **柱状条**：宽度 bar_w = max(3dp, step × 0.65)，高度比例于 value/max_val
- **颜色渐变**：根据 ratio 计算 RGB，ratio 越高越亮
- **数值标签**：柱顶显示，font_size=9dp，只在 ≤14 柱或每隔 N 柱时显示
- **X 轴标签**：周一~周日 或 1~31，font_size=8dp
- 使用 Kivy CoreLabel 渲染纹理到 canvas

### 18.3 数据聚合

- `_view_mode`：week / month / last_month
- `_metric_mode`：cal（卡路里）/ vol（训练量）
- 训练量 = sets × weight（力量）+ distance × 10（有氧）
- 遍历日期 → `db.get_date_detail(d)` → 逐条计算 → 汇总

## 19. 卡路里计算公式

### 19.1 力量训练

```python
factor = STRENGTH_CAL_FACTORS.get(exercise_name, 0.035)  # 动作特异性系数
reps = reps or 8                                          # 默认次数
weight = weight_kg if weight_kg > 0 else body_weight * 0.4
calories = sets * reps * weight * factor * (body_weight / 70.0)
```

**系数分级**：
- 大重量复合 (深蹲、硬拉、卧推、划船)：0.040–0.045
- 中等复合 (引体向上、下拉、窄距卧推)：0.035–0.038
- 孤立动作 (弯举、侧平举、三头下压)：0.024–0.028
- 小肌群 (提踵、卷腹)：0.018–0.020

### 19.2 有氧训练

```python
met = CARDIO_MET.get(exercise_type, 6.0)  # 代谢当量
calories = met * body_weight * (duration_min / 60.0)
```

**MET 值**：跑步 8.0, 骑行 6.0, 游泳 7.0, 跳绳 10.0, HIIT 12.0, 瑜伽 3.0, ...

## 20. 字体系统

### 20.1 字体文件

- `assets/fonts/roboto_regular.ttf` — 主字体，注册为 "Roboto"
- `assets/fonts/symbols.ttf` — 符号字体，注册为 "Symbols"，包含 ▲▼◆★●►◄♫♨♠♦♪♣♥

### 20.2 Android CJK 回退

`utils/platform.py` → `get_font_path()`：
- Android 平台：检测系统字体路径，优先用 NotoSansCJK-Regular.ttc / DroidSansFallback.ttf
- 桌面平台：直接用 bundled Roboto

## 21. 音效系统 (sounds.py)

- Windows：使用 `winsound.Beep(freq, duration)` 
- `play_click()`：1800Hz, 14ms 短促点击音
- `play_explosion()`：序列 Beep (90Hz/200ms, 60Hz/150ms, 250Hz/50ms, 450Hz/35ms) 模拟爆炸
- `lighten(color, factor=0.28)`：提亮颜色
- `bind_feedback(btn, bg_color, text_color)`：绑定按钮按下/释放的视觉+音效反馈

## 22. buildozer.spec 配置

```ini
[app]
title = Fitness Tracker
package.name = fitnessapp
package.domain = org.fitness
source.dir = .
source.include_exts = py,ttf,wav,atlas,png,gif
version = 1.3

icon.filename = assets/icons/icon.png
presplash.filename = assets/icons/icon.png
presplash.color = #12141A

requirements = python3,kivy==2.1.0
p4a.branch = v2023.09.16

orientation = portrait
fullscreen = 1

android.permissions = VIBRATE
android.archs = arm64-v8a
android.api = 31
android.minapi = 24
android.ndk = 23c
android.enable_androidx = True

log_level = 1

[buildozer]
log_level = 2
warn_on_root = 1
```

**关键版本说明**：
- Kivy 2.1.0 而非 2.3.1 — 2.1.0 与 p4a v2023.09.16 + NDK 23c 组合最稳定
- NDK 必须用 23c (r23c)，不能用 25b
- Python 3.10 / 3.12 均可，避免 3.14（无 Kivy wheel）
- android.api 31 足够覆盖 99% 设备

## 23. 打包流程

### 23.1 环境准备

```bash
# 创建 Python 3.10/3.12 虚拟环境
python -m venv .venv
source .venv/Scripts/activate  # Windows
pip install kivy==2.1.0 buildozer

# 安装 Java JDK 17+
# 安装 Android SDK (或让 buildozer 自动下载)
```

### 23.2 编译 APK

```bash
buildozer init                # 生成默认 spec（首次）
# 修改 buildozer.spec 为上面配置
buildozer android debug       # 构建 debug APK
buildozer android deploy run  # 部署到连接的设备
```

### 23.3 预计构建时间

- 首次：30–60 分钟（下载 NDK、SDK、编译 Kivy + 依赖）
- 后续：5–15 分钟（仅编译变更代码）

## 24. 常见打包问题

| 问题 | 原因 | 解决 |
|------|------|------|
| NDK 编译失败 | NDK 版本不匹配 | 使用 NDK 23c |
| kivy._clock missing | Cython 未编译 | 核对 Kivy 版本 + p4a 分支组合 |
| 中文字体不显示 | Android 缺少 CJK 字体 | 使用 `get_font_path()` 回退机制 |
| APK 过大 (30MB+) | 包含不需要的 .so | 限定 `android.archs = arm64-v8a` |
| pip 找不到 kivy | Python 版本太新 | 降级到 3.10–3.12 |

## 25. 完整数据流

### 25.1 应用启动

```
main.py
  → theme.py → config/theme.py (加载颜色)
  → database as db → models/__init__.py (重导出)
  → LabelBase.register("Roboto", roboto_regular.ttf)
  → LabelBase.register("Symbols", symbols.ttf)
  → db.init_db() (建表 + 种子数据)
  → FitnessApp().run()
      → MainLayout().init_ui()
          → Sidebar (抽屉菜单)
          → ScreenManager with 5 screens
              → home:    NukeButton + WarmupWidget + TaskCard + CalendarHeatmap
              → strength: StrengthPanel → PresetGrid
              → cardio:   CardioPanel → PresetGrid
              → body:     BodyPanel
              → stats:    StatsPanel → ChartWidget
          → PageBar (右侧滑块)
```

### 25.2 核爆流程

```
点击 NukeButton
  → _do_nuke()
  → if not nuked_today: db.add_nuke_marker(today)
  → nuked_today = True (触发视觉变化)
  → PlanPopup(on_confirm=callback)
      → 用户选择模板 → 勾选动作
      → _confirm()
          → db.clear_today_plan()
          → for item: db.add_plan_item(...)
          → popup.dismiss()
  → _on_plan_confirmed()
      → refresh_heatmap()
      → task_card.refresh()
      → shake_widget(sm)
      → flash_screen(self)
      → explode_particles(...)
      → 0.9s后: show_battle_report()
```

### 25.3 训练记录流程

```
点击预设动作 (如"卧推")
  → db.get_last_strength("卧推") → 获取上次数据
  → _show_popup("卧推", last)
      → 用户填写 组数/次数/重量
      → on_save()
          → db.add_strength(name, sets, reps, weight, date, notes)
          → refresh_list()
          → main_layout.refresh_heatmap()
```

## 26. 关键 API 接口总结

### models 层（database.py + 所有 model 文件）

| 函数 | 参数 | 返回 |
|------|------|------|
| `get_db()` | — | sqlite3.Connection |
| `init_db()` | — | 无，建表+种子数据 |
| `add_strength(name, sets, reps, weight, date, notes)` | 力量记录字段 | 无 |
| `get_last_strength(name)` | 动作名 | Dict 或 None |
| `get_strength_records()` | — | List[Dict] |
| `delete_strength(id)` | 记录ID | 无 |
| `add_cardio(type, dist, dur, date, notes)` | 有氧记录字段 | 无 |
| `get_last_cardio(type)` | 运动类型 | Dict 或 None |
| `get_cardio_records()` | — | List[Dict] |
| `delete_cardio(id)` | 记录ID | 无 |
| `add_body(weight, bf, chest, waist, arm, date, notes)` | 身体数据 | 无 |
| `get_body_records()` | — | List[Dict] |
| `delete_body(id)` | 记录ID | 无 |
| `clear_today_plan()` | — | 无 |
| `add_plan_item(type, name, sets, reps, weight, ...)` | 计划项字段 | 无 |
| `get_today_plan()` | — | List[Dict] |
| `complete_plan_item(id)` | 计划项ID | 无 |
| `delete_plan_item(id)` | 计划项ID | 无 |
| `add_template(name, items)` | 模板名, 动作列表 | 无 |
| `get_templates()` | — | List[Dict]（含 parsed items） |
| `update_template(id, name, items)` | 模板ID, 新名, 新列表 | 无 |
| `delete_template(id)` | 模板ID | 无 |
| `get_active_dates()` | — | Dict[str, Dict] |
| `get_date_detail(date)` | ISO日期 | (List[Dict], List[Dict]) |
| `get_date_template_name(date)` | ISO日期 | str 或 None |
| `add_nuke_marker(date)` | ISO日期 | 无 |
| `is_date_nuked(date)` | ISO日期 | bool |
| `get_nuke_dates()` | — | Set[str] |
| `get_user_weight(date?)` | ISO日期（可选） | float |
| `set_user_weight(date, weight)` | ISO日期, 体重 | 无 |
| `calc_strength_calories(name, sets, reps, weight, bw?)` | 动作参数 | float |
| `calc_cardio_calories(type, duration, bw?)` | 有氧参数 | float |
| `get_custom_exercises(type)` | "strength"\|"cardio" | List[str] |
| `add_custom_exercise(type, name)` | 类型, 动作名 | 无 |
| `delete_custom_exercise(type, name)` | 类型, 动作名 | 无 |

## 27. 待实现 / 可选增强

- 热身倒计时交互（当前仅显示静态列表）
- 训练视频/教程链接
- 云端备份（Firebase/自建 API）
- 社交分享（训练报告截图）
- 训练提醒通知
- iOS 构建（当前仅 Android）
- 数据导出 (CSV/JSON)

---

**文档版本**: 1.0
**生成日期**: 2026-06-20
**总代码行数**: ~3800 行 Python (Kivy)
**唯一依赖**: Kivy
**目标平台**: Android (ARM64) + Windows/Linux 桌面
