# V1.2 热量统计 & 强度统计表 — 设计文档

日期: 2026-06-04

## 热量计算

### 力量训练（容量换算法）

```
热量(kcal) = 组数 × 次数 × 重量(kg) × 0.0007 × (用户体重/70)
```

### 有氧训练（MET 法）

```
热量(kcal) = MET值 × 体重(kg) × 时长(小时)
```

MET 值预设：

| 运动 | MET |
|---|---|
| 跑步 | 8.0 |
| 骑行 | 6.0 |
| 游泳 | 7.0 |
| 跳绳 | 10.0 |
| 椭圆机 | 5.0 |
| 划船机 | 6.5 |
| 快走 | 4.0 |
| HIIT | 12.0 |
| 爬楼 | 8.5 |
| 登山 | 7.0 |
| 滑雪 | 6.0 |
| 瑜伽 | 3.0 |

## 数据存储

```sql
CREATE TABLE user_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_date DATE UNIQUE,
    weight_kg REAL
);
```

热量不存库，查询时动态计算。

## 用户体重

优先取 `body_records` 最新 `weight`，无则 `user_metrics` 存入值，再无则默认 70kg。

## UI — 新增 STATS 页面

第 5 个 tab，`main_layout.py` screen 列表新增。

### 汇总表
- 每行：项目名 | 类型(力量/有氧) | 热量(kcal) | 容量
- 底部总计行
- 超出滚动

### 趋势图
- Canvas 手绘柱状图
- 下拉切换：本周/本月/上月 热量 或 容量
- X 轴 = 天，Y 轴 = kcal 或 容量值

### 体重编辑
- 点击体重数字可编辑，自动存 `user_metrics`

## 文件变更

| 文件 | 动作 |
|---|---|
| `panels/stats.py` | 新建 — 统计面板 |
| `database.py` | 新增 user_metrics 表 + CRUD |
| `main_layout.py` | 新增 stats screen |
