#!/usr/bin/env python3
"""
Script chuyển Markdown → Word (.docx) với format chuyên nghiệp.
- Bảng có border, header tô nền, cột tự điều chỉnh theo nội dung
- Font Times New Roman 12pt, justify, thụt đầu dòng
- Sơ đồ Mermaid → render thành ảnh PNG và chèn vào Word
- Header công ty SETCOM trên mỗi trang
"""

import subprocess
import sys
import os
import re
import tempfile
import shutil
import time
from pathlib import Path

from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor, Emu
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


# ============================================================
# THÔNG TIN CÔNG TY (lấy từ setcom.com.vn)
# ============================================================
COMPANY_NAME = "SETCOM"
COMPANY_FULL = "Công ty TNHH Dịch vụ và Thiết bị Khoa học Setcom"
COMPANY_HOTLINE = "0913 425 986"
COMPANY_WEBSITE = "setcom.com.vn"
COMPANY_EMAIL = "info@setcom.com.vn"


def add_company_header(doc):
    """Thêm header công ty SETCOM nổi bật vào mỗi trang."""
    
    HEADER_COLOR = RGBColor(0x1F, 0x4E, 0x79)  # Xanh đậm chủ đạo
    HEADER_GRAY = RGBColor(0x55, 0x55, 0x55)
    
    for section in doc.sections:
        header = section.header
        header.is_linked_to_previous = False
        
        # Xóa nội dung cũ nếu có
        for p in header.paragraphs:
            p.clear()
        
        # ── Dòng 1: Tên công ty nổi bật ──
        if header.paragraphs:
            para1 = header.paragraphs[0]
        else:
            para1 = header.add_paragraph()
        
        para1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        para1.paragraph_format.first_line_indent = Cm(0)
        para1.paragraph_format.space_after = Pt(1)
        para1.paragraph_format.space_before = Pt(0)
        
        # Tên viết tắt (lớn, bold, xanh đậm)
        run_name = para1.add_run(COMPANY_NAME)
        run_name.bold = True
        run_name.font.size = Pt(11)
        run_name.font.name = 'Times New Roman'
        run_name.font.color.rgb = HEADER_COLOR
        
        # Separator
        run_sep = para1.add_run("  —  ")
        run_sep.font.size = Pt(9)
        run_sep.font.name = 'Times New Roman'
        run_sep.font.color.rgb = HEADER_GRAY
        
        # Tên đầy đủ
        run_full = para1.add_run(COMPANY_FULL)
        run_full.font.size = Pt(9)
        run_full.font.name = 'Times New Roman'
        run_full.font.color.rgb = HEADER_GRAY
        
        # ── Dòng 2: Thông tin liên hệ ──
        para2 = header.add_paragraph()
        para2.alignment = WD_ALIGN_PARAGRAPH.LEFT
        para2.paragraph_format.first_line_indent = Cm(0)
        para2.paragraph_format.space_after = Pt(4)
        para2.paragraph_format.space_before = Pt(0)
        
        # Hotline
        run_icon1 = para2.add_run("☎ ")
        run_icon1.font.size = Pt(8)
        run_icon1.font.name = 'Times New Roman'
        run_icon1.font.color.rgb = HEADER_COLOR
        
        run_phone = para2.add_run(COMPANY_HOTLINE)
        run_phone.font.size = Pt(8)
        run_phone.font.name = 'Times New Roman'
        run_phone.font.color.rgb = HEADER_GRAY
        
        run_sep1 = para2.add_run("    ✉ ")
        run_sep1.font.size = Pt(8)
        run_sep1.font.name = 'Times New Roman'
        run_sep1.font.color.rgb = HEADER_COLOR
        
        run_email = para2.add_run(COMPANY_EMAIL)
        run_email.font.size = Pt(8)
        run_email.font.name = 'Times New Roman'
        run_email.font.color.rgb = HEADER_GRAY
        
        run_sep2 = para2.add_run("    🌐 ")
        run_sep2.font.size = Pt(8)
        run_sep2.font.name = 'Times New Roman'
        run_sep2.font.color.rgb = HEADER_COLOR
        
        run_web = para2.add_run(COMPANY_WEBSITE)
        run_web.bold = True
        run_web.font.size = Pt(8)
        run_web.font.name = 'Times New Roman'
        run_web.font.color.rgb = HEADER_COLOR
        
        # Border dưới header (đường kẻ xanh đậm nổi bật)
        pPr = para2._element.get_or_add_pPr()
        pBdr = parse_xml(
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:bottom w:val="single" w:sz="8" w:space="2" w:color="1F4E79"/>'
            f'</w:pBdr>'
        )
        pPr.append(pBdr)


def _render_single_mermaid(code, img_path, mmdc, mmdc_config):
    """Render 1 block Mermaid → PNG. Trả về True nếu thành công."""
    tmp_mmd = os.path.join(tempfile.gettempdir(), f"mermaid_{os.getpid()}.mmd")
    with open(tmp_mmd, "w", encoding="utf-8") as f:
        f.write(code)
    try:
        result = subprocess.run(
            [mmdc, "-i", tmp_mmd, "-o", img_path, "-w", "1200", "-s", "2",
             "--configFile", mmdc_config],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0 and os.path.exists(img_path)
    finally:
        if os.path.exists(tmp_mmd):
            os.remove(tmp_mmd)


def _render_single_d2(code, img_path, d2_bin):
    """Render 1 block D2 → PNG. Trả về True nếu thành công."""
    tmp_d2 = os.path.join(tempfile.gettempdir(), f"d2_{os.getpid()}.d2")
    with open(tmp_d2, "w", encoding="utf-8") as f:
        f.write(code)
    try:
        result = subprocess.run(
            [d2_bin, "--layout=elk", tmp_d2, img_path],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0 and os.path.exists(img_path)
    finally:
        if os.path.exists(tmp_d2):
            os.remove(tmp_d2)


def render_diagrams(md_text, output_dir):
    """Tìm tất cả block ```mermaid và ```d2, render thành PNG, thay bằng ![img](path).
    
    Hỗ trợ mix: 1 file MD có thể chứa cả Mermaid lẫn D2.
    """
    
    # Tìm tất cả diagram blocks (mermaid hoặc d2)
    pattern = re.compile(r'```(mermaid|d2)\n(.*?)```', re.DOTALL)
    matches = list(pattern.finditer(md_text))
    
    if not matches:
        print("   ℹ️  Không có sơ đồ nào (Mermaid/D2).")
        return md_text, None
    
    # Đếm theo loại
    mermaid_count = sum(1 for m in matches if m.group(1) == 'mermaid')
    d2_count = sum(1 for m in matches if m.group(1) == 'd2')
    
    summary_parts = []
    if mermaid_count > 0:
        summary_parts.append(f"{mermaid_count} Mermaid")
    if d2_count > 0:
        summary_parts.append(f"{d2_count} D2")
    print(f"   📊 Tìm thấy {len(matches)} sơ đồ ({', '.join(summary_parts)}), đang render...")
    
    # Kiểm tra tools có sẵn
    mmdc = shutil.which("mmdc")
    d2_bin = shutil.which("d2")
    
    if mermaid_count > 0 and not mmdc:
        print("   ⚠️  mmdc không tìm thấy — bỏ qua Mermaid. Cài: npm install -g @mermaid-js/mermaid-cli")
    if d2_count > 0 and not d2_bin:
        print("   ⚠️  d2 không tìm thấy — bỏ qua D2. Cài: brew install d2")
    
    img_dir = os.path.join(output_dir, "diagram_images")
    os.makedirs(img_dir, exist_ok=True)
    
    # Mermaid config
    mmdc_config = os.path.join(tempfile.gettempdir(), "mermaid_config.json")
    if mmdc:
        with open(mmdc_config, "w") as f:
            f.write('{"theme": "default", "themeVariables": {"fontSize": "14px"}}')
    
    # Render từ cuối lên đầu (để index không bị lệch)
    for i, match in enumerate(reversed(matches), 1):
        diagram_type = match.group(1)  # 'mermaid' hoặc 'd2'
        diagram_code = match.group(2).strip()
        img_path = os.path.join(img_dir, f"diagram_{i}.png")
        label = f"Sơ đồ {i} [{diagram_type.upper()}]"
        
        try:
            success = False
            if diagram_type == 'mermaid' and mmdc:
                success = _render_single_mermaid(diagram_code, img_path, mmdc, mmdc_config)
            elif diagram_type == 'd2' and d2_bin:
                success = _render_single_d2(diagram_code, img_path, d2_bin)
            else:
                print(f"      ⏭️  {label} — bỏ qua (thiếu tool)")
                continue
            
            if success:
                img_ref = f"![{label}]({img_path})"
                md_text = md_text[:match.start()] + img_ref + md_text[match.end():]
                print(f"      ✅ {label} → OK")
            else:
                print(f"      ⚠️ {label} render thất bại")
        except subprocess.TimeoutExpired:
            print(f"      ⚠️ {label} timeout (>30s)")
        except Exception as e:
            print(f"      ❌ {label} lỗi: {e}")
    
    return md_text, img_dir


def apply_table_style(table):
    """Thêm border, tô header, full-width, xóa indent trong cell."""
    
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else parse_xml(f'<w:tblPr {nsdecls("w")} />')
    
    # ---- BORDERS ----
    borders_xml = f'''
    <w:tblBorders {nsdecls("w")}>
        <w:top w:val="single" w:sz="4" w:space="0" w:color="999999"/>
        <w:left w:val="single" w:sz="4" w:space="0" w:color="999999"/>
        <w:bottom w:val="single" w:sz="4" w:space="0" w:color="999999"/>
        <w:right w:val="single" w:sz="4" w:space="0" w:color="999999"/>
        <w:insideH w:val="single" w:sz="4" w:space="0" w:color="BBBBBB"/>
        <w:insideV w:val="single" w:sz="4" w:space="0" w:color="BBBBBB"/>
    </w:tblBorders>'''
    existing = tblPr.find(qn('w:tblBorders'))
    if existing is not None:
        tblPr.remove(existing)
    tblPr.append(parse_xml(borders_xml))
    
    # ---- Full width 100% ----
    tblW = tblPr.find(qn('w:tblW'))
    if tblW is None:
        tblW = parse_xml(f'<w:tblW {nsdecls("w")} w:w="5000" w:type="pct"/>')
        tblPr.append(tblW)
    else:
        tblW.set(qn('w:w'), '5000')
        tblW.set(qn('w:type'), 'pct')

    # ---- Xóa indent bảng ----
    tblInd = tblPr.find(qn('w:tblInd'))
    if tblInd is not None:
        tblPr.remove(tblInd)
    tblInd = parse_xml(f'<w:tblInd {nsdecls("w")} w:w="0" w:type="dxa"/>')
    tblPr.append(tblInd)

    # ---- FIXED layout (để explicit column width có hiệu lực) ----
    layout = tblPr.find(qn('w:tblLayout'))
    if layout is not None:
        tblPr.remove(layout)
    layout = parse_xml(f'<w:tblLayout {nsdecls("w")} w:type="fixed"/>')
    tblPr.append(layout)

    # ---- Xóa cell margin mặc định ----
    tblCellMar = tblPr.find(qn('w:tblCellMar'))
    if tblCellMar is not None:
        tblPr.remove(tblCellMar)

    # ---- HEADER ROW ----
    if len(table.rows) > 0:
        header_row = table.rows[0]
        for cell in header_row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            # Tô nền xanh đậm
            shading = parse_xml(
                f'<w:shd {nsdecls("w")} w:fill="1F4E79" w:val="clear"/>'
            )
            tcPr.append(shading)
            # Căn dọc lên trên (TOP)
            vAlign = parse_xml(f'<w:vAlign {nsdecls("w")} w:val="top"/>')
            tcPr.append(vAlign)
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                paragraph.paragraph_format.first_line_indent = Cm(0)
                for run in paragraph.runs:
                    run.bold = True
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                    run.font.size = Pt(12)
                    run.font.name = 'Times New Roman'

    # ---- DATA ROWS ----
    for row_idx, row in enumerate(table.rows):
        if row_idx == 0:
            continue
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.first_line_indent = Cm(0)
                for run in paragraph.runs:
                    run.font.size = Pt(12)
                    run.font.name = 'Times New Roman'
        
        # Zebra striping
        if row_idx % 2 == 0:
            for cell in row.cells:
                shading = parse_xml(
                    f'<w:shd {nsdecls("w")} w:fill="F2F7FB" w:val="clear"/>'
                )
                cell._tc.get_or_add_tcPr().append(shading)


# Từ khóa cột hẹp và rộng để nhận diện
NARROW_KEYWORDS = {'STT', 'SL', '#', 'SỐ LƯỢNG', 'ĐVT'}
WIDE_KEYWORDS = {'MÔ TẢ', 'MODEL', 'CHI TIẾT', 'NỘI DUNG', 'GHI CHÚ',
                  'HẠNG MỤC', 'THIẾT BỊ', 'MODEL / MÔ TẢ', 'THÔNG SỐ'}


def smart_column_widths(table, doc):
    """Phân tích nội dung từng cột, gán width DXA tỷ lệ hợp lý."""
    if len(table.rows) == 0 or len(table.columns) == 0:
        return
    
    # Tính độ rộng khả dụng (trang - lề trái - lề phải) theo DXA (1 inch = 1440 DXA)
    section = doc.sections[0]
    page_w = section.page_width or Cm(21)   # A4 default
    left_m = section.left_margin or Cm(2)
    right_m = section.right_margin or Cm(2)
    avail_width_dxa = int((page_w - left_m - right_m) / Emu(635))  # Emu to DXA: 1 DXA = 635 EMU
    
    num_cols = len(table.columns)
    headers = [table.rows[0].cells[i].text.strip().upper() for i in range(num_cols)]
    
    # Tính độ dài nội dung trung bình + max mỗi cột
    col_max_len = []
    for col_idx in range(num_cols):
        lengths = [len(headers[col_idx])]
        for row_idx, row in enumerate(table.rows):
            if row_idx == 0:
                continue
            if row_idx > 15:
                break
            text = row.cells[col_idx].text.strip()
            lengths.append(len(text))
        col_max_len.append(max(lengths))
    
    # Gán trọng số dựa trên nội dung
    MIN_PCT = 0.05  # cột hẹp nhất tối thiểu 5% page width
    MAX_PCT = 0.40  # cột rộng nhất tối đa 40% page width
    
    raw_weights = []
    for col_idx in range(num_cols):
        header = headers[col_idx]
        max_len = col_max_len[col_idx]
        
        if header in NARROW_KEYWORDS or max_len <= 5:
            w = 2.0  # hẹp nhưng vẫn đọc được
        elif any(kw in header for kw in WIDE_KEYWORDS) or max_len > 40:
            w = min(10.0, max(5.0, max_len / 5.0))  # rộng, cap 10
        elif max_len > 20:
            w = 4.0
        elif max_len > 10:
            w = 3.0
        else:
            w = 2.5
        raw_weights.append(w)
    
    # Áp dụng min/max cap theo phần trăm
    total_raw = sum(raw_weights)
    col_dxas = []
    for col_idx in range(num_cols):
        pct = raw_weights[col_idx] / total_raw
        pct = max(MIN_PCT, min(MAX_PCT, pct))  # clamp
        col_dxas.append(int(avail_width_dxa * pct))
    
    # Điều chỉnh tổng = avail_width_dxa (bù sai số do clamp)
    diff = avail_width_dxa - sum(col_dxas)
    max_col = col_dxas.index(max(col_dxas))
    col_dxas[max_col] += diff
    
    # ===== CẬP NHẬT tblGrid/gridCol (quan trọng nhất — Word dùng cái này) =====
    tbl = table._tbl
    old_grid = tbl.find(qn('w:tblGrid'))
    if old_grid is not None:
        tbl.remove(old_grid)
    new_grid = parse_xml(f'<w:tblGrid {nsdecls("w")}/>')
    for col_dxa in col_dxas:
        grid_col = parse_xml(f'<w:gridCol {nsdecls("w")} w:w="{col_dxa}"/>')
        new_grid.append(grid_col)
    tblPr = tbl.tblPr
    if tblPr is not None:
        tblPr.addnext(new_grid)
    else:
        tbl.insert(0, new_grid)
    
    # ===== Gán tcW cho từng cell để khớp =====
    for col_idx in range(num_cols):
        col_dxa = col_dxas[col_idx]
        for row in table.rows:
            cell = row.cells[col_idx]
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            old_tcW = tcPr.find(qn('w:tcW'))
            if old_tcW is not None:
                tcPr.remove(old_tcW)
            new_tcW = parse_xml(f'<w:tcW {nsdecls("w")} w:w="{col_dxa}" w:type="dxa"/>')
            tcPr.append(new_tcW)


def set_document_style(doc):
    """Font Times New Roman 12pt, justify, thụt đầu dòng, margin chuẩn."""
    
    FONT_NAME = 'Times New Roman'
    FONT_SIZE = Pt(12)
    
    # ---- Margins: 2cm trái-phải, 2cm trên-dưới ----
    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(2.0)
        section.right_margin = Cm(2.0)
    
    # ---- Default Normal style ----
    style = doc.styles['Normal']
    style.font.name = FONT_NAME
    style.font.size = FONT_SIZE
    pf = style.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = Cm(1.27)  # thụt đầu dòng
    pf.space_after = Pt(6)
    
    # ---- Heading styles ----
    for level in range(1, 5):
        style_name = f'Heading {level}'
        if style_name in doc.styles:
            hs = doc.styles[style_name]
            hs.font.name = FONT_NAME
            hs.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
            hs.paragraph_format.first_line_indent = Cm(0)  # heading không thụt
    
    # ---- List styles: không thụt đầu dòng ----
    for style_name in ['List Paragraph', 'List Bullet', 'List Number']:
        if style_name in doc.styles:
            ls = doc.styles[style_name]
            ls.font.name = FONT_NAME
            ls.paragraph_format.first_line_indent = Cm(0)
    
    # ---- Fix all paragraph fonts ----
    for para in doc.paragraphs:
        is_heading = para.style.name.startswith('Heading') or para.style.name == 'Title'
        is_list = 'List' in para.style.name
        
        # Heading và list: không thụt đầu dòng
        if is_heading or is_list:
            para.paragraph_format.first_line_indent = Cm(0)
        
        for run in para.runs:
            run.font.name = FONT_NAME
            if not is_heading:
                if run.font.size is None or run.font.size > Pt(14):
                    run.font.size = FONT_SIZE


def cleanup_temp_files(img_dir, tmp_md):
    """Dọn dẹp file tạm sau khi chuyển đổi xong."""
    cleaned = []
    
    # Xóa file MD tạm
    if tmp_md and os.path.exists(tmp_md):
        os.remove(tmp_md)
        cleaned.append("processed.md")
    
    # Xóa thư mục diagram_images
    if img_dir and os.path.exists(img_dir):
        file_count = len(os.listdir(img_dir))
        shutil.rmtree(img_dir)
        cleaned.append(f"diagram_images/ ({file_count} files)")
    
    if cleaned:
        print(f"   🧹 Đã dọn dẹp: {', '.join(cleaned)}")


def convert_md_to_docx(md_file, output_file=None):
    """Main conversion: MD → Mermaid render → Pandoc → Post-process → DOCX."""
    
    start_time = time.time()
    
    if output_file is None:
        output_file = md_file.rsplit('.', 1)[0] + '.docx'
    
    md_dir = os.path.dirname(os.path.abspath(md_file))
    img_dir = None
    tmp_md = os.path.join(tempfile.gettempdir(), "processed.md")
    
    print()
    print(f"{'=' * 60}")
    print(f"  md2docx — Chuyển Markdown sang Word")
    print(f"{'=' * 60}")
    print(f"  📂 Input:  {os.path.basename(md_file)}")
    print(f"  📄 Output: {os.path.basename(output_file)}")
    print(f"{'=' * 60}")
    print()

    try:
        # ── Step 1: Đọc file MD ──
        print("[1/5] 📖 Đọc file Markdown...")
        if not os.path.exists(md_file):
            raise FileNotFoundError(f"Không tìm thấy file: {md_file}")
        
        with open(md_file, 'r', encoding='utf-8') as f:
            md_text = f.read()
        print(f"   ✅ Đọc thành công ({len(md_text):,} ký tự)")

        # ── Step 2: Render diagrams (Mermaid + D2) ──
        print()
        print("[2/5] 🎨 Xử lý sơ đồ (Mermaid / D2)...")
        md_text_processed, img_dir = render_diagrams(md_text, md_dir)
        
        # Write processed MD to temp file
        with open(tmp_md, 'w', encoding='utf-8') as f:
            f.write(md_text_processed)

        # ── Step 3: Pandoc convert ──
        print()
        print("[3/5] 📄 Chạy Pandoc (MD → DOCX thô)...")
        pandoc = shutil.which("pandoc")
        if not pandoc:
            raise FileNotFoundError("Pandoc chưa được cài. Cài bằng: brew install pandoc")
        
        result = subprocess.run(
            [pandoc, tmp_md, "-o", output_file, "--from", "markdown", "--to", "docx"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Pandoc lỗi: {result.stderr}")
        print("   ✅ Pandoc chuyển đổi thành công")

        # ── Step 4: Post-process với python-docx ──
        print()
        print("[4/5] 🎨 Post-process (bảng, font, style, header)...")
        doc = Document(output_file)
        
        # Set document-level styles
        set_document_style(doc)
        print("   ✅ Font, margin, indent đã set")
        
        # Thêm header công ty
        add_company_header(doc)
        print(f"   ✅ Header công ty: {COMPANY_NAME} | {COMPANY_HOTLINE} | {COMPANY_WEBSITE}")
        
        # Process all tables
        table_count = len(doc.tables)
        for table in doc.tables:
            apply_table_style(table)
            smart_column_widths(table, doc)
            table.alignment = WD_TABLE_ALIGNMENT.LEFT
        print(f"   ✅ Đã format {table_count} bảng (border, header, zebra, auto-width)")
        
        # Save
        doc.save(output_file)
        print(f"   ✅ Đã lưu: {output_file}")

        # ── Step 5: Dọn dẹp ──
        print()
        print("[5/5] 🧹 Dọn dẹp file tạm...")
        cleanup_temp_files(img_dir, tmp_md)

        # ── Hoàn tất ──
        elapsed = time.time() - start_time
        print()
        print(f"{'=' * 60}")
        print(f"  ✅ HOÀN TẤT trong {elapsed:.1f}s")
        print(f"  📄 {output_file}")
        print(f"  📊 {table_count} bảng đã format")
        print(f"{'=' * 60}")
        print()

    except FileNotFoundError as e:
        print(f"\n❌ LỖI — File không tìm thấy: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"\n❌ LỖI — Runtime: {e}")
        cleanup_temp_files(img_dir, tmp_md)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ LỖI KHÔNG XÁC ĐỊNH: {type(e).__name__}: {e}")
        cleanup_temp_files(img_dir, tmp_md)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cách dùng: md2docx <file.md> [output.docx]")
        print("Ví dụ:     md2docx bao_gia.md")
        print("           md2docx bao_gia.md output.docx")
        sys.exit(1)
    
    md_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    convert_md_to_docx(md_file, output_file)
