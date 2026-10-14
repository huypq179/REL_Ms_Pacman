# Hướng dẫn Đăng tải Paper lên Overleaf

## ✅ Các file sẵn sàng

### Option 1: **Standalone (Khuyến nghị cho Overleaf)**
- **File**: `docs/paper_overleaf.tex`
- **Ưu điểm**: Không cần external references, compile ngay
- **Cách dùng**:
  1. Copy nội dung của `paper_overleaf.tex`
  2. Dán vào Overleaf main.tex
  3. Compile (Ctrl+Enter)

### Option 2: **Với References BibTeX (Nếu muốn tham khảo)** 
- **Files**:
  - `docs/paper.tex` (version gốc)
  - `docs/references.bib`
- **Cách dùng**:
  1. Upload cả 2 file lên Overleaf
  2. Đặt `paper.tex` làm main file
  3. Compiler: XeLaTeX hoặc pdfLaTeX
  4. BibTeX: "Bibliography tool" → "BibTeX" (Overleaf sẽ tự detect)

## ❌ Vấn đề gốc (đã sửa)
- ❌ `\usepackage[utf-8]{inputenc}` → xóa bỏ (Overleaf mặc định UTF-8)
- ❌ Citations không resolve → thêm `references.bib`

## 📋 Các tài liệu liên quan

| File | Mục đích | Lưu ý |
|------|---------|-------|
| `docs/REPORT.md` | Báo cáo chi tiết (markdown) | Có thể convert → LaTeX nếu cần |
| `docs/presentation.pptx` | Slide thuyết trình | 18 slides, sẵn sàng |
| `README.md` | Tổng quan dự án | Hướng dẫn setup & training |

## 🚀 Nhanh nhất: Copy-Paste vào Overleaf

```
1. Mở: https://www.overleaf.com/
2. Tạo project mới → Blank Project
3. Xóa nội dung main.tex mặc định
4. Copy toàn bộ nội dung từ paper_overleaf.tex
5. Paste vào main.tex ở Overleaf
6. Nhấn Compile → ✅ PDF sẽ được tạo
```

## 📝 Nếu muốn chỉnh sửa

- **Thêm figure**: Sử dụng `\includegraphics{...}` (upload ảnh lên Overleaf trước)
- **Thêm table**: Copy bảng LaTeX từ `paper_overleaf.tex` làm template
- **Thay đổi references**: Chỉnh sửa `\begin{thebibliography}....\end{thebibliography}` section

## ✨ Kết quả

Overleaf sẽ compile ra PDF với:
- ✅ Tiêu đề, tác giả, ngày tháng
- ✅ Abstract với 5 đoạn
- ✅ 7 sections: Introduction, Related Work, Methodology, Results, Discussion, Conclusion
- ✅ Table & references
- ✅ Tất cả công thức toán học
- ✅ Code listings (Python)
- ✅ Hyperlinks hoạt động

---

**Chọn `paper_overleaf.tex` để nhanh nhất! 🚀**
