---
trigger: glob
description: "Quy chuẩn đặt tên và cấu trúc thư mục cho ROMs và Thumbnails."
globs: ["public/data/**/*", "scripts/*.py"]
---

# ASSET NAMING & STRUCTURE

## Directory Map
- `public/roms/{system}/`: Chứa file game (ví dụ: `public/roms/nes/Mario.nes`).
- `public/logos/{system}/`: Chứa ảnh bìa (ví dụ: `public/logos/nes/Mario.png`).
- `public/data/gamelist.json`: Cơ sở dữ liệu trung tâm.

## Naming Protocol
1. **Filename Matching**: Tên file ảnh (trừ đuôi mở rộng) PHẢI trùng khớp chính xác từng ký tự với tên file ROM.
2. **Special Characters**: Các ký tự đặc biệt như `&`, `*`, `/`, `:`,, `<`, `>`, `?`, `\` phải được thay thế bằng dấu gạch dưới `_` trong tên file ảnh, tuân thủ chuẩn Libretro.
3. **Synchronization**: Agent không được phép đổi tên file ROM thủ công mà không cập nhật lại ảnh bìa tương ứng. Mọi sự thay đổi phải thông qua skill `manage_assets`.

## Libretro Fallback
- Khi tìm kiếm ảnh bìa từ nguồn bên ngoài, ưu tiên repository `libretro-thumbnails`. Sử dụng nhánh `master`, thư mục `Named_Boxarts`.