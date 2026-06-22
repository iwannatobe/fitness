# 核弹按钮重构设计

日期: 2026-06-04

## 目标

将 `main_layout.py` 中与核弹按钮耦合的 ~360 行代码拆分为三个独立模块，使 `main_layout.py` 仅保留编排逻辑。

## 模块边界

| 文件 | 职责 | 依赖 |
|---|---|---|
| `nuke_button.py` | NukeButton 组件：辐射图标绘制 + 呼吸发光动画 + 蜂鸣音效 | `theme.py`, `sounds.py`, `database.py` |
| `nuke_effects.py` | 纯视觉特效函数：屏幕震动、白闪、粒子爆炸 | 无数据库依赖 |
| `battle_report.py` | 战报弹窗：查询当日数据 + 构建 overlay 卡片 + dismiss | `database.py`, `theme.py` |

## 编排流程

`main_layout.py` 中的 `_do_nuke` 精简为：

```python
def _do_nuke(self, btn):
    is_first = not btn.nuked_today
    if is_first:
        db.add_nuke_marker(date.today().isoformat())
        btn.nuked_today = True
        self.refresh_heatmap()

    shake_widget(self.sm)
    flash_screen(self)
    explode_particles(self, btn.center_x, btn.center_y)
    Clock.schedule_once(lambda dt: show_battle_report(self), 0.9)
```

## 删除清单

| 删除项 | 行数 | 去向 |
|---|---|---|
| NukeButton 整个类 | ~175 | `nuke_button.py` |
| `_shake_screen` | ~15 | `nuke_effects.py` |
| `_flash_screen` | ~25 | `nuke_effects.py` |
| `_explode_particles` | ~55 | `nuke_effects.py` |
| `_show_battle_report` | ~80 | `battle_report.py` |
| `_find_nuke_btn` | ~10 | 不再需要 |

## 接口签名

```python
# nuke_button.py
class NukeButton(Button):
    nuked_today = BooleanProperty(False)

# nuke_effects.py
def shake_widget(widget): ...
def flash_screen(parent): ...
def explode_particles(parent, x, y): ...

# battle_report.py
def show_battle_report(parent, date_str=None): ...
```
