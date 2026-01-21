---
description: "Workflow: Ingest New Game. Adds games, matches covers, and updates JSON."
trigger: "User upload ROMs or ask to add game"
---
# Workflow: Ingest New Game

## Trigger
Người dùng upload một hoặc nhiều file ROM mới vào thư mục `public/roms/{system}/`.

## Execution Steps

### 1. Validation (Kiểm tra Tiền điều kiện)
- Kiểm tra phần mở rộng file có phù hợp với hệ máy không (ví dụ: `.nes` cho NES, `.sfc` cho SNES).
- **Rule Check**: Đảm bảo tên file không chứa ký tự gây lỗi URL.

### 2. Asset Normalization (Chuẩn hóa Tài sản)
- Gọi Skill `asset_manager.fix_cover_art` với tham số hệ máy tương ứng.
- **Insight**: Bước này đảm bảo rằng ngay cả khi người dùng chỉ ném file ROM vào, hệ thống sẽ tự động đi tìm ảnh bìa từ Libretro server. Agent cần giám sát output của script Python để báo cáo bao nhiêu ảnh bìa đã được fix.

### 3. Database Regeneration (Tái tạo CSDL)
- Gọi Skill `asset_manager.generate_gamelist`.
- Script này sẽ quét lại toàn bộ cây thư mục và tạo ra file JSON mới.
- **Constraint**: JSON output phải chứa trường `crc32` để hỗ trợ việc match thumbnail chính xác hơn trong tương lai.

### 4. Cache Busting Verification (Kiểm tra Cache)
- Agent kiểm tra code frontend (`src/main.js` hoặc tương đương).
- Đảm bảo logic gọi `gamelist.json` có chứa tham số `?v=` hoặc `?t=`. Nếu chưa có, Agent phải tự động refactor code JS để thêm vào (tuân thủ Rule 02).

### 5. User Report
- Báo cáo kết quả: "Đã thêm X game. Đã tải Y ảnh bìa. Database đã cập nhật."
