"""
PDF 表格提取工具 - Streamlit 入口（用于 Streamlit Cloud 部署）
运行命令: streamlit run streamlit_app.py
"""
import os
import sys
import tempfile
import json
import io
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from pathlib import Path

import streamlit as st

# 确保项目根目录在路径中
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from extract_all_tables import (
    get_all_tables_info,
    filter_tables_for_display,
    extract_all_tables_from_pdf,
)
from backend.app import (
    word_remove_non_table_content,
    _get_docx_table_groups,
)

st.set_page_config(
    page_title="PDF/Word 表格提取工具",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("📄 PDF/Word 表格提取工具")
st.caption("支持两种方式：本地直接处理（适合 Streamlit Cloud，支持 PDF/Word，输出 Word），或连接后端 API（可选）。")

def _join_url(base: str, path: str) -> str:
    base = (base or "").strip().rstrip("/")
    path = (path or "").strip()
    if not base:
        return path
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def _http_json(method: str, url: str, payload: dict | None = None, timeout: int = 60) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = Request(url, data=data, headers=headers, method=method.upper())
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))


def _encode_multipart(file_field: str, filename: str, content: bytes, content_type: str = "application/octet-stream") -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    body = io.BytesIO()
    body.write(f"--{boundary}\r\n".encode("utf-8"))
    body.write(
        (
            f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8")
    )
    body.write(content)
    body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode("utf-8"))
    return body.getvalue(), f"multipart/form-data; boundary={boundary}"


def _http_upload_file(url: str, field_name: str, filename: str, content: bytes, timeout: int = 120) -> dict:
    body, content_type = _encode_multipart(field_name, filename, content)
    req = Request(
        url,
        data=body,
        headers={"Content-Type": content_type, "Accept": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        return json.loads(raw.decode("utf-8")) if raw else {}


def _http_get_bytes(url: str, timeout: int = 120) -> bytes:
    req = Request(url, method="GET")
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _build_docx_from_tables(tables_data: list[dict]) -> bytes:
    from docx import Document
    from docx.shared import Pt
    from docx.oxml.ns import qn
    from docx.enum.table import WD_TABLE_ALIGNMENT

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "等线"
    style.font.size = Pt(9)
    try:
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
    except Exception:
        pass

    for t in tables_data:
        title = (t.get("title") or t.get("name") or t.get("id") or "表格").strip()
        if title:
            p = doc.add_paragraph()
            r = p.add_run(title)
            r.bold = True
            r.font.name = "等线"
            r.font.size = Pt(10.5)
            try:
                r._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
            except Exception:
                pass

        table_data = t.get("data") or []
        if not table_data:
            continue
        num_cols = max((len(row) for row in table_data), default=0)
        if num_cols <= 0:
            continue
        normalized = []
        for row in table_data:
            row = list(row or [])
            while len(row) < num_cols:
                row.append("")
            normalized.append(row[:num_cols])

        tbl = doc.add_table(rows=len(normalized), cols=num_cols, style="Table Grid")
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        for r_idx, row in enumerate(normalized):
            for c_idx, val in enumerate(row):
                cell = tbl.cell(r_idx, c_idx)
                cell.text = "" if val is None else str(val)
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.name = "等线"
                        run.font.size = Pt(9)
                        try:
                            run._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
                        except Exception:
                            pass
        doc.add_paragraph("")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def _extract_tables_from_docx_bytes(docx_bytes: bytes) -> list[dict]:
    from docx import Document

    doc = Document(io.BytesIO(docx_bytes))
    tables_data: list[dict] = []

    for i, tbl in enumerate(doc.tables, start=1):
        data: list[list[str]] = []
        for row in tbl.rows:
            data.append([cell.text.strip() for cell in row.cells])
        if not data:
            continue
        tables_data.append(
            {
                "id": f"docx_table_{i}",
                "name": f"Word 表格 {i}",
                "title": f"Word 表格 {i}",
                "data": data,
            }
        )

    return tables_data


with st.sidebar:
    st.subheader("运行方式")
    mode = st.radio(
        "选择处理方式",
        options=["本地处理（推荐用于 Streamlit Cloud）", "连接后端 API（推荐用于本机/服务器）"],
        index=0,
    )
    api_base = st.text_input("后端地址（API 模式）", value="http://localhost:5000", help="示例：http://localhost:5000 或 https://xxx.onrender.com")
    api_timeout = st.slider("API 超时（秒）", min_value=10, max_value=300, value=120, step=10)

uploaded_file = st.file_uploader(
    "上传文件",
    type=["pdf", "docx"],
    help="支持 PDF / Word（.docx）。在 Streamlit Cloud 推荐使用「本地处理」，结果导出为 Word（.docx）。",
)

if uploaded_file is None:
    st.info("请先上传一个 PDF 或 Word（.docx）文件。")
    st.stop()

filename = (uploaded_file.name or "upload").strip()
ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
file_bytes = uploaded_file.getvalue()

if mode.startswith("本地处理"):
    if ext not in {"pdf", "docx"}:
        st.error("仅支持上传 PDF 或 Word（.docx）。")
        st.stop()

    st.write("导出格式：**Word（.docx，仅表格）**")

    if ext == "docx":
        # 本地 Word 处理：与后端逻辑对齐，只保留表格及其上方一行表名
        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, filename or "upload.docx")
            with open(in_path, "wb") as f:
                f.write(file_bytes)

            try:
                with st.spinner("正在分析 Word 中的表格…"):
                    groups, _ = _get_docx_table_groups(in_path)
            except Exception as e:
                st.error(f"读取 Word 失败：{e}")
                st.stop()

            if not groups:
                st.warning("未在该 Word 文档中发现表格。")
                st.stop()

            st.success(f"共识别到 **{len(groups)}** 个表格（按表名去重后）。")

            options = []
            option_to_id = {}
            for g in groups:
                name = g.get("name") or g.get("id") or "表格"
                count = g.get("count") or 1
                if count and count > 1:
                    label = f"{name}（共 {count} 个同名表）"
                else:
                    label = name
                options.append(label)
                option_to_id[label] = g.get("id")

            selected_options = st.multiselect(
                "选择要保留的表格（不选则保留全部）",
                options=options,
                default=options,
                help="每项代表一个表名，若同名有多个表格，则会一起保留。",
            )
            selected_ids = [option_to_id[o] for o in selected_options] if selected_options else None

            if st.button("生成 Word（.docx，仅保留表格）", type="primary"):
                out_path = os.path.join(tmpdir, f"{Path(filename).stem}_tables_only.docx")
                try:
                    with st.spinner("正在删除非表格内容并生成 Word…"):
                        kept = word_remove_non_table_content(in_path, out_path, selected_ids)
                        if kept <= 0:
                            st.error("文档中无表格或未选择任何表格。")
                            st.stop()
                        with open(out_path, "rb") as f:
                            docx_bytes = f.read()
                    st.download_button(
                        "下载结果 Word（.docx）",
                        data=docx_bytes,
                        file_name=f"{Path(filename).stem}_tables_only.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                    st.success(f"已保留 {kept} 个表格，其他内容已删除。")
                except Exception as e:
                    st.error(f"生成失败：{e}")

    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, filename)
            with open(pdf_path, "wb") as f:
                f.write(file_bytes)

            try:
                with st.spinner("正在识别 PDF 中的表格…"):
                    all_tables = get_all_tables_info(pdf_path)
                    display_tables = filter_tables_for_display(all_tables)
            except Exception as e:
                st.error(f"识别表格失败：{e}")
                st.stop()

            if not display_tables:
                st.warning("未在该 PDF 中发现可显示的表格。")
                st.stop()

            st.success(f"共识别到 **{len(display_tables)}** 个表格（共 {len(all_tables)} 个区域）。")

            options = [f"{t.get('name', t.get('id', ''))}（第{t.get('page', '?')}页）" for t in display_tables]
            option_to_id = {opt: t["id"] for t, opt in zip(display_tables, options)}

            selected_options = st.multiselect(
                "选择要提取的表格（不选则提取全部）",
                options=options,
                default=[],
                help="可多选；不选则导出所有表格。",
            )
            selected_ids = [option_to_id[opt] for opt in selected_options] if selected_options else None

            if st.button("生成 Word（.docx）", type="primary"):
                out_dir = os.path.join(tmpdir, "output")
                os.makedirs(out_dir, exist_ok=True)
                try:
                    with st.spinner("正在提取表格并生成 Word…"):
                        result = extract_all_tables_from_pdf(
                            pdf_path,
                            output_dir=out_dir,
                            selected_table_ids=selected_ids,
                            output_format="docx",
                        )
                        tables_data = result.get("tables_data", []) if isinstance(result, dict) else []
                        if not tables_data:
                            st.error("未提取到任何表格数据。")
                            st.stop()
                        docx_bytes = _build_docx_from_tables(tables_data)
                    st.download_button(
                        "下载结果 Word（.docx）",
                        data=docx_bytes,
                        file_name=f"{Path(filename).stem}_tables.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                    st.success(f"已提取 {len(tables_data)} 个表格，请点击上方按钮下载。")
                except Exception as e:
                    st.error(f"提取失败：{e}")

else:
    base = (api_base or "").strip()
    if not base:
        st.error("请输入后端地址（例如 http://localhost:5000）。")
        st.stop()

    try:
        with st.spinner("正在检查后端服务…"):
            health = _http_json("GET", _join_url(base, "/api/health"), timeout=int(api_timeout))
        if not isinstance(health, dict) or health.get("status") != "ok":
            st.warning(f"后端健康检查返回异常：{health}")
    except Exception as e:
        st.error(f"无法连接后端：{e}")
        st.stop()

    try:
        with st.spinner("正在上传文件到后端…"):
            up = _http_upload_file(_join_url(base, "/api/upload"), "file", filename, file_bytes, timeout=int(api_timeout))
        backend_filename = up.get("filename")
        if not backend_filename:
            st.error(f"上传失败：{up}")
            st.stop()
        st.success("上传成功，正在读取表格列表…")
    except HTTPError as e:
        st.error(f"上传失败（HTTP {e.code}）：{e.read().decode('utf-8', errors='ignore')}")
        st.stop()
    except URLError as e:
        st.error(f"上传失败（网络错误）：{e}")
        st.stop()
    except Exception as e:
        st.error(f"上传失败：{e}")
        st.stop()

    try:
        with st.spinner("正在获取表格列表…"):
            tables_resp = _http_json("POST", _join_url(base, "/api/tables"), payload={"filename": backend_filename}, timeout=int(api_timeout))
        tables = tables_resp.get("tables", []) if isinstance(tables_resp, dict) else []
        if not tables:
            st.warning(f"未获取到表格列表：{tables_resp}")
            st.stop()
    except Exception as e:
        st.error(f"获取表格列表失败：{e}")
        st.stop()

    st.success(f"后端共返回 **{len(tables)}** 个表格供选择。")
    options = []
    option_to_id = {}
    for t in tables:
        tid = t.get("id")
        if not tid:
            continue
        page = t.get("page") or t.get("page_num") or "?"
        name = t.get("name") or t.get("title") or tid
        opt = f"{name}（第{page}页）"
        options.append(opt)
        option_to_id[opt] = tid

    selected_options = st.multiselect(
        "选择要提取的表格（不选则提取全部）",
        options=options,
        default=[],
        help="API 模式下最终输出为 Word（.docx）。",
    )
    selected_ids = [option_to_id[opt] for opt in selected_options] if selected_options else None

    if st.button("提取并生成 Word（.docx）", type="primary"):
        try:
            with st.spinner("后端正在提取并生成 Word…"):
                payload = {"filename": backend_filename}
                if selected_ids is not None:
                    payload["selected_table_ids"] = selected_ids
                result = _http_json("POST", _join_url(base, "/api/extract"), payload=payload, timeout=int(api_timeout))
            dl = result.get("download_url")
            out_name = result.get("output_filename") or "result.docx"
            if not dl:
                st.error(f"提取失败：{result}")
                st.stop()
            dl_url = _join_url(base, dl)
            with st.spinner("正在下载生成结果…"):
                out_bytes = _http_get_bytes(dl_url, timeout=int(api_timeout))
            st.download_button(
                "下载结果文件",
                data=out_bytes,
                file_name=out_name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            st.success(f"已生成：{out_name}（表格数量：{result.get('total_tables', '未知')}）")
        except HTTPError as e:
            st.error(f"提取失败（HTTP {e.code}）：{e.read().decode('utf-8', errors='ignore')}")
        except Exception as e:
            st.error(f"提取失败：{e}")
