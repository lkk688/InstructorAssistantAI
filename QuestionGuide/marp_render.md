# Marp渲染指南 - Singapore Math条形图支持

## 使用方法

1. **生成课件内容**：
   ```bash
   cd /Developer/InstructorAssistantAI/QuestionGuide
   python questionguide.py math_problems.docx --output-dir ../output
   ```

2. **使用Marp渲染为PDF**：
   ```bash
   # 安装Marp CLI (如果尚未安装)
   npm install -g @marp-team/marp-cli
   
   # 渲染为PDF
   marp ../output/problem_01/slides.md --pdf --output ../output/problem_01/slides.pdf
   
   # 渲染为HTML
   marp ../output/problem_01/slides.md --html --output ../output/problem_01/slides.html
   ```

3. **批量渲染所有问题**：
   ```bash
   # 创建批量渲染脚本
   for dir in ../output/problem_*/; do
     if [ -f "$dir/slides.md" ]; then
       marp "$dir/slides.md" --pdf --output "$dir/slides.pdf"
       marp "$dir/slides.md" --html --output "$dir/slides.html"
       echo "Rendered: $dir"
     fi
   done
   ```

## 条形图特性

### 支持的问题类型
- **加减法问题**: 显示已知量、未知量和总量的关系
- **乘除法问题**: 显示等分组和总量的关系  
- **分数/比例问题**: 显示整体和部分的关系
- **通用问题**: 显示给定信息和待求量

### 视觉元素
- 🟢 **已知量** (绿色条形)
- 🌸 **未知量** (粉色条形)  
- 🔵 **总量** (蓝色条形)
- 🟣 **分组** (紫色条形)
- 🟡 **整体** (黄色条形)

### CSS样式特点
- 响应式设计，适配不同屏幕尺寸
- 清晰的颜色编码系统
- 专业的教学演示外观
- 与Marp完全兼容

## 示例输出

生成的课件将包含以下幻灯片：
1. **学习目标** - 概述要点
2. **可视化问题解决** - Singapore Math条形图
3. **详细解答** - 步骤说明
4. **最终答案** - 突出显示结果
5. **常见错误** - 避免陷阱
6. **练习题** - 巩固学习
7. **总结** - 关键要点回顾

## 技术说明

- 使用HTML/CSS在Markdown中实现条形图
- 兼容Marp的渲染引擎
- 支持PDF和HTML输出格式
- 自动识别问题类型并生成相应的可视化