---
name: asset_management
version: 1.0.0
description: "Bộ công cụ quản lý ROM game và tự động hóa việc tải/sửa ảnh bìa."
tools:
  - name: fix_cover_art
    description: "Quét thư mục ROM, đối chiếu với thư mục Logos, và tải ảnh bìa còn thiếu từ Libretro."
    executable: python3
    arguments:
      - "scripts/fix_cover.py"
      - "--system"
      - "{system_name}"
      - "--fuzzy" # Bật chế độ tìm kiếm gần đúng
    env:
      PYTHONIOENCODING: "utf-8"

  - name: generate_gamelist
    description: "Quét toàn bộ thư mục public/roms và tái tạo file gamelist.json."
    executable: python3
    arguments:
      - "scripts/generate_list.py"
