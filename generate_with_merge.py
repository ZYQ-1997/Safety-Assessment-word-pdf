"""
为已提取的表格生成包含连续页码合并功能的整合Excel文件
"""
import pandas as pd
import os
from pathlib import Path

def clean_sheet_name(name):
    """清理工作表名称，确保符合Excel要求"""
    invalid_chars = ['\\', '/', '?', '*', '[', ']', ':']
    for char in invalid_chars:
        name = name.replace(char, '_')
    if len(name) > 31:
        name = name[:31]
    return name

def merge_consecutive_pages_tables(writer, all_tables_data, output_path, used_sheet_names):
    """将连续页码的表格合并为一个sheet页"""
    # 按页码分组
    pages_dict = {}
    for item in all_tables_data:
        page = item['页码']
        if page not in pages_dict:
            pages_dict[page] = []
        pages_dict[page].append(item)
    
    # 找出连续页码的组
    sorted_pages = sorted(pages_dict.keys())
    consecutive_groups = []
    current_group = [sorted_pages[0]]
    
    for i in range(1, len(sorted_pages)):
        if sorted_pages[i] == sorted_pages[i-1] + 1:
            current_group.append(sorted_pages[i])
        else:
            if len(current_group) >= 2:
                consecutive_groups.append(current_group)
            current_group = [sorted_pages[i]]
    
    if len(current_group) >= 2:
        consecutive_groups.append(current_group)
    
    merged_sheet_count = 0
    
    for group in consecutive_groups:
        try:
            group_tables = []
            for page in group:
                if page in pages_dict:
                    group_tables.extend(pages_dict[page])
            
            group_tables.sort(key=lambda x: (x['页码'], x['表格编号']))
            
            all_dfs = []
            all_columns = set()
            
            for item in group_tables:
                try:
                    csv_path = output_path / item['CSV文件名']
                    if csv_path.exists():
                        df = pd.read_csv(csv_path, encoding='utf-8-sig')
                        all_columns.update(df.columns)
                        all_dfs.append((item, df))
                except Exception as e:
                    continue
            
            if not all_dfs:
                continue
            
            all_columns = sorted(list(all_columns))
            
            merged_rows = []
            for idx, (item, df) in enumerate(all_dfs):
                if idx > 0:
                    separator_row = {col: '' for col in all_columns}
                    if len(all_columns) > 0:
                        separator_row[all_columns[0]] = f"--- 页码{item['页码']}_表格{item['表格编号']} ---"
                    merged_rows.append(separator_row)
                
                for _, row in df.iterrows():
                    row_dict = {col: row.get(col, '') if col in row else '' for col in all_columns}
                    merged_rows.append(row_dict)
            
            merged_df = pd.DataFrame(merged_rows, columns=all_columns)
            
            start_page = group[0]
            end_page = group[-1]
            if start_page == end_page:
                sheet_name = f"合并_P{start_page}"
            else:
                sheet_name = f"合并_P{start_page}-{end_page}"
            
            sheet_name = clean_sheet_name(sheet_name)
            
            original_sheet_name = sheet_name
            counter = 1
            while sheet_name in used_sheet_names:
                sheet_name = f"{original_sheet_name[:28]}_{counter}"
                counter += 1
            
            used_sheet_names.add(sheet_name)
            merged_df.to_excel(writer, sheet_name=sheet_name, index=False)
            merged_sheet_count += 1
            
        except Exception as e:
            print(f"    警告: 合并页码组 {group} 时出错: {str(e)}")
            continue
    
    return merged_sheet_count

def generate_with_merge(output_dir):
    """生成包含合并功能的Excel文件"""
    output_path = Path(output_dir)
    
    if not output_path.exists():
        print(f"错误: 目录不存在: {output_dir}")
        return
    
    csv_files = sorted(output_path.glob("page_*.csv"))
    
    if not csv_files:
        print("未找到CSV文件")
        return
    
    print(f"找到 {len(csv_files)} 个CSV文件")
    print("正在生成包含合并功能的Excel文件...")
    
    all_tables_data = []
    
    for csv_file in csv_files:
        try:
            filename = csv_file.stem
            parts = filename.split('_')
            if len(parts) >= 4:
                page_num = int(parts[1])
                table_num = int(parts[3])
                
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
    
    all_tables_data.sort(key=lambda x: (x['页码'], x['表格编号']))
    
    excel_path = output_path / "all_tables_combined.xlsx"
    print(f"正在创建Excel文件: {excel_path}")
    
    try:
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # 汇总表
            summary_df = pd.DataFrame(all_tables_data)
            summary_df['Sheet名称'] = summary_df.apply(
                lambda row: f"P{row['页码']}_T{row['表格编号']}", axis=1
            )
            summary_df.to_excel(writer, sheet_name='表格汇总', index=False)
            print(f"  [OK] 已添加汇总表")
            
            # 独立表格sheet
            used_sheet_names = {'表格汇总'}
            added_count = 0
            
            for idx, item in enumerate(all_tables_data, start=1):
                try:
                    csv_path = output_path / item['CSV文件名']
                    if csv_path.exists():
                        df = pd.read_csv(csv_path, encoding='utf-8-sig')
                        sheet_name = f"P{item['页码']}_T{item['表格编号']}"
                        sheet_name = clean_sheet_name(sheet_name)
                        
                        original_sheet_name = sheet_name
                        counter = 1
                        while sheet_name in used_sheet_names:
                            sheet_name = f"{original_sheet_name[:28]}_{counter}"
                            counter += 1
                        
                        used_sheet_names.add(sheet_name)
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        added_count += 1
                        
                        if idx % 50 == 0:
                            print(f"  已处理 {idx}/{len(all_tables_data)} 个表格...")
                except Exception as e:
                    continue
            
            print(f"  [OK] 成功添加 {added_count} 个表格到Excel")
            
            # 连续页码合并
            print(f"\n  正在生成连续页码合并的sheet页...")
            merged_count = merge_consecutive_pages_tables(writer, all_tables_data, output_path, used_sheet_names)
            print(f"  [OK] 成功生成 {merged_count} 个连续页码合并的sheet页")
        
        print(f"\n整合Excel文件已生成: {excel_path}")
        print(f"文件大小: {excel_path.stat().st_size / 1024 / 1024:.2f} MB")
        print(f"总计: {len(all_tables_data)} 个表格")
        
    except Exception as e:
        print(f"错误: 生成Excel文件时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    output_dir = r"c:\Users\Z2200\Desktop\Safety Assessment\extracted_tables\tables_20251218_134130"
    generate_with_merge(output_dir)
