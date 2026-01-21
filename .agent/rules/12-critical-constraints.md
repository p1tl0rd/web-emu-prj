---
trigger: glob
globs: ["index.html", "src/**/*.js", "styles/**/*.css"]
---

# HỆ THỐNG RÀNG BUỘC "TỐI KỴ" (NON-NEGOTIABLE CONSTRAINTS)

## 1. Cross-Origin Isolation (COI) Service Worker
- **Bối cảnh**: EmulatorJS yêu cầu `SharedArrayBuffer` để hỗ trợ đa luồng (multi-threading) trong WebAssembly. Các trình duyệt hiện đại tắt mặc định để chống lỗ hổng Spectre/Meltdown.
- **Vấn đề**: GitHub Pages không cho phép config HTTP Headers (COOP/COEP).
- **MANDATE (Bắt buộc)**:
    - Script `coi-serviceworker.js` PHẢI là script đầu tiên được tải trong thẻ `<head>` hoặc đầu `<body>` của `index.html`.
    - **Cấm**: Không được bundle script này vào file JS chính. Nó phải tồn tại độc lập để register service worker trước khi Wasm khởi chạy.
    - **Kiểm tra**: Agent phải verify sự tồn tại của `<script src="coi-serviceworker.js"></script>` trong mỗi lần build.

## 2. Legacy Script Injection (Cấm Logic Cũ)
- **MANDATE**:
    - **Cấm**: Không sử dụng thẻ `<script>` tĩnh để load core giả lập (ví dụ `emulator.js`).
    - **Yêu cầu**: Sử dụng mẫu thiết kế "Smart Loader Injection":
        1. Định nghĩa các biến cấu hình `window.EJS_*` (`core`, `path`, `bios`) bằng JavaScript.
        2. Tạo thẻ `<script>` động (`document.createElement`) trỏ tới `data/loader.js` và append vào DOM sau khi cấu hình đã sẵn sàng.
        3. `EJS_pathtodata` phải luôn trỏ về thư mục `data/`, tuyệt đối không để null.

## 3. Mobile Fullscreen & Notch Handling (Xử lý Tai thỏ)
- **Bối cảnh**: iPhone "tai thỏ" che khuất nội dung game.
- **MANDATE**:
    - **Viewport Meta**: Bắt buộc phải có `viewport-fit=cover` trong thẻ meta viewport.
    - **Class Trigger**: Trạng thái toàn màn hình phải được kích hoạt bởi class CSS `.game-active` trên thẻ `<body>`.
    - **CSS Safe Area**: Khi ở chế độ `.game-active`, sử dụng biến môi trường:
        ```css
        padding-top: env(safe-area-inset-top);
        padding-left: env(safe-area-inset-left); /* Chế độ ngang */
        min-height: -webkit-fill-available; /* Fix lỗi 100vh trên iOS */
        ```

## 4. DOM Structure Integrity
- **MANDATE**:
    - Cấu trúc sau là BẤT BIẾN (Immutable), Agent không được phép đổi ID hay Class:
    ```html
    <div style="width:100%;height:100%;max-width:100%">
        <div id="game"></div> <!-- Container của Emulator -->
    </div>
    ```

## 5. Cache-Busting cho Gamelist
- **MANDATE**:
    - Mọi lệnh `fetch('gamelist.json')` đều phải kèm query param thời gian: `?t=${new Date().getTime()}` hoặc version hash.
    - Tuyệt đối không fetch thuần để tránh cache cũ của GitHub Pages.