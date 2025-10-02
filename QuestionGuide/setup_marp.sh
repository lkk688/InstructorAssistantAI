#!/bin/bash

# Singapore Math条形图课件渲染设置脚本
# 此脚本将安装必要的依赖并提供渲染示例

echo "🎯 Singapore Math条形图课件渲染设置"
echo "======================================"

# 检查Node.js是否已安装
if ! command -v node &> /dev/null; then
    echo "📦 安装Node.js..."
    # 对于Ubuntu/Debian系统
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y nodejs npm
    # 对于CentOS/RHEL系统  
    elif command -v yum &> /dev/null; then
        sudo yum install -y nodejs npm
    # 对于macOS系统
    elif command -v brew &> /dev/null; then
        brew install node
    else
        echo "❌ 请手动安装Node.js: https://nodejs.org/"
        exit 1
    fi
else
    echo "✅ Node.js已安装: $(node --version)"
fi

# 安装Marp CLI
echo "📦 安装Marp CLI..."
npm install -g @marp-team/marp-cli

# 验证安装
if command -v marp &> /dev/null; then
    echo "✅ Marp CLI安装成功: $(marp --version)"
else
    echo "❌ Marp CLI安装失败"
    exit 1
fi

echo ""
echo "🚀 使用示例:"
echo "============"
echo ""
echo "1. 生成包含条形图的课件:"
echo "   python questionguide.py math_problems.docx --output-dir ../output"
echo ""
echo "2. 渲染为PDF:"
echo "   marp ../output/problem_01/slides.md --pdf --output ../output/problem_01/slides.pdf"
echo ""
echo "3. 渲染为HTML:"
echo "   marp ../output/problem_01/slides.md --html --output ../output/problem_01/slides.html"
echo ""
echo "4. 批量渲染所有问题:"
echo "   for dir in ../output/problem_*/; do"
echo "     if [ -f \"\$dir/slides.md\" ]; then"
echo "       marp \"\$dir/slides.md\" --pdf --output \"\$dir/slides.pdf\""
echo "       marp \"\$dir/slides.md\" --html --output \"\$dir/slides.html\""
echo "       echo \"Rendered: \$dir\""
echo "     fi"
echo "   done"
echo ""
echo "✨ 现在可以使用Singapore Math条形图功能了！"

# 测试渲染功能
if [ -f "test_slides.md" ]; then
    echo ""
    echo "🧪 测试渲染功能..."
    marp test_slides.md --html --output test_slides.html
    if [ -f "test_slides.html" ]; then
        echo "✅ 测试渲染成功！查看 test_slides.html"
    else
        echo "❌ 测试渲染失败"
    fi
fi