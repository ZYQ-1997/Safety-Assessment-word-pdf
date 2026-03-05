"""
为已提取的表格生成汇总Excel文件
"""
import pandas as pd
import os
from pathlib import Path
import glob

def generate_summary(output_dir):
    """生成汇总Excel文件"""
    output_path = Path(output_dir)
    
    if not output_path.exists():
        print(f"错误: 目录不存在: {output_dir}")
        return
    
    # 获取所有CSV文件
    csv_files = sorted(output_path.glob("page_*.csv"))
    
    if not csv_files:
        print("未找到CSV文件")
        return
    
    print(f"找到 {len(csv_files)} 个CSV文件")
    print("正在生成汇总文件...")
    
    all_tables_data = []
    
    for csv_file in csv_files:
        try:
            # 从文件名提取页码和表格编号
            filename = csv_file.stem  # 例如: page_0003_table_01
            parts = filename.split('_')
            if len(parts) >= 4:
                page_num = int(parts[1])
                table_num = int(parts[3])
                
                # 读取CSV文件获取行数和列数
                df = pd.read_csv(csv_file, encoding='utf-8-sig')
                rows = len(df)
                columns = len(df.columns)
                
                all_tables_data.append({
                    '页码': page_num,
                    '表格编号': table_num,
                    '行数': rows,
                    '列数': columns,
                    'CSV文件名': csv_file.name
                })
        except Exception as e:
            print(f"  警告: 处理 {csv_file.name} 时出错: {str(e)}")
    
    if not all_tables_data:
        print("没有有效的表格数据")
        return
    
    # 创建汇总DataFrame
    summary_df = pd.DataFrame(all_tables_data)
    summary_df = summary_df.sort_values(['页码', '表格编号'])
    
    # 保存汇总Excel文件
    excel_path = output_path / "tables_summary.xlsx"
    
    try:
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='表格汇总', index=False)
            
            # 为前20个表格创建详细工作表
            for idx, row in summary_df.head(20).iterrows():
                try:
                    csv_path = output_path / row['CSV文件名']
                    if csv_path.exists():
                        df = pd.read_csv(csv_path, encoding='utf-8-sig')
                        sheet_name = f"P{row['页码']}_T{row['表格编号']}"
                        # Excel工作表名称限制为31个字符
                        if len(sheet_name) > 31:
                            sheet_name = sheet_name[:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                except Exception as e:
                    print(f"  警告: 无法添加表格到Excel: {str(e)}")
        
        print(f"\n汇总文件已生成: {excel_path}")
        print(f"总计: {len(all_tables_data)} 个表格")
        
    except Exception as e:
        print(f"错误: 生成Excel文件时出错: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 使用最新的输出目录
    output_dir = r"c:\Users\Z2200\Desktop\Safety Assessment\extracted_tables\tables_20251218_105313"
    generate_summary(output_dir)
