#!/usr/bin/env python3
"""
启动 Pandoc + reveal.js 演示文稿服务器
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def find_presentation_file():
    """查找演示文稿文件"""
    possible_files = [
        "physical_ai_pandoc_presentation.html",
        "physical_ai_presentation.html",
        "presentation.html"
    ]
    
    for filename in possible_files:
        if Path(filename).exists():
            return filename
    
    return None

def serve_presentation():
    """启动演示文稿服务器"""
    presentation_file = find_presentation_file()
    
    if not presentation_file:
        print("❌ 未找到演示文稿文件")
        print("请先运行以下命令之一生成演示文稿：")
        print("  ./create_pandoc_presentation.sh")
        print("  ./convert_to_revealjs.sh")
        print("  或手动运行 pandoc 命令")
        sys.exit(1)
    
    print(f"📄 找到演示文稿文件: {presentation_file}")
    
    # 尝试不同端口
    ports = [8000, 8001, 8002, 8003, 8080, 3000]
    
    for port in ports:
        try:
            with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
                url = f"http://localhost:{port}/{presentation_file}"
                print(f"\n🚀 演示文稿服务器已启动")
                print(f"📱 本地访问: {url}")
                print(f"🌐 网络访问: http://[你的IP地址]:{port}/{presentation_file}")
                print("\n🎮 演示文稿控制：")
                print("  - 箭头键: 导航幻灯片")
                print("  - F: 全屏模式")
                print("  - S: 演讲者备注")
                print("  - O: 概览模式")
                print("  - B: 黑屏模式")
                print("  - ?: 显示帮助")
                print("\n⏹️  按 Ctrl+C 停止服务器")
                
                # 在浏览器中打开
                try:
                    webbrowser.open(url)
                    print(f"✅ 已在浏览器中打开演示文稿")
                except:
                    print(f"⚠️  请手动在浏览器中打开: {url}")
                
                # 开始服务
                httpd.serve_forever()
                
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"端口 {port} 被占用，尝试下一个端口...")
                continue
            else:
                print(f"在端口 {port} 启动服务器时出错: {e}")
                continue
    
    print("❌ 无法在任何可用端口启动服务器")
    sys.exit(1)

if __name__ == "__main__":
    print("🎬 Pandoc + reveal.js 演示文稿服务器")
    print("=" * 40)
    serve_presentation()