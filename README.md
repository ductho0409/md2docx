# md2docx — Chuyển Markdown sang Word (.docx) chuyên nghiệp

Công cụ chuyển đổi file Markdown (.md) thành Word (.docx) với chất lượng cao, sẵn sàng gửi khách hàng hoặc in ấn. Khắc phục toàn bộ hạn chế của pandoc mặc định.

> **SETCOM** — Công ty TNHH Dịch vụ và Thiết bị Khoa học Setcom  
> Website: [setcom.com.vn](https://setcom.com.vn) | Hotline: 0913 425 986

## Tính năng

| Tính năng | Mô tả |
|---|---|
| **Bảng biểu đẹp** | Border đầy đủ, header nền xanh đậm/chữ trắng/bold, zebra striping dòng chẵn |
| **Auto-sizing cột** | Phân tích nội dung + header keyword → cột hẹp (STT, SL, ĐVT) min 5%, cột rộng (Model, Mô tả) max 40% |
| **Bảng full-width** | Bảng căn sát lề 2 bên, chiếm 100% trang |
| **Font chuẩn VN** | Times New Roman 12pt cho toàn bộ document |
| **Justify + thụt đầu dòng** | Đoạn văn justify, thụt 1.27cm. Heading và list thì không thụt |
| **Mermaid → ảnh** | Tự phát hiện block ` ```mermaid `, render PNG bằng `mmdc`, chèn vào Word |
| **Heading style** | Heading 1–4 có màu xanh đậm (#1F4E79) |
| **Header công ty** | Mỗi trang có header: SETCOM \| Hotline \| Website |
| **Dọn dẹp tự động** | Xóa file tạm (mermaid_images/, processed.md) sau khi xong |
| **Error handling** | Try/catch đầy đủ, log chi tiết từng bước trong terminal |

## Cài đặt

### Cách 1: Clone từ GitHub

```bash
# Clone repo
git clone https://github.com/<username>/md2docx.git
cd md2docx

# Tạo virtual environment và cài dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# (Tùy chọn) Thêm vào PATH để dùng từ mọi nơi
echo 'export PATH="'$(pwd)':$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Yêu cầu hệ thống

| Tool | Cài bằng | Mục đích |
|---|---|---|
| `pandoc` | `brew install pandoc` | Chuyển MD → docx thô |
| `mmdc` (mermaid-cli) | `npm install -g @mermaid-js/mermaid-cli` | Render sơ đồ Mermaid → PNG |
| `python-docx` | `pip install -r requirements.txt` | Post-process docx |

## Cách dùng

```bash
# Chuyển đổi cơ bản (tạo file.docx cùng thư mục)
md2docx file.md

# Chỉ định tên output
md2docx file.md output.docx
```

### Output trong terminal

```
============================================================
  md2docx — Chuyển Markdown sang Word
============================================================
  📂 Input:  file.md
  📄 Output: file.docx
============================================================

[1/5] 📖 Đọc file Markdown...
   ✅ Đọc thành công (12,345 ký tự)

[2/5] 🎨 Xử lý sơ đồ Mermaid...
   📊 Tìm thấy 2 sơ đồ Mermaid, đang render...
      ✅ Sơ đồ 1 → OK
      ✅ Sơ đồ 2 → OK

[3/5] 📄 Chạy Pandoc (MD → DOCX thô)...
   ✅ Pandoc chuyển đổi thành công

[4/5] 🎨 Post-process (bảng, font, style, header)...
   ✅ Font, margin, indent đã set
   ✅ Header công ty: SETCOM | 0913 425 986 | setcom.com.vn
   ✅ Đã format 5 bảng (border, header, zebra, auto-width)
   ✅ Đã lưu: file.docx

[5/5] 🧹 Dọn dẹp file tạm...
   🧹 Đã dọn dẹp: processed.md, mermaid_images/ (2 files)

============================================================
  ✅ HOÀN TẤT trong 3.2s
  📄 file.docx
  📊 5 bảng đã format
============================================================
```

## Cấu trúc dự án

```
md2docx/
├── README.md              ← File này
├── convert_to_docx.py     ← Script Python chính
├── md2docx                ← Shell wrapper (gọi Python từ venv)
├── requirements.txt       ← Python dependencies
├── .gitignore             ← Git ignore rules
└── venv/                  ← Python virtual environment (không track trong git)
```

## Kiến trúc xử lý

```
Input: file.md
  │
  ├─ 1. Tìm block ```mermaid → render PNG bằng mmdc
  │     (hàm render_mermaid_diagrams)
  │
  ├─ 2. Thay block mermaid bằng ![image](path) trong MD
  │
  ├─ 3. Pandoc chuyển MD đã xử lý → docx thô
  │
  ├─ 4. python-docx post-process:
  │     ├─ set_document_style()      → Font, margin, justify, indent
  │     ├─ add_company_header()      → Header SETCOM trên mỗi trang
  │     ├─ apply_table_style()       → Border, header, zebra, full-width
  │     └─ smart_column_widths()     → Phân tích nội dung → gán gridCol DXA
  │
  └─ 5. cleanup_temp_files()        → Xóa mermaid_images/ và file tạm
Output: file.docx
```

## Chi tiết kỹ thuật

### Column width (vấn đề phức tạp nhất)

Word dùng `tblGrid/gridCol` để quyết định độ rộng cột, **KHÔNG** dùng `tcW`. Pandoc tạo `gridCol` bằng nhau → phải xóa và ghi lại.

**Logic auto-sizing:**
- Đọc header text → match keyword (NARROW_KEYWORDS / WIDE_KEYWORDS)
- Đo max content length từ 15 dòng đầu
- Gán weight → clamp min 5%, max 40% → tính DXA
- Ghi vào cả `gridCol` VÀ `tcW` để đồng bộ

### Table layout

Dùng `tblLayout type="fixed"` (không phải "autofit") để Word tôn trọng explicit column width.

### First-line indent

Set ở Normal style (1.27cm) nhưng phải **xóa** ở: Heading, List, Table cell.

### Header công ty

Sử dụng `section.header` của python-docx, format: **SETCOM** | Hotline: 0913 425 986 | setcom.com.vn. Font 8pt, màu xám, có đường kẻ dưới.

## Cách cập nhật / bảo trì

- **Sửa logic**: Edit `convert_to_docx.py`
- **Đổi thông tin công ty**: Sửa các biến `COMPANY_*` ở đầu script
- **Thêm keyword cột hẹp/rộng**: Sửa `NARROW_KEYWORDS` / `WIDE_KEYWORDS`
- **Đổi font/margin**: Sửa hàm `set_document_style()`
- **Đổi màu header bảng**: Sửa `w:fill="1F4E79"` trong `apply_table_style()`
- **Cài thêm Python package**: `source venv/bin/activate && pip install <package>`
- **Nếu venv hỏng**: Xóa `venv/`, tạo lại: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
