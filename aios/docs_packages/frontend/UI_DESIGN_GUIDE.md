# 太极OS UI 设计指南 v1.0

## 1. 设计理念

### 1.1 核心原则

**太极哲学：**
- **阴阳平衡** - 亮暗模式、动静结合、简繁适度
- **动态演化** - 实时更新、流畅过渡、渐进增强
- **万物归一** - 统一风格、一致体验、整体和谐

**设计目标：**
- **清晰** - 信息层级分明，一目了然
- **高效** - 减少点击，快速操作
- **美观** - 现代简约，赏心悦目
- **可靠** - 稳定流畅，值得信赖

---

## 2. 视觉系统

### 2.1 颜色系统

#### 主色调（Primary）

**蓝色系（主色）：**
```css
--primary-50: #e6f7ff;
--primary-100: #bae7ff;
--primary-200: #91d5ff;
--primary-300: #69c0ff;
--primary-400: #40a9ff;
--primary-500: #1890ff;  /* 主色 */
--primary-600: #096dd9;
--primary-700: #0050b3;
--primary-800: #003a8c;
--primary-900: #002766;
```

**使用场景：**
- 主按钮背景
- 链接文字
- 选中状态
- 进度条

#### 功能色（Functional）

**成功（Success）：**
```css
--success-50: #f6ffed;
--success-500: #52c41a;  /* 主色 */
--success-700: #389e0d;
```

**警告（Warning）：**
```css
--warning-50: #fffbe6;
--warning-500: #faad14;  /* 主色 */
--warning-700: #d48806;
```

**错误（Error）：**
```css
--error-50: #fff1f0;
--error-500: #f5222d;  /* 主色 */
--error-700: #cf1322;
```

**信息（Info）：**
```css
--info-50: #e6f7ff;
--info-500: #1890ff;  /* 主色 */
--info-700: #096dd9;
```

#### 中性色（Neutral）

**亮色模式：**
```css
--gray-50: #fafafa;
--gray-100: #f5f5f5;
--gray-200: #e8e8e8;
--gray-300: #d9d9d9;
--gray-400: #bfbfbf;
--gray-500: #8c8c8c;
--gray-600: #595959;
--gray-700: #434343;
--gray-800: #262626;
--gray-900: #1f1f1f;
```

**暗色模式：**
```css
--dark-bg-1: #141414;    /* 页面背景 */
--dark-bg-2: #1f1f1f;    /* 卡片背景 */
--dark-bg-3: #2a2a2a;    /* 悬停背景 */
--dark-border: #434343;  /* 边框 */
--dark-text-1: #e8e8e8;  /* 主文本 */
--dark-text-2: #a6a6a6;  /* 次文本 */
--dark-text-3: #737373;  /* 辅助文本 */
```

#### 状态色（Status）

**Agent 状态：**
```css
--status-active: #52c41a;   /* 活跃 - 绿色 */
--status-idle: #1890ff;     /* 空闲 - 蓝色 */
--status-offline: #8c8c8c;  /* 离线 - 灰色 */
--status-error: #f5222d;    /* 错误 - 红色 */
```

**任务状态：**
```css
--task-pending: #faad14;    /* 待处理 - 黄色 */
--task-running: #1890ff;    /* 执行中 - 蓝色 */
--task-completed: #52c41a;  /* 已完成 - 绿色 */
--task-failed: #f5222d;     /* 失败 - 红色 */
--task-cancelled: #8c8c8c;  /* 已取消 - 灰色 */
```

**健康度：**
```css
--health-good: #52c41a;     /* 良好 (80-100) - 绿色 */
--health-warning: #faad14;  /* 警告 (60-79) - 黄色 */
--health-critical: #f5222d; /* 危险 (<60) - 红色 */
```

---

### 2.2 字体系统

#### 字体家族

**中文：**
```css
font-family: 
  "PingFang SC",
  "Microsoft YaHei",
  "Hiragino Sans GB",
  "WenQuanYi Micro Hei",
  sans-serif;
```

**英文：**
```css
font-family:
  -apple-system,
  BlinkMacSystemFont,
  "Segoe UI",
  Roboto,
  "Helvetica Neue",
  Arial,
  sans-serif;
```

**代码：**
```css
font-family:
  "Fira Code",
  Consolas,
  Monaco,
  "Courier New",
  monospace;
```

#### 字体大小

**标题：**
```css
--font-size-h1: 32px;  /* 页面标题 */
--font-size-h2: 24px;  /* 区块标题 */
--font-size-h3: 20px;  /* 卡片标题 */
--font-size-h4: 16px;  /* 小标题 */
```

**正文：**
```css
--font-size-base: 14px;    /* 正文 */
--font-size-small: 12px;   /* 辅助文本 */
--font-size-tiny: 10px;    /* 标签 */
```

**代码：**
```css
--font-size-code: 13px;
```

#### 字重

```css
--font-weight-light: 300;
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;
```

#### 行高

```css
--line-height-tight: 1.2;   /* 标题 */
--line-height-normal: 1.5;  /* 正文 */
--line-height-loose: 1.8;   /* 段落 */
```

---

### 2.3 间距系统

#### 基础单位

```css
--spacing-unit: 8px;
```

#### 间距规范

```css
--spacing-xs: 4px;    /* 0.5x */
--spacing-sm: 8px;    /* 1x */
--spacing-md: 16px;   /* 2x */
--spacing-lg: 24px;   /* 3x */
--spacing-xl: 32px;   /* 4x */
--spacing-2xl: 48px;  /* 6x */
--spacing-3xl: 64px;  /* 8x */
```

#### 使用场景

**内边距（Padding）：**
- 按钮：8px 16px
- 卡片：16px
- 表格单元格：12px 16px
- 输入框：8px 12px

**外边距（Margin）：**
- 段落间距：16px
- 卡片间距：16px
- 区块间距：24px
- 页面边距：24px

---

### 2.4 圆角系统

```css
--radius-none: 0;
--radius-sm: 2px;    /* 标签 */
--radius-md: 4px;    /* 按钮、输入框 */
--radius-lg: 8px;    /* 卡片 */
--radius-xl: 12px;   /* 模态框 */
--radius-full: 9999px; /* 圆形 */
```

---

### 2.5 阴影系统

```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);
```

**使用场景：**
- 卡片：shadow-sm
- 悬停卡片：shadow-md
- 模态框：shadow-lg
- 下拉菜单：shadow-xl

---

## 3. 组件设计

### 3.1 按钮（Button）

#### 主按钮（Primary）

```css
.btn-primary {
  background: var(--primary-500);
  color: #ffffff;
  border: none;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: var(--primary-600);
  box-shadow: var(--shadow-md);
}

.btn-primary:active {
  background: var(--primary-700);
}

.btn-primary:disabled {
  background: var(--gray-300);
  cursor: not-allowed;
}
```

#### 次按钮（Secondary）

```css
.btn-secondary {
  background: #ffffff;
  color: var(--primary-500);
  border: 1px solid var(--primary-500);
  /* 其他样式同主按钮 */
}
```

#### 危险按钮（Danger）

```css
.btn-danger {
  background: var(--error-500);
  color: #ffffff;
  /* 其他样式同主按钮 */
}
```

#### 文字按钮（Text）

```css
.btn-text {
  background: transparent;
  color: var(--primary-500);
  border: none;
  padding: 4px 8px;
}
```

#### 尺寸变体

```css
.btn-sm { padding: 4px 12px; font-size: 12px; }
.btn-md { padding: 8px 16px; font-size: 14px; }
.btn-lg { padding: 12px 24px; font-size: 16px; }
```

---

### 3.2 卡片（Card）

```css
.card {
  background: #ffffff;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-lg);
  padding: 16px;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s;
}

.card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.card-header {
  font-size: var(--font-size-h3);
  font-weight: var(--font-weight-semibold);
  margin-bottom: 12px;
}

.card-body {
  font-size: var(--font-size-base);
  color: var(--gray-700);
}

.card-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--gray-200);
}
```

---

### 3.3 表格（Table）

```css
.table {
  width: 100%;
  border-collapse: collapse;
}

.table thead {
  background: var(--gray-50);
  border-bottom: 2px solid var(--gray-300);
}

.table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-small);
  color: var(--gray-700);
}

.table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--gray-200);
}

.table tbody tr:hover {
  background: var(--gray-50);
}

.table tbody tr:nth-child(even) {
  background: var(--gray-50);
}
```

---

### 3.4 标签（Badge）

```css
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-tiny);
  font-weight: var(--font-weight-medium);
}

.badge-success {
  background: var(--success-50);
  color: var(--success-700);
}

.badge-warning {
  background: var(--warning-50);
  color: var(--warning-700);
}

.badge-error {
  background: var(--error-50);
  color: var(--error-700);
}

.badge-info {
  background: var(--info-50);
  color: var(--info-700);
}
```

---

### 3.5 输入框（Input）

```css
.input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  transition: all 0.2s;
}

.input:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.1);
}

.input:disabled {
  background: var(--gray-100);
  cursor: not-allowed;
}

.input-error {
  border-color: var(--error-500);
}
```

---

### 3.6 进度条（Progress）

```css
.progress {
  width: 100%;
  height: 8px;
  background: var(--gray-200);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: var(--primary-500);
  transition: width 0.3s;
}

.progress-bar-success { background: var(--success-500); }
.progress-bar-warning { background: var(--warning-500); }
.progress-bar-error { background: var(--error-500); }
```

---

## 4. 布局系统

### 4.1 网格系统

```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.row {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -8px;
}

.col {
  flex: 1;
  padding: 0 8px;
}

.col-1 { flex: 0 0 8.333%; }
.col-2 { flex: 0 0 16.666%; }
.col-3 { flex: 0 0 25%; }
.col-4 { flex: 0 0 33.333%; }
.col-6 { flex: 0 0 50%; }
.col-8 { flex: 0 0 66.666%; }
.col-12 { flex: 0 0 100%; }
```

### 4.2 页面布局

```css
.layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 240px;
  background: var(--gray-900);
  color: #ffffff;
}

.main {
  flex: 1;
  background: var(--gray-50);
  padding: 24px;
}

.header {
  height: 64px;
  background: #ffffff;
  border-bottom: 1px solid var(--gray-200);
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
```

---

## 5. 动画系统

### 5.1 过渡动画

```css
/* 通用过渡 */
.transition {
  transition: all 0.2s ease-in-out;
}

/* 淡入淡出 */
.fade-enter {
  opacity: 0;
}
.fade-enter-active {
  opacity: 1;
  transition: opacity 0.3s;
}
.fade-exit {
  opacity: 1;
}
.fade-exit-active {
  opacity: 0;
  transition: opacity 0.3s;
}

/* 滑入滑出 */
.slide-enter {
  transform: translateY(-20px);
  opacity: 0;
}
.slide-enter-active {
  transform: translateY(0);
  opacity: 1;
  transition: all 0.3s;
}
```

### 5.2 加载动画

```css
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--gray-200);
  border-top-color: var(--primary-500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
```

---

## 6. 图标系统

### 6.1 图标库

推荐使用：
- **Lucide Icons** - 现代、简洁
- **Heroicons** - 精美、一致
- **Feather Icons** - 轻量、优雅

### 6.2 图标尺寸

```css
.icon-sm { width: 16px; height: 16px; }
.icon-md { width: 20px; height: 20px; }
.icon-lg { width: 24px; height: 24px; }
.icon-xl { width: 32px; height: 32px; }
```

### 6.3 状态图标

- ✓ 成功 - 绿色对勾
- ✗ 失败 - 红色叉号
- ⚠ 警告 - 黄色感叹号
- ℹ 信息 - 蓝色圆圈 i
- ▶ 运行 - 蓝色播放
- ⏸ 暂停 - 灰色暂停
- ⚡ 改进 - 黄色闪电

---

## 7. 响应式设计

### 7.1 断点

```css
/* 移动端 */
@media (max-width: 767px) { }

/* 平板 */
@media (min-width: 768px) and (max-width: 1023px) { }

/* 桌面端 */
@media (min-width: 1024px) { }

/* 大屏 */
@media (min-width: 1440px) { }
```

### 7.2 响应式策略

- 桌面端优先（Desktop First）
- 关键内容优先显示
- 触摸友好（移动端）
- 适配不同屏幕密度

---

## 8. 暗色模式

### 8.1 切换实现

```css
:root {
  --bg-primary: #ffffff;
  --text-primary: #262626;
}

[data-theme="dark"] {
  --bg-primary: #141414;
  --text-primary: #e8e8e8;
}
```

### 8.2 暗色模式调整

- 降低对比度（避免刺眼）
- 调整阴影（更柔和）
- 保持功能色（成功/警告/错误）
- 图表配色适配

---

## 9. 可访问性

### 9.1 颜色对比度

- 正文文字：至少 4.5:1
- 大号文字：至少 3:1
- 图标和图形：至少 3:1

### 9.2 键盘导航

- 所有交互元素可通过 Tab 访问
- 焦点状态清晰可见
- 支持快捷键

### 9.3 屏幕阅读器

- 语义化 HTML
- ARIA 标签
- 图片 alt 文本

---

## 10. 设计资源

### 10.1 Figma 文件

（待创建）

### 10.2 设计规范文档

本文档

### 10.3 组件库

（待开发）

---

**维护者：** 小九 + 珊瑚海  
**最后更新：** 2026-03-10
