"""
直接处理PDF文件的脚本
"""
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import extract_specific_content_from_pdf, save_content_to_excel
from datetime import datetime

def main():
    pdf_path = r"c:\Users\Z2200\Desktop\Safety Assessment\safety-assessment.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"错误: 文件不存在: {pdf_path}")
        return
    
    print("=" * 60)
    print("开始处理PDF文件")
    print("=" * 60)
    print(f"文件路径: {pdf_path}")
    print(f"文件大小: {os.path.getsize(pdf_path) / 1024 / 1024:.2f} MB")
    print("=" * 60)
    
    try:
        # 提取内容
        print("\n正在提取表格内容...")
        content_results = extract_specific_content_from_pdf(pdf_path)
        
        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"extracted_content_{timestamp}.xlsx"
        output_path = os.path.join("backend", "outputs", output_filename)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print(f"\n正在保存结果到: {output_path}")
        stats = save_content_to_excel(content_results, output_path)
        
        print("\n" + "=" * 60)
        print("处理完成！")
        print("=" * 60)
        print(f"找到章节: {stats['found_sections']}/{stats['total_sections']}")
        print(f"提取表格: {stats['total_tables']} 个")
        print(f"输出文件: {output_path}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
