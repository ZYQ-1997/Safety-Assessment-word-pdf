"""
从PDF文件中提取表格区域并保存为新的PDF文件
使用pdfplumber识别表格位置，使用PyMuPDF裁剪和合并PDF页面

功能：
1. 识别PDF中的所有表格位置
2. 裁剪包含表格的页面区域
3. 将所有裁剪的区域合并成新的PDF文件
"""
import pdfplumber
import os
import warnings
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

# 尝试导入PyMuPDF (fitz)，如果失败则使用pypdf作为备选
try:
    import fitz  # PyMuPDF
    USE_PYMUPDF = True
except ImportError:
    USE_PYMUPDF = False
    from pypdf import PdfWriter, PdfReader
    from pypdf.generic import RectangleObject
    import copy

# 配置logging过滤器以忽略Xref相关的错误
class XrefFilter(logging.Filter):
    """过滤Xref相关错误的日志过滤器"""
    def filter(self, record):
        message = str(record.getMessage())
        # 过滤掉Xref相关的错误
        if 'Xref' in message or ('entry' in message.lower() and 'invalid' in message.lower()):
            return False
        return True

# 为pypdf的logger添加过滤器
pypdf_logger = logging.getLogger('pypdf')
pypdf_logger.addFilter(XrefFilter())


def calculate_table_region(bbox: Tuple[float, float, float, float], 
                          page_width: float, 
                          page_height: float,
                          margin_top: float = 80,
                          margin_bottom: float = 20,
                          margin_left: float = 20,
                          margin_right: float = 20) -> Tuple[float, float, float, float]:
    """
    计算表格区域的裁剪边界，包括表格上方的标题区域
    
    参数:
        bbox: 表格边界框 (x0, top, x1, bottom) - pdfplumber格式
        page_width: 页面宽度（点）
        page_height: 页面高度（点）
        margin_top: 表格上方的边距（像素，用于包含标题）
        margin_bottom: 表格下方的边距（像素）
        margin_left: 左侧边距（像素）
        margin_right: 右侧边距（像素）
    
    返回:
        (left, bottom, right, top) - pypdf裁剪格式
    """
    x0, top, x1, bottom = bbox
    
    # pdfplumber的坐标系：原点在左上角，y轴向下
    # pypdf的坐标系：原点在左下角，y轴向上
    # 需要转换y坐标
    
    # 计算裁剪区域
    # 左边界：表格左边界减去左边距，但不能小于0
    left = max(0, x0 - margin_left)
    
    # 右边界：表格右边界加上右边距，但不能大于页面宽度
    right = min(page_width, x1 + margin_right)
    
    # 上边界（pdfplumber的top）：表格上方减去上边距（向上扩展），但不能小于0
    # top值越小表示位置越靠上
    top_bound = max(0, top - margin_top)
    
    # 下边界（pdfplumber的bottom）：表格下方加上下边距（向下扩展），但不能大于页面高度
    bottom_bound = min(page_height, bottom + margin_bottom)
    
    # 转换为pypdf坐标系（左下角为原点）
    # pdfplumber: y坐标从上到下（top < bottom）
    # pypdf: y坐标从下到上（bottom < top）
    pypdf_bottom = page_height - bottom_bound
    pypdf_top = page_height - top_bound
    
    return (left, pypdf_bottom, right, pypdf_top)


def extract_table_name_from_page(page, table_bbox, table_data) -> Optional[str]:
    """
    从PDF页面中提取表格名称
    
    参数:
        page: pdfplumber页面对象
        table_bbox: 表格的边界框 (x0, top, x1, bottom)
        table_data: 表格数据（可选）
    
    返回:
        表格名称（如果找到），否则返回None
    """
    import re
    
    try:
        if table_bbox:
            x0, top, x1, bottom = table_bbox
            # 提取表格上方的文本（向上查找80像素）
            top_margin = 80
            search_top = max(0, top - top_margin)
            
            # 获取表格上方的文本
            text_above = page.within_bbox((x0, search_top, x1, top)).extract_text()
            
            if text_above:
                # 按行分割文本
                lines = [line.strip() for line in text_above.split('\n') if line.strip()]
                
                # 从下往上查找（最接近表格的文本更可能是表格名称）
                for line in reversed(lines):
                    # 跳过页码、页眉等
                    if re.match(r'^\d+$', line) or len(line) < 3:
                        continue
                    
                    # 清理行内容
                    line_clean = re.sub(r'\s+', ' ', line).strip()
                    
                    # 检查是否包含表格相关关键词
                    table_keywords = ['表', '一览表', '清单', '明细', '统计表', '汇总表', '登记表', '记录表']
                    if any(keyword in line_clean for keyword in table_keywords):
                        # 提取表格名称（移除可能的编号前缀，如"表1-1"）
                        name = re.sub(r'^表\s*\d+[-\s]*\d*\s*[：:]\s*', '', line_clean)
                        name = re.sub(r'^表\s*\d+\s*[：:]\s*', '', name)
                        name = name.strip()
                        
                        if 2 <= len(name) <= 50:
                            return name
    except Exception:
        pass
    
    return None


def is_formal_table_name(name: str) -> bool:
    """
    判断表格名称是否是正式名称（不是"页码-表格编号"格式）
    
    参数:
        name: 表格名称
    
    返回:
        True表示是正式名称，False表示是"页码-表格编号"格式
    """
    if not name:
        return False
    
    # 检查是否是"第X页-表格X"格式
    pattern = r'^第\d+页-表格\d+$'
    if re.match(pattern, name):
        return False
    
    return True


def filter_tables_for_display(tables_info: List[dict]) -> List[dict]:
    """
    过滤表格列表，只显示有正式名称的表格
    但保留文档开头的"页码-表格编号"表格（如果它们前面没有正式名称表格）
    
    参数:
        tables_info: 完整的表格信息列表
    
    返回:
        过滤后的表格信息列表（用于前端显示）
    """
    if not tables_info:
        return []
    
    filtered = []
    first_formal_table_index = -1  # 第一个正式名称表格的索引
    
    # 第一遍：找到第一个正式名称表格的位置
    for i, table in enumerate(tables_info):
        if is_formal_table_name(table.get('name', '')):
            first_formal_table_index = i
            break  # 找到第一个就停止
    
    # 第二遍：过滤表格
    for i, table in enumerate(tables_info):
        name = table.get('name', '')
        
        # 如果是正式名称表格，保留
        if is_formal_table_name(name):
            filtered.append(table)
        # 如果是"页码-表格编号"格式
        else:
            # 如果这个表格在第一个正式名称表格之前，保留（文档开头的独立表格）
            # 或者如果整个文档都没有正式名称表格，也保留（全部都是"页码-表格编号"格式）
            if first_formal_table_index == -1 or i < first_formal_table_index:
                filtered.append(table)
            # 否则跳过（这是某个正式表格的截断部分）
            # 不添加到显示列表，但会在下载时自动包含
    
    print(f"[调试] 过滤表格: 总数={len(tables_info)}, 过滤后={len(filtered)}, 第一个正式表格索引={first_formal_table_index}")
    
    return filtered


def get_related_table_ids(tables_info: List[dict], selected_table_id: str) -> List[str]:
    """
    获取与选中表格相关的所有表格ID（包括后续的"页码-表格编号"表格）
    
    参数:
        tables_info: 完整的表格信息列表
        selected_table_id: 选中的表格ID
    
    返回:
        相关的表格ID列表（包括选中的表格和后续的截断部分）
    """
    if not tables_info:
        return [selected_table_id]
    
    # 找到选中表格的索引
    selected_index = -1
    for i, table in enumerate(tables_info):
        if table.get('id') == selected_table_id:
            selected_index = i
            break
    
    if selected_index == -1:
        return [selected_table_id]
    
    # 检查选中的表格是否是正式名称表格
    selected_table = tables_info[selected_index]
    if not is_formal_table_name(selected_table.get('name', '')):
        # 如果不是正式名称表格，只返回它自己
        return [selected_table_id]
    
    # 如果是正式名称表格，收集它和后续的所有"页码-表格编号"表格
    related_ids = [selected_table_id]
    
    # 从下一个表格开始，收集所有连续的"页码-表格编号"表格
    for i in range(selected_index + 1, len(tables_info)):
        table = tables_info[i]
        name = table.get('name', '')
        
        # 如果遇到下一个正式名称表格，停止收集
        if is_formal_table_name(name):
            break
        
        # 执行到这里说明是"页码-表格编号"格式，添加到相关列表
        related_ids.append(table.get('id'))
    
    return related_ids


def get_all_tables_info(pdf_path: str) -> List[dict]:
    """
    获取PDF中所有表格的信息列表
    
    参数:
        pdf_path: PDF文件路径
    
    返回:
        表格信息列表，每个元素包含：
        - id: 表格唯一ID（页码_表格序号）
        - page: 页码
        - table_num: 表格在该页的序号
        - name: 表格名称（如果识别到）
        - bbox: 表格边界框
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"文件不存在: {pdf_path}")
    
    tables_info = []
    table_id_counter = 0
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # 查找表格对象
                table_objects = page.find_tables()
                
                if table_objects:
                    for table_num, table_obj in enumerate(table_objects, start=1):
                        table_id_counter += 1
                        table_id = f"page_{page_num}_table_{table_num}"
                        
                        # 尝试提取表格名称
                        table_data = None
                        try:
                            tables = page.extract_tables()
                            if table_num <= len(tables):
                                table_data = tables[table_num - 1]
                        except:
                            pass
                        
                        table_name = extract_table_name_from_page(page, table_obj.bbox, table_data)
                        
                        # 如果没有识别到名称，使用默认名称
                        if not table_name:
                            table_name = f"第{page_num}页-表格{table_num}"
                        
                        tables_info.append({
                            'id': table_id,
                            'page': page_num,
                            'table_num': table_num,
                            'name': table_name,
                            'bbox': table_obj.bbox  # (x0, top, x1, bottom)
                        })
    except Exception as e:
        error_msg = f"识别表格信息时发生错误: {str(e)}"
        print(f"错误: {error_msg}")
        raise Exception(error_msg) from e
    
    return tables_info


def merge_overlapping_regions(regions: List[Tuple[float, float, float, float]]) -> List[Tuple[float, float, float, float]]:
    """
    合并重叠的表格区域，避免重复裁剪
    
    参数:
        regions: 区域列表，每个区域为 (left, bottom, right, top)
    
    返回:
        合并后的区域列表
    """
    if not regions:
        return []
    
    # 按bottom坐标排序（从下到上）
    sorted_regions = sorted(regions, key=lambda r: r[1])
    merged = []
    
    for region in sorted_regions:
        if not merged:
            merged.append(region)
            continue
        
        # 检查是否与最后一个合并区域重叠
        last = merged[-1]
        left1, bottom1, right1, top1 = last
        left2, bottom2, right2, top2 = region
        
        # 检查是否重叠（在x轴和y轴上都有重叠）
        x_overlap = not (right1 < left2 or right2 < left1)
        y_overlap = not (top1 < bottom2 or top2 < bottom1)
        
        if x_overlap and y_overlap:
            # 合并区域
            new_left = min(left1, left2)
            new_bottom = min(bottom1, bottom2)
            new_right = max(right1, right2)
            new_top = max(top1, top2)
            merged[-1] = (new_left, new_bottom, new_right, new_top)
        else:
            merged.append(region)
    
    return merged


def extract_tables_as_pdf(pdf_path: str, output_path: Optional[str] = None, selected_table_ids: Optional[List[str]] = None) -> str:
    """
    从PDF文件中提取表格区域，保存为新的PDF文件
    
    参数:
        pdf_path: 输入PDF文件路径
        output_path: 输出PDF文件路径（如果为None，则自动生成）
        selected_table_ids: 要提取的表格ID列表（如果为None，则提取所有表格）
                           表格ID格式为: "page_{页码}_table_{表格序号}"
                           如果选择的是有正式名称的表格，会自动包含后续的"页码-表格编号"表格
    
    返回:
        输出PDF文件的路径
    """
    if not os.path.exists(pdf_path):
        error_msg = f"错误: 文件不存在: {pdf_path}"
        print(error_msg)
        raise FileNotFoundError(error_msg)
    
    # 如果指定了选择的表格，自动扩展为包含相关表格（截断部分）
    if selected_table_ids:
        # 获取所有表格信息
        all_tables_info = get_all_tables_info(pdf_path)
        
        # 扩展selected_table_ids，包含每个选中表格的相关表格
        expanded_table_ids = []
        for table_id in selected_table_ids:
            related_ids = get_related_table_ids(all_tables_info, table_id)
            expanded_table_ids.extend(related_ids)
        
        # 去重并保持顺序
        seen = set()
        selected_table_ids = []
        for table_id in expanded_table_ids:
            if table_id not in seen:
                seen.add(table_id)
                selected_table_ids.append(table_id)
        
        print(f"已自动包含相关表格，共 {len(selected_table_ids)} 个表格")
    
    # 生成输出文件路径
    if output_path is None:
        pdf_name = Path(pdf_path).stem
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(pdf_path).parent
        output_path = str(output_dir / f"{pdf_name}_tables_{timestamp}.pdf")
    
    output_path = Path(output_path)
    
    print("=" * 60)
    print("开始提取PDF中的表格区域")
    print("=" * 60)
    print(f"输入PDF文件: {pdf_path}")
    print(f"文件大小: {os.path.getsize(pdf_path) / 1024 / 1024:.2f} MB")
    print(f"输出PDF文件: {output_path}")
    print("=" * 60)
    
    # 存储所有需要裁剪的页面和区域
    page_regions = {}  # {page_num: [(left, bottom, right, top), ...]}
    
    # 使用pdfplumber识别表格位置
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"\nPDF总页数: {total_pages}")
            print("\n正在识别表格位置...")
            
            total_tables = 0
            
            for page_num, page in enumerate(pdf.pages, start=1):
                # 获取页面尺寸
                page_width = page.width
                page_height = page.height
                
                # 查找表格对象（包含边界框信息）
                table_objects = page.find_tables()
                
                if table_objects:
                    # 存储当前页面的所有表格区域
                    regions = []
                    page_selected_count = 0
                    
                    for table_num, table_obj in enumerate(table_objects, start=1):
                        # 生成表格ID
                        table_id = f"page_{page_num}_table_{table_num}"
                        
                        # 如果指定了选择的表格ID列表，只处理选中的表格
                        if selected_table_ids is not None and table_id not in selected_table_ids:
                            continue
                        
                        page_selected_count += 1
                        total_tables += 1
                        
                        bbox = table_obj.bbox  # (x0, top, x1, bottom)
                        # 计算裁剪区域（包括标题）
                        crop_region = calculate_table_region(
                            bbox, 
                            page_width, 
                            page_height,
                            margin_top=80,  # 表格上方80像素，用于包含标题
                            margin_bottom=20,  # 表格下方20像素
                            margin_left=20,  # 左右各20像素边距
                            margin_right=20
                        )
                        regions.append(crop_region)
                    
                    if page_selected_count > 0:
                        print(f"  第 {page_num} 页: 找到 {len(table_objects)} 个表格，选中 {page_selected_count} 个")
                        
                        # 合并重叠的区域
                        merged_regions = merge_overlapping_regions(regions)
                        
                        if merged_regions:
                            page_regions[page_num] = merged_regions
                            print(f"    -> 生成 {len(merged_regions)} 个裁剪区域")
                
                # 每处理10页显示一次进度
                if page_num % 10 == 0:
                    print(f"  已处理 {page_num}/{total_pages} 页，找到 {total_tables} 个表格")
            
            if total_tables == 0:
                if selected_table_ids:
                    print(f"\n警告: 未找到任何选中的表格")
                    raise ValueError(f"未找到任何选中的表格，选中的表格ID: {selected_table_ids}")
                else:
                    print(f"\n警告: 在PDF中未找到任何表格")
                    print(f"总页数: {total_pages}")
                    raise ValueError("PDF中未找到任何表格")
            
            if selected_table_ids:
                print(f"\n共找到 {total_tables} 个选中的表格，分布在 {len(page_regions)} 页中")
            else:
                print(f"\n共找到 {total_tables} 个表格，分布在 {len(page_regions)} 页中")
    
    except Exception as e:
        error_msg = f"识别表格时发生错误: {str(e)}"
        print(f"\n错误: {error_msg}")
        raise Exception(error_msg) from e
    
    # 使用PyMuPDF或pypdf裁剪和合并PDF
    try:
        print(f"\n正在裁剪PDF页面并生成新PDF...")
        
        total_regions = sum(len(regions) for regions in page_regions.values())
        print(f"  需要处理 {len(page_regions)} 页，共 {total_regions} 个区域")
        
        if USE_PYMUPDF:
            # 使用PyMuPDF (fitz) - 更简单快捷的方法
            print(f"  使用PyMuPDF进行裁剪（快速模式）...")
            
            # 打开源PDF
            source_pdf = fitz.open(pdf_path)
            output_pdf = fitz.open()  # 创建新的PDF
            
            pages_added = 0
            
            for page_num, regions in sorted(page_regions.items()):
                page_index = page_num - 1
                
                if page_index >= len(source_pdf):
                    print(f"  警告: 页面 {page_num} 超出范围，跳过")
                    continue
                
                source_page = source_pdf[page_index]
                page_height = source_page.rect.height  # 获取页面高度用于坐标转换
                
                # 为每个区域创建一个裁剪后的页面
                for region_idx, (left, bottom, right, top) in enumerate(regions):
                    try:
                        # 坐标转换：regions中的坐标是pypdf格式（左下角为原点）
                        # 需要转换为fitz格式（左上角为原点）
                        # pypdf: (left, bottom, right, top) - bottom < top，原点在左下角
                        # fitz: (x0, y0, x1, y1) - y0 < y1，原点在左上角
                        # 转换公式: fitz_y = page_height - pypdf_y
                        fitz_y0 = page_height - top   # 上边界（pypdf的top对应fitz的较小y值）
                        fitz_y1 = page_height - bottom  # 下边界（pypdf的bottom对应fitz的较大y值）
                        
                        # 创建裁剪矩形（fitz格式：左上角为原点）
                        rect = fitz.Rect(left, fitz_y0, right, fitz_y1)
                        
                        # 方法：直接在新页面中显示源页面的指定区域
                        # 创建新页面，尺寸与裁剪区域相同
                        new_page = output_pdf.new_page(width=rect.width, height=rect.height)
                        
                        # 将源页面的指定区域显示在新页面中
                        # 需要将rect区域的内容平移到新页面的(0,0)位置
                        # 使用变换：将rect的左上角(rect.x0, rect.y0)映射到新页面的(0,0)
                        # 变换矩阵：[1, 0, 0, 1, -rect.x0, -rect.y0]
                        
                        # 使用渲染方式确保内容正确
                        # 从源页面渲染指定区域
                        pix = source_page.get_pixmap(clip=rect, matrix=fitz.Matrix(2, 2))
                        
                        # 在新页面中插入渲染的图片
                        new_page.insert_image(
                            fitz.Rect(0, 0, rect.width, rect.height),
                            pixmap=pix
                        )
                        
                        pix = None  # 释放内存
                        
                        pages_added += 1
                        
                        if pages_added % 10 == 0 or region_idx == len(regions) - 1:
                            print(f"  已处理 {pages_added}/{total_regions} 个区域...")
                    
                    except Exception as e:
                        print(f"  错误: 处理第 {page_num} 页的区域 {region_idx + 1} 时发生错误: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        continue
            
            # 保存PDF文件
            print(f"\n正在保存PDF文件到: {output_path}...")
            output_pdf.save(output_path)
            output_pdf.close()
            source_pdf.close()
            print(f"  [OK] PDF文件保存成功，共 {pages_added} 页")
        
        else:
            # 使用pypdf作为备选方案
            print(f"  使用pypdf进行裁剪（备选模式）...")
            
            # 过滤Xref相关的警告信息
            warnings.filterwarnings('ignore', category=UserWarning)
            warnings.filterwarnings('ignore', message='.*Xref.*')
            warnings.filterwarnings('ignore', message='.*entry.*invalid.*')
            
            import sys
            from io import StringIO
            
            class FilteredStderr:
                """过滤Xref相关错误的stderr包装器"""
                def __init__(self, original_stderr):
                    self.original_stderr = original_stderr
                
                def write(self, message):
                    if message and ('Xref' in message or ('entry' in message.lower() and 'invalid' in message.lower())):
                        return
                    self.original_stderr.write(message)
                
                def flush(self):
                    self.original_stderr.flush()
            
            old_stderr = sys.stderr
            sys.stderr = FilteredStderr(old_stderr)
            
            try:
                pdf_reader = PdfReader(pdf_path, strict=False)
            finally:
                sys.stderr = old_stderr
            
            pdf_writer = PdfWriter()
            pages_added = 0
            
            for page_num, regions in sorted(page_regions.items()):
                page_index = page_num - 1
                
                if page_index >= len(pdf_reader.pages):
                    print(f"  警告: 页面 {page_num} 超出范围，跳过")
                    continue
                
                original_page = pdf_reader.pages[page_index]
                
                for region_idx, (left, bottom, right, top) in enumerate(regions):
                    try:
                        # 使用序列化方法复制页面（比deepcopy快）
                        temp_writer = PdfWriter()
                        temp_writer.add_page(original_page)
                        
                        from io import BytesIO
                        temp_buffer = BytesIO()
                        temp_writer.write(temp_buffer)
                        temp_buffer.seek(0)
                        
                        temp_reader = PdfReader(temp_buffer, strict=False)
                        cropped_page = temp_reader.pages[0]
                        cropped_page.cropbox = RectangleObject([left, bottom, right, top])
                        
                        pdf_writer.add_page(cropped_page)
                        pages_added += 1
                        
                        if pages_added % 10 == 0:
                            print(f"  已处理 {pages_added}/{total_regions} 个区域...")
                    
                    except Exception as e:
                        print(f"  错误: 处理第 {page_num} 页的区域 {region_idx + 1} 时发生错误: {str(e)}")
                        continue
            
            print(f"\n正在保存PDF文件到: {output_path}...")
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            print(f"  [OK] PDF文件保存成功，共 {pages_added} 页")
        
        print(f"\n" + "=" * 60)
        print("提取完成！")
        print("=" * 60)
        print(f"总页数: {total_pages}")
        print(f"找到表格: {total_tables} 个")
        print(f"输出PDF页数: {pages_added} 页")
        print(f"输出文件: {output_path}")
        print(f"输出文件大小: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
        print("=" * 60)
        
        return str(output_path)
    
    except Exception as e:
        error_msg = f"裁剪PDF时发生错误: {str(e)}"
        print(f"\n错误: {error_msg}")
        import traceback
        traceback.print_exc()
        raise Exception(error_msg) from e


def extract_all_tables_from_pdf(pdf_path: str, output_dir: str = "extracted_tables", selected_table_ids: Optional[List[str]] = None) -> dict:
    """
    向后兼容的函数，用于适配后端API
    
    这个函数调用新的 extract_tables_as_pdf 函数，但返回后端期望的格式
    
    参数:
        pdf_path: 输入PDF文件路径
        output_dir: 输出目录
        selected_table_ids: 要提取的表格ID列表（如果为None，则提取所有表格）
    
    返回:
        包含提取结果的字典（适配后端API格式）
    """
    try:
        # 生成输出PDF文件路径
        pdf_name = Path(pdf_path).stem
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_pdf_path = os.path.join(output_dir, f"{pdf_name}_tables_{timestamp}.pdf")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 调用新的PDF提取函数
        result_pdf_path = extract_tables_as_pdf(pdf_path, output_pdf_path, selected_table_ids)
        
        # 读取PDF以获取页数
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
        
        # 读取输出PDF以获取页数（表格区域页数）
        # 如果USE_PYMUPDF为False，PdfReader已在顶部导入；否则需要导入
        if USE_PYMUPDF:
            from pypdf import PdfReader
        output_reader = PdfReader(result_pdf_path, strict=False)
        total_output_pages = len(output_reader.pages)
        
        # 返回后端期望的格式
        return {
            'total_pages': total_pages,
            'total_tables': total_output_pages,  # 输出PDF的页数就是表格区域的数量
            'output_dir': output_dir,
            'output_pdf': result_pdf_path,  # 新增：输出PDF文件路径
            'tables_data': []  # 空列表，因为新功能不提取表格数据，只提取PDF区域
        }
    except Exception as e:
        import traceback
        error_msg = f"提取PDF表格区域时发生错误: {str(e)}"
        print(f"错误: {error_msg}")
        traceback.print_exc()
        raise Exception(error_msg) from e


def main():
    """主函数"""
    # 默认PDF文件路径
    pdf_path = r"c:\Users\Z2200\Desktop\Safety Assessment\safety-assessment.pdf"
    
    # 如果文件不存在，提示用户
    if not os.path.exists(pdf_path):
        print(f"错误: PDF文件不存在: {pdf_path}")
        print("\n使用方法:")
        print("  python extract_all_tables.py")
        print("  或者修改脚本中的 pdf_path 变量")
        return
    
    try:
        output_path = extract_tables_as_pdf(pdf_path)
        print(f"\n[成功] 成功提取表格区域并保存到: {output_path}")
    except Exception as e:
        print(f"\n[失败] 提取失败: {str(e)}")


if __name__ == "__main__":
    main()
