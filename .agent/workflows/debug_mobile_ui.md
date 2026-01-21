---
description: "Workflow: Debug Mobile UI Issues. Handles notch, safe-areas, and viewports."
trigger: "User report mobile/iOS issues"
---
# Workflow: Debug Mobile UI Issues

## Trigger
User báo cáo lỗi: "Bị mất hình ở cạnh", "Thanh trắng ở dưới đáy màn hình", "Không bấm được nút Start".

## Diagnostic Steps (Các bước chẩn đoán)

### 1. Check Meta Tags
- Mở `index.html`.
- Tìm: `<meta name="viewport">`.
- **Verify**: Có `viewport-fit=cover` không? Nếu không -> **FIX NGAY**. Đây là nguyên nhân số 1 gây ra lỗi viền trắng.

### 2. Check CSS Environment Variables
- Mở file CSS hoặc component style.
- Kiểm tra các class liên quan đến container game (`#game`, `.game-active`).
- **Verify**: Có sử dụng `env(safe-area-inset-*)` không?
- **Lưu ý**: `safe-area-inset-bottom` thường cần thiết cho iPhone dòng X trở lên để đẩy UI lên khỏi thanh Home ảo.

### 3. Check Fullscreen Logic
- Kiểm tra logic JS kích hoạt class `.game-active`.
- **Verify**: Khi class này kích hoạt, `body` có thuộc tính `overflow: hidden` và `position: fixed` không? Điều này ngăn trang web bị cuộn nảy (elastic scrolling) trên iOS.

### 4. Check PWA Manifest
- Mở `manifest.json`.
- **Verify**: `display` phải là `standalone`.
- **Verify**: `theme_color` và `background_color` phải khớp với màu nền game (thường là đen `#000000`) để notch hòa vào nền.
