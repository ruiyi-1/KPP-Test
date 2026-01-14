# UI元素位置参考文档

本文档记录了KPP App中首页和题目页面的UI元素位置信息，用于自动化脚本的精确点击和元素识别。

## 屏幕尺寸

- 宽度：1276px
- 高度：2848px

---

## 一、首页（Home Page）

### 1.1 页面布局结构

```
┌─────────────────────────────────────┐
│  顶部导航栏 (Y: 138-334)            │
│  [按钮1] [按钮2] [按钮3]            │
├─────────────────────────────────────┤
│  语言切换按钮 (Y: 879-1061)         │
│  [Tukar Bahasa/Change Language]     │
├─────────────────────────────────────┤
│  功能区域 (Y: 1061-1526)            │
│  [Theory Test]                      │
│  [Colour Blind Test]                │
├─────────────────────────────────────┤
│  Exercise按钮 (Y: 1526-1722)        │
│  [Exercise]                         │
├─────────────────────────────────────┤
│  Part按钮区域 (Y: 1722-2310)        │
│  [Part A]                           │
│  [Part B]                           │
│  [Part C]                           │
├─────────────────────────────────────┤
│  其他功能 (Y: 2345+)                │
│  [KEJARA System]                    │
│  [New KEJARA - Notes]               │
└─────────────────────────────────────┘
```

### 1.2 关键元素详情

#### 语言切换按钮
- **识别方式**：`content-desc="Tukar Bahasa/Change Language"` 或包含 "language"/"bahasa"/"tukar"
- **位置**：bounds=[162,879][1114,1061]
- **中心坐标**：(638, 970)
- **类型**：Button (clickable=true)
- **⚠️ 重要**：位于页面中上部，点击Part按钮时需要避免误点击

#### Exercise按钮
- **识别方式**：`content-desc="Exercise"` 或 class包含 "ImageView"
- **位置**：bounds=[14,1526][1262,1722]
- **中心坐标**：(638, 1624)
- **类型**：ImageView (clickable=true)
- **用途**：可能需要先点击展开，才能看到Part按钮

#### Part A按钮
- **识别方式**：`content-desc="Part A"` (大小写不敏感)
- **位置**：bounds=[14,1722][1262,1918]
- **中心坐标**：(638, 1820)
- **尺寸**：1248×196px
- **类型**：View (clickable=true)
- **Y坐标范围**：1722-1918

#### Part B按钮
- **识别方式**：`content-desc="Part B"` (大小写不敏感)
- **位置**：bounds=[14,1918][1262,2114]
- **中心坐标**：(638, 2016)
- **尺寸**：1248×196px
- **类型**：View (clickable=true)
- **Y坐标范围**：1918-2114

#### Part C按钮
- **识别方式**：`content-desc="Part C"` (大小写不敏感)
- **位置**：bounds=[14,2114][1262,2310]
- **中心坐标**：(638, 2212)
- **尺寸**：1248×196px
- **类型**：View (clickable=true)
- **Y坐标范围**：2114-2310

### 1.3 点击策略

#### 进入Part页面的步骤：
1. **检查是否在首页**
   - 查找 `content-desc` 包含 "Part A/B/C" 的元素
   - 如果找到且 Y > 1000，说明在首页

2. **展开Exercise（如果需要）**
   - 查找 `content-desc="Exercise"` 的元素
   - 如果Part按钮不可见，先点击Exercise按钮
   - 等待1-2秒让页面展开

3. **点击目标Part按钮**
   - 使用 `content-desc` 精确匹配 "Part A/B/C"
   - **关键过滤条件**：Y坐标 > 1000（避免误点击语言按钮）
   - 验证：点击后等待页面更新，检查是否进入题目页面

#### 安全点击规则：
```python
# 伪代码
def click_part_button(part_name):
    # 1. 查找Part按钮
    part_button = find_element(
        content_desc=f"Part {part_name}",
        y_min=1000,  # 避免误点击语言按钮
        clickable=True
    )
    
    # 2. 验证位置
    if part_button.center_y < 1000:
        raise Error("Part按钮位置异常，可能误识别为语言按钮")
    
    # 3. 点击
    tap(part_button.center_x, part_button.center_y)
    
    # 4. 等待并验证
    wait(3)
    verify_in_question_page()
```

---

## 二、题目页面（Question Page）

### 2.1 页面布局结构

```
┌─────────────────────────────────────┐
│  顶部导航栏 (Y: 0-334)              │
│  [Back] [19/150] [右上角按钮]        │
├─────────────────────────────────────┤
│  题目内容区域 (Y: 334-1883)         │
│  ┌───────────────────────────────┐ │
│  │ 题目文本 (ScrollView)         │ │
│  │ Y: 353-1319                   │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ 题目图片 (ImageView)          │ │
│  │ Y: 1347-1827                  │ │
│  └───────────────────────────────┘ │
├─────────────────────────────────────┤
│  选项区域 (Y: 1883-2477)            │
│  [选项A] Y: 1883-2051               │
│  [选项B] Y: 2079-2247               │
│  [选项C] Y: 2275-2443               │
├─────────────────────────────────────┤
│  底部导航 (Y: 2477-2645)            │
│  [Previous] [Next]                 │
└─────────────────────────────────────┘
```

### 2.2 关键元素详情

#### Back按钮
- **识别方式**：`content-desc="Back"`
- **位置**：bounds=[0,138][196,334]
- **中心坐标**：(98, 236)
- **类型**：Button (clickable=true)
- **用途**：返回上一页

#### 题目编号
- **识别方式**：`content-desc` 包含 "/"（如 "19/150"）
- **位置**：bounds=[252,196][487,276]
- **中心坐标**：(369, 236)
- **类型**：View
- **用途**：显示当前题目编号和总题数

#### 题目文本
- **识别方式**：
  - 位于ScrollView中
  - Y坐标：300-1500
  - 宽度 > 800px
  - `content-desc` 或 `text` 包含长文本（>50字符）
- **位置**：bounds=[42,353][1232,1319]
- **尺寸**：1190×966px
- **类型**：View (在ScrollView内)
- **内容**：包含马来文题目文本（第一行）+ 翻译文本（第二行）

#### 题目图片（ImageView）
- **识别方式**：
  - `class` 以 "ImageView" 结尾
  - 尺寸 > 100×100px
  - Y坐标：1000-2000（题目文本下方，选项上方）
- **位置**：bounds=[70,1347][1206,1827]
- **尺寸**：1136×480px
- **中心坐标**：(638, 1587)
- **类型**：ImageView
- **用途**：题目中的图片（如交通标志），用于帮助理解题目
- **⚠️ 重要**：这是题目内容的一部分，不是选项

#### 选项A
- **识别方式**：`content-desc="A"` 且 `clickable=true`
- **位置**：bounds=[42,1883][1234,2051]
- **中心坐标**：(638, 1967)
- **尺寸**：1192×168px
- **类型**：Button (clickable=true)
- **Y坐标范围**：1883-2051

#### 选项B
- **识别方式**：`content-desc="B"` 且 `clickable=true`
- **位置**：bounds=[42,2079][1234,2247]
- **中心坐标**：(638, 2163)
- **尺寸**：1192×168px
- **类型**：Button (clickable=true)
- **Y坐标范围**：2079-2247

#### 选项C
- **识别方式**：`content-desc="C"` 且 `clickable=true`
- **位置**：bounds=[42,2275][1234,2443]
- **中心坐标**：(638, 2359)
- **尺寸**：1192×168px
- **类型**：Button (clickable=true)
- **Y坐标范围**：2275-2443

#### Previous按钮
- **识别方式**：`content-desc="Previous"` 或包含 "上一"
- **位置**：bounds=[32,2477][606,2645]
- **中心坐标**：(319, 2561)
- **类型**：Button (clickable=true)
- **用途**：上一题

#### Next按钮
- **识别方式**：`content-desc="Next"` 或包含 "下一"
- **位置**：bounds=[670,2477][1244,2645]
- **中心坐标**：(957, 2561)
- **类型**：Button (clickable=true)
- **用途**：下一题

### 2.3 点击策略

#### 采集题目的步骤：
1. **验证在题目页面**
   - 查找 `content-desc="A"` 或 `content-desc="B"` 的按钮
   - 查找 `content-desc="Next"` 按钮
   - 如果都找到，说明在题目页面

2. **处理广告（如果有）**
   - 检测广告元素（Y < 500，包含 "关闭"/"Skip" 等）
   - 点击关闭按钮
   - 等待广告关闭

3. **提取题目内容**
   - 提取题目文本（Y: 300-1500，宽度 > 800）
   - 提取题目图片（ImageView，Y: 1000-2000，尺寸 > 100×100）
   - 提取选项（content-desc="A/B/C"，Y: 1800-2500）

4. **点击选项（必须）**
   - 必须点击一个选项才能继续
   - 点击后等待2秒，让颜色反馈显示
   - 颜色反馈：
     - 选错的选项：背景变红
     - 正确答案：背景变绿

5. **提取答案**
   - 重新获取UI树（点击选项后页面可能更新）
   - 通过颜色反馈识别正确答案（绿色背景的选项）

6. **点击Next按钮**
   - 查找 `content-desc="Next"` 按钮
   - 点击后等待3秒
   - 验证页面更新

#### 元素识别规则：

```python
# 伪代码：识别题目文本
def find_question_text(root):
    for elem in root.iter():
        bounds = get_bounds(elem)
        if not bounds:
            continue
        x1, y1, x2, y2 = bounds
        width = x2 - x1
        
        # 题目文本特征
        if (300 < y1 < 1500 and 
            width > 800 and 
            (len(elem.get('content-desc', '')) > 50 or 
             len(elem.get('text', '')) > 50)):
            return elem
    return None

# 伪代码：识别题目图片
def find_question_images(root):
    images = []
    for elem in root.iter():
        if not elem.get('class', '').endswith('ImageView'):
            continue
        bounds = get_bounds(elem)
        if not bounds:
            continue
        x1, y1, x2, y2 = bounds
        width = x2 - x1
        height = y2 - y1
        
        # 题目图片特征
        if (width > 100 and height > 100 and 
            1000 < y1 < 2000):  # 在题目文本下方，选项上方
            images.append(elem)
    return images

# 伪代码：识别选项
def find_options(root):
    options = []
    for elem in root.iter():
        if elem.get('clickable') != 'true':
            continue
        content_desc = elem.get('content-desc', '').strip()
        if content_desc not in ['A', 'B', 'C', 'D']:
            continue
        bounds = get_bounds(elem)
        if not bounds:
            continue
        _, y1, _, _ = bounds
        
        # 选项特征
        if 1800 < y1 < 2500:  # 在选项区域
            options.append(elem)
    
    # 按Y坐标排序
    options.sort(key=lambda e: get_bounds(e)[1])
    return options
```

---

## 三、坐标范围总结

### 3.1 Y坐标分区

| 区域 | Y坐标范围 | 说明 |
|------|----------|------|
| 顶部导航 | 0-400 | Back按钮、题目编号、右上角按钮 |
| 题目文本区 | 300-1500 | 题目文本内容（ScrollView） |
| 题目图片区 | 1000-2000 | 题目中的图片（ImageView） |
| 选项区域 | 1800-2500 | 选项A/B/C按钮 |
| 底部导航 | 2400-2700 | Previous/Next按钮 |

### 3.2 安全点击范围

- **Part按钮**：Y > 1000（避免误点击语言按钮）
- **选项按钮**：1800 < Y < 2500
- **Next按钮**：Y > 2400

---

## 四、注意事项

### 4.1 首页注意事项

1. **语言按钮误点击**
   - 语言按钮在 Y=970，Part按钮在 Y>1700
   - 点击Part按钮时，确保 Y > 1000

2. **Exercise展开**
   - 某些情况下可能需要先点击Exercise按钮
   - 点击后等待1-2秒让页面展开

3. **Part按钮识别**
   - 使用 `content-desc` 精确匹配
   - 排除包含 "language"/"bahasa"/"tukar" 的元素

### 4.2 题目页面注意事项

1. **必须点击选项**
   - 必须先点击一个选项，才能点击Next按钮
   - 点击选项后等待2秒，让颜色反馈显示

2. **题目图片 vs 选项图片**
   - 题目图片：Y坐标 1000-2000（题目内容的一部分）
   - 选项图片：Y坐标 > 1800（选项的一部分）
   - 通过Y坐标范围区分

3. **页面更新检测**
   - 点击Next后需要验证页面是否更新
   - 可以通过检查题目编号变化或UI树变化来验证

4. **广告处理**
   - 广告通常在屏幕上半部分（Y < 500）
   - 检测到广告时，查找关闭按钮并点击
   - 等待广告关闭后再继续

---

## 五、代码实现参考

### 5.1 首页进入Part

```python
def enter_part(part_name):
    # 1. 检查是否在首页
    root = get_ui_tree()
    if not is_in_home_page(root):
        return False
    
    # 2. 展开Exercise（如果需要）
    exercise = find_element(root, content_desc="Exercise")
    if exercise and need_expand(root):
        tap(exercise.center)
        wait(2)
        root = get_ui_tree()
    
    # 3. 查找Part按钮
    part_button = find_element(
        root,
        content_desc=f"Part {part_name}",
        y_min=1000,  # 避免误点击语言按钮
        clickable=True
    )
    
    if not part_button:
        return False
    
    # 4. 点击
    tap(part_button.center)
    wait(3)
    
    # 5. 验证进入题目页面
    return is_in_question_page(get_ui_tree())
```

### 5.2 题目页面采集

```python
def capture_question():
    # 1. 验证在题目页面
    root = get_ui_tree()
    if not is_in_question_page(root):
        return False
    
    # 2. 处理广告
    if has_ad(root):
        close_ad(root)
        wait_for_ad_close()
        root = get_ui_tree()
    
    # 3. 提取题目内容
    question_text = extract_question_text(root)
    question_images = find_question_images(root)  # Y: 1000-2000
    options = find_options(root)  # Y: 1800-2500
    
    # 4. 点击第一个选项
    tap(options[0].center)
    wait(2)  # 等待颜色反馈
    
    # 5. 重新获取UI树（点击后可能更新）
    root_after = get_ui_tree()
    
    # 6. 提取答案（通过颜色反馈）
    correct_answer = detect_correct_answer(root_after)
    
    # 7. 提取图片（只提取图片元素）
    extract_images(root_after, question_images)
    
    # 8. 保存数据
    save_question_data(question_text, question_images, options, correct_answer)
    
    # 9. 点击Next
    next_button = find_element(root_after, content_desc="Next")
    tap(next_button.center)
    wait(3)
    
    return True
```

---

## 六、更新日志

- **2026-01-14**: 初始版本，基于实际UI dump分析
- 屏幕尺寸：1276×2848px
- 首页Part按钮：Y坐标 1722-2310
- 题目页面选项：Y坐标 1883-2443

---

## 七、相关文件

- 标注图片：
  - `screenshots/annotated_homepage.png` - 首页标注
  - `screenshots/annotated_question_page.png` - 题目页面标注
- 分析脚本：
  - `scripts/analyze_homepage.py` - 首页分析脚本
  - `scripts/analyze_question_page.py` - 题目页面分析脚本
