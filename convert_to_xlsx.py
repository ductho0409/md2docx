#!/usr/bin/env python3
"""
Script chuyển Markdown → Excel (.xlsx) với format chuyên nghiệp.
- Layout document-style: text → merged row, bảng → Excel table
- Heading sizing theo level (H1 > H2 > H3)
- Bảng: header xanh đậm, zebra, border, số căn phải
- Print-ready: A4, lề 2cm, header công ty, fit-to-page
"""

import os
import re
import sys
import time
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side,
    GradientFill
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins
from openpyxl.drawing.image import Image as XLImage

# ── Thông tin công ty ──────────────────────────────────────────────
COMPANY_NAME    = "SETCOM"
COMPANY_FULL    = "Công ty TNHH Dịch vụ và Thiết bị Khoa học Setcom"
COMPANY_HOTLINE = "0913 425 986"
COMPANY_WEBSITE = "setcom.com.vn"
COMPANY_EMAIL   = "info@setcom.com.vn"

# ── Màu sắc ────────────────────────────────────────────────────────
COLOR_HEADER    = "1F4E79"   # Xanh đậm header bảng + H1
COLOR_H2        = "2E75B6"   # Xanh vừa H2
COLOR_H3        = "404040"   # Xám đậm H3
COLOR_ZEBRA     = "EBF3FB"   # Xanh nhạt zebra
COLOR_BORDER    = "AAAAAA"   # Xám viền bảng
COLOR_WHITE     = "FFFFFF"
COLOR_BG_HEADER = "F0F4FA"   # Nền hàng header công ty

# ── Cố định số cột (A4 = 17cm = ~9 cột nếu mỗi cột 1.9cm) ─────────
TOTAL_COLS = 9   # Tổng cột trang, dùng để merge text


# ──────────────────────────────────────────────────────────────────
#  PARSE MD BLOCKS
# ──────────────────────────────────────────────────────────────────

def parse_md_blocks(md_text):
    """
    Phân tích Markdown thành list of blocks:
    {type: heading|paragraph|table|blank, level, content, headers, rows}
    """
    blocks = []
    lines = md_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # ── Blank line ──
        if line.strip() == '':
            blocks.append({'type': 'blank'})
            i += 1
            continue

        # ── Horizontal rule (---) → spacing block ──
        if re.match(r'^[-_*]{3,}\s*$', line.strip()):
            blocks.append({'type': 'blank'})
            blocks.append({'type': 'blank'})
            i += 1
            continue

        # ── Heading ──
        heading_match = re.match(r'^(#{1,6})\s+(.+)', line)
        if heading_match:
            level = len(heading_match.group(1))
            content = heading_match.group(2).strip()
            blocks.append({'type': 'heading', 'level': level, 'content': content})
            i += 1
            continue

        # ── Table ── (phát hiện từ dòng header | separator | rows)
        if '|' in line:
            # Thu thập các dòng của bảng
            table_lines = []
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1

            # Parse header + separator + rows
            if len(table_lines) >= 2:
                # Dòng header
                header_cells = _parse_table_row(table_lines[0])

                # Bỏ dòng separator (---)
                data_start = 1
                if len(table_lines) > 1 and re.match(r'^\|[-| :]+\|', table_lines[1].strip()):
                    data_start = 2

                # Data rows
                data_rows = [_parse_table_row(l) for l in table_lines[data_start:]]

                blocks.append({
                    'type': 'table',
                    'headers': header_cells,
                    'rows': data_rows,
                })
            continue

        # ── Paragraph ──
        # Thu thập các dòng liên tiếp (không phải blank/heading/table)
        para_lines = []
        while i < len(lines):
            l = lines[i]
            if l.strip() == '':
                break
            if re.match(r'^#{1,6}\s', l):
                break
            if '|' in l:
                break
            para_lines.append(l.strip())
            i += 1

        if para_lines:
            content = ' '.join(para_lines)
            # Detect list items
            if re.match(r'^[-*+]\s', para_lines[0]) or re.match(r'^\d+\.\s', para_lines[0]):
                # Giữ dạng list, join bằng newline
                content = '\n'.join(para_lines)
                blocks.append({'type': 'list', 'content': content})
            else:
                blocks.append({'type': 'paragraph', 'content': content})

    return blocks


def _parse_table_row(line):
    """Parse 1 dòng bảng Markdown thành list cells."""
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    cells = [c.strip() for c in line.split('|')]
    return cells


def _is_numeric_cell(text):
    """Kiểm tra cell chứa chủ yếu là số."""
    if not text:
        return False
    cleaned = text.replace(' ', '').replace('\n', '')
    if not cleaned:
        return False
    numeric_chars = sum(1 for c in cleaned if c in '0123456789.,đ₫%×xX+-')
    return len(cleaned) > 0 and numeric_chars / len(cleaned) > 0.5


def _strip_md(text):
    """Bỏ markdown formatting: **bold**, *italic*, `code`, [link](url)."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    return text


# ──────────────────────────────────────────────────────────────────
#  STYLES HELPERS
# ──────────────────────────────────────────────────────────────────

def _border(color=COLOR_BORDER, style='thin'):
    side = Side(style=style, color=color)
    return Border(left=side, right=side, top=side, bottom=side)


def _fill(hex_color):
    return PatternFill(fill_type='solid', fgColor=hex_color)


def _font(name='Times New Roman', size=12, bold=False, italic=False, color='000000'):
    return Font(name=name, size=size, bold=bold, italic=italic, color=color)


def _align(horizontal='left', vertical='top', wrap=True):
    return Alignment(horizontal=horizontal, vertical=vertical, wrap_text=wrap)


# ──────────────────────────────────────────────────────────────────
#  COMPANY HEADER
# ──────────────────────────────────────────────────────────────────

def add_company_header(ws):
    """Thêm 2 hàng header công ty ở đầu sheet."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(script_dir, 'assets', 'logo.png')

    # Row 1: Logo bên trái + tên công ty bên phải
    ws.row_dimensions[1].height = 35

    # Cột A-B: Logo (hoặc tên nếu không có logo)
    logo_cell = ws.cell(row=1, column=1)
    if os.path.exists(logo_path):
        try:
            img = XLImage(logo_path)
            img.height = 45
            img.width = 120
            ws.add_image(img, 'A1')
        except Exception:
            logo_cell.value = COMPANY_NAME
            logo_cell.font = _font(size=14, bold=True, color=COLOR_HEADER)
    else:
        # Fallback base64
        try:
            import base64
            from logo_data import LOGO_BASE64
            import tempfile
            tmp = os.path.join(tempfile.gettempdir(), 'setcom_logo.png')
            with open(tmp, 'wb') as f:
                f.write(base64.b64decode(LOGO_BASE64))
            img = XLImage(tmp)
            img.height = 45
            img.width = 120
            ws.add_image(img, 'A1')
        except Exception:
            logo_cell.value = COMPANY_NAME
            logo_cell.font = _font(size=14, bold=True, color=COLOR_HEADER)

    # Merge A1:C1 cho logo
    ws.merge_cells(f'A1:C1')

    # Cột D-I: Tên công ty + thông tin liên hệ
    ws.merge_cells(f'D1:{get_column_letter(TOTAL_COLS)}1')
    info_cell = ws.cell(row=1, column=4)
    info_cell.value = (
        f"{COMPANY_FULL}\n"
        f"☎ {COMPANY_HOTLINE}    ✉ {COMPANY_EMAIL}    🌐 {COMPANY_WEBSITE}"
    )
    info_cell.font = _font(size=8, bold=False, color=COLOR_HEADER)
    info_cell.alignment = Alignment(horizontal='right', vertical='center', wrap_text=True)

    # Tô nền row 1
    for col in range(1, TOTAL_COLS + 1):
        ws.cell(row=1, column=col).fill = _fill(COLOR_BG_HEADER)

    # Row 2: Đường kẻ xanh đậm phân cách
    ws.row_dimensions[2].height = 4
    for col in range(1, TOTAL_COLS + 1):
        c = ws.cell(row=2, column=col)
        c.fill = _fill(COLOR_HEADER)

    return 3  # Row tiếp theo để bắt đầu nội dung


# ──────────────────────────────────────────────────────────────────
#  RENDER BLOCKS
# ──────────────────────────────────────────────────────────────────

def render_heading(ws, row, level, content):
    """Render 1 heading vào 1 merged row."""
    # Config theo level
    config = {
        1: {'size': 16, 'bold': True,  'italic': False, 'color': COLOR_HEADER, 'height': 36},
        2: {'size': 14, 'bold': True,  'italic': False, 'color': COLOR_H2,     'height': 26},
        3: {'size': 12, 'bold': True,  'italic': True,  'color': COLOR_H3,     'height': 22},
        4: {'size': 12, 'bold': True,  'italic': False, 'color': COLOR_H3,     'height': 20},
        5: {'size': 11, 'bold': False, 'italic': True,  'color': COLOR_H3,     'height': 18},
        6: {'size': 11, 'bold': False, 'italic': False, 'color': COLOR_H3,     'height': 16},
    }
    cfg = config.get(level, config[3])

    # Padding trái theo level
    pad = '  ' * (level - 1)
    text = _strip_md(content)

    ws.merge_cells(f'A{row}:{get_column_letter(TOTAL_COLS)}{row}')
    cell = ws.cell(row=row, column=1)
    cell.value = f"{pad}{text}"
    cell.font = _font(size=cfg['size'], bold=cfg['bold'],
                      italic=cfg['italic'], color=cfg['color'])
    cell.alignment = _align(horizontal='left', vertical='center', wrap=False)
    ws.row_dimensions[row].height = cfg['height']

    # Underline nhẹ cho H1, H2
    if level <= 2:
        bottom_side = Side(style='medium', color=cfg['color'])
        cell.border = Border(bottom=bottom_side)

    return row + 1


def render_paragraph(ws, row, content, is_list=False):
    """Render đoạn văn vào 1 merged row, wrap text."""
    text = _strip_md(content)
    if not text.strip():
        return row

    ws.merge_cells(f'A{row}:{get_column_letter(TOTAL_COLS)}{row}')
    cell = ws.cell(row=row, column=1)
    cell.value = text
    cell.font = _font(size=12)
    cell.alignment = _align(horizontal='justify' if not is_list else 'left',
                             vertical='top', wrap=True)

    # Ước tính chiều cao: 15px mỗi dòng ~50 ký tự
    chars_per_line = 90  # Ước tính cho A4 width
    num_lines = max(1, len(text) // chars_per_line + text.count('\n') + 1)
    ws.row_dimensions[row].height = max(16, min(num_lines * 15, 120))

    return row + 1


def render_blank(ws, row, height=8):
    """Render dòng trống (khoảng cách)."""
    ws.row_dimensions[row].height = height
    return row + 1


def render_table(ws, row, headers, rows):
    """Render bảng Markdown thành Excel table có style đầy đủ."""
    if not headers:
        return row

    num_cols = len(headers)

    # ── Tính độ rộng cột (nội dung + header) ──
    col_widths = [max(len(str(h)), 4) for h in headers]
    for data_row in rows[:20]:  # Lấy tối đa 20 dòng để estimate
        for ci, cell_val in enumerate(data_row):
            if ci < num_cols:
                col_widths[ci] = max(col_widths[ci], len(str(cell_val)))

    # ── Nhận diện cột số ──
    col_is_numeric = [False] * num_cols
    for data_row in rows[:10]:
        for ci, cell_val in enumerate(data_row):
            if ci < num_cols and _is_numeric_cell(str(cell_val)):
                col_is_numeric[ci] = True

    # ── Header row ──
    ws.row_dimensions[row].height = 20
    for ci, header in enumerate(headers):
        col_idx = ci + 1
        cell = ws.cell(row=row, column=col_idx)
        cell.value = _strip_md(str(header))
        cell.font = _font(size=11, bold=True, color=COLOR_WHITE)
        cell.fill = _fill(COLOR_HEADER)
        cell.alignment = _align(horizontal='center', vertical='top', wrap=True)
        cell.border = _border(color='FFFFFF', style='thin')

    header_row = row
    row += 1

    # ── Data rows ──
    for ri, data_row in enumerate(rows):
        ws.row_dimensions[row].height = 16
        is_zebra = (ri % 2 == 0)

        # Đảm bảo luôn đủ số cột
        padded_row = list(data_row) + [''] * (num_cols - len(data_row))

        for ci in range(num_cols):
            cell_val = padded_row[ci] if ci < len(padded_row) else ''
            numeric = col_is_numeric[ci]

            cell = ws.cell(row=row, column=ci + 1)
            cell.value = _strip_md(str(cell_val))
            cell.font = _font(size=11)
            cell.alignment = _align(
                horizontal='right' if numeric else 'left',
                vertical='top', wrap=not numeric
            )
            cell.border = _border()
            if is_zebra:
                cell.fill = _fill(COLOR_ZEBRA)

            # Number format cho số tiền
            if numeric and cell_val:
                clean = str(cell_val).replace('.', '').replace(',', '')
                if clean.isdigit():
                    try:
                        cell.value = int(clean)
                        cell.number_format = '#,##0'
                    except Exception:
                        pass

        row += 1

    # ── Thiết lập column widths ──
    # Map col_widths vào actual worksheet column letters
    # Cần tính toán cột nào trong sheet ứng với cột nào trong bảng
    # Bảng bắt đầu từ cột A (1)
    for ci, w in enumerate(col_widths):
        col_letter = get_column_letter(ci + 1)
        current = ws.column_dimensions[col_letter].width
        # Chỉ mở rộng, không thu hẹp cột đã đủ rộng
        target = min(max(w + 3, 8), 40)  # 8 min, 40 max
        if target > current:
            ws.column_dimensions[col_letter].width = target

    # Spacing sau bảng
    return row


# ──────────────────────────────────────────────────────────────────
#  PAGE SETUP
# ──────────────────────────────────────────────────────────────────

def setup_page(ws, last_row):
    """Thiết lập trang in A4, lề 2cm, header/footer công ty."""
    from openpyxl.worksheet.header_footer import HeaderFooter

    # A4
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = 'portrait'
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0  # Nhiều trang dọc nếu cần

    # Lề 2cm (1 inch ≈ 2.54cm, 2cm ≈ 0.787 inch)
    ws.page_margins = PageMargins(
        left=0.787, right=0.787,
        top=0.984, bottom=0.787,
        header=0.315, footer=0.315
    )

    # Print header: tên công ty + số trang
    ws.oddHeader.center.text = f"{COMPANY_FULL}"
    ws.oddHeader.center.font = "Times New Roman,Italic"
    ws.oddHeader.center.size = 8

    ws.oddFooter.left.text = f"{COMPANY_WEBSITE}"
    ws.oddFooter.center.text = "Trang &P / &N"
    ws.oddFooter.right.text = f"☎ {COMPANY_HOTLINE}"

    # Print area
    ws.print_area = f"A1:{get_column_letter(TOTAL_COLS)}{last_row}"

    # Freeze row 3 (sau 2 row header công ty)
    ws.freeze_panes = 'A3'

    # Lặp lại 2 hàng header khi in nhiều trang
    ws.print_title_rows = '1:2'

    # Set column widths mặc định nếu chưa set
    for i in range(1, TOTAL_COLS + 1):
        letter = get_column_letter(i)
        if ws.column_dimensions[letter].width < 8:
            ws.column_dimensions[letter].width = 12


# ──────────────────────────────────────────────────────────────────
#  MAIN CONVERSION
# ──────────────────────────────────────────────────────────────────

def convert_md_to_xlsx(md_file, output_file=None):
    """Main: Markdown → XLSX document-style."""

    start_time = time.time()

    # Xác định output path
    md_file = os.path.abspath(md_file)
    if output_file is None:
        output_file = os.path.splitext(md_file)[0] + '.xlsx'
    else:
        output_file = os.path.abspath(output_file)

    print()
    print('=' * 60)
    print('  md2xlsx — Chuyển Markdown sang Excel')
    print('=' * 60)
    print(f'  📂 Input:  {os.path.basename(md_file)}')
    print(f'  📄 Output: {os.path.basename(output_file)}')
    print('=' * 60)
    print()

    # ── Step 1: Đọc file ──
    print('[1/3] 📖 Đọc file Markdown...')
    if not os.path.exists(md_file):
        raise FileNotFoundError(f'Không tìm thấy file: {md_file}')
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()
    print(f'   ✅ Đọc thành công ({len(md_text):,} ký tự)')

    # ── Step 2: Parse blocks ──
    print()
    print('[2/3] 🔍 Phân tích cấu trúc...')
    blocks = parse_md_blocks(md_text)

    # Thống kê
    n_headings   = sum(1 for b in blocks if b['type'] == 'heading')
    n_paragraphs = sum(1 for b in blocks if b['type'] in ('paragraph', 'list'))
    n_tables     = sum(1 for b in blocks if b['type'] == 'table')
    print(f'   📊 {n_headings} heading, {n_paragraphs} đoạn văn, {n_tables} bảng')

    # ── Step 3: Tạo Excel ──
    print()
    print('[3/3] 🎨 Tạo file Excel...')

    wb = Workbook()
    ws = wb.active
    ws.title = 'Nội dung'

    # Header công ty
    current_row = add_company_header(ws)
    print(f'   ✅ Header công ty: {COMPANY_NAME} | {COMPANY_HOTLINE}')

    # Render từng block
    table_count = 0
    for block in blocks:
        btype = block['type']

        if btype == 'blank':
            current_row = render_blank(ws, current_row)

        elif btype == 'heading':
            current_row = render_heading(ws, current_row,
                                         block['level'], block['content'])

        elif btype in ('paragraph', 'list'):
            current_row = render_paragraph(ws, current_row,
                                           block['content'],
                                           is_list=(btype == 'list'))

        elif btype == 'table':
            # Spacing trước bảng
            current_row = render_blank(ws, current_row, height=6)
            current_row = render_table(ws, current_row,
                                       block['headers'], block['rows'])
            # Spacing sau bảng
            current_row = render_blank(ws, current_row, height=6)
            table_count += 1

    print(f'   ✅ Đã render {table_count} bảng, {current_row - 3} rows tổng')

    # Page setup
    setup_page(ws, current_row)

    # Lưu file
    wb.save(output_file)
    elapsed = time.time() - start_time
    print(f'   ✅ Đã lưu: {output_file}')

    print()
    print('=' * 60)
    print(f'  ✅ HOÀN TẤT trong {elapsed:.1f}s')
    print(f'  📊 {output_file}')
    print(f'  📋 {table_count} bảng | {n_headings} heading | {n_paragraphs} đoạn')
    print('=' * 60)
    print()

    return output_file


# ──────────────────────────────────────────────────────────────────
#  CLI ENTRY POINT
# ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Dùng: python3 convert_to_xlsx.py <file.md> [output.xlsx]')
        sys.exit(1)

    md_input = sys.argv[1]
    output   = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        convert_md_to_xlsx(md_input, output)
    except Exception as e:
        print(f'\n❌ Lỗi: {e}')
        sys.exit(1)
