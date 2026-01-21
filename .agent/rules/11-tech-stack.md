---
description: "BẮT BUỘC: Định nghĩa ngăn xếp công nghệ và các thư viện bị cấm tuyệt đối."
globs: ["/*.js", "/.html", "**/.css"]
always_apply: true
priority: critical
---
# MANDATORY TECHNOLOGY STACK

## Core Logic & Runtime
- **Language**: Vanilla JavaScript (ES6+).
- **Module System**: Native ES Modules (`import`/`export`).
- **Forbidden**: KHÔNG sử dụng React, Vue, Angular, Svelte, hoặc jQuery. Mọi thao tác DOM phải sử dụng API native (`document.querySelector`, `classList`, `addEventListener`).
- **Reasoning**: EmulatorJS chạy trên WebAssembly và tiêu tốn tài nguyên lớn cho việc giả lập CPU/GPU. Việc thêm Virtual DOM overhead sẽ gây sụt giảm FPS trên các thiết bị di động yếu.

## User Interface
- **Framework**: Bootstrap 5.3+ (Sử dụng qua CDN hoặc local assets).
- **Style Strategy**: Ưu tiên sử dụng Utility Classes của Bootstrap cho layout. Custom CSS (`style.css`) chỉ dành cho các hiệu ứng game-specific (CRT scanlines, notch handling).

## Backend Architecture
- **Service**: Google Firebase (Platform-as-a-Service).
- **SDK Version**: Firebase V9 Modular SDK.
- **Constraint**: BẮT BUỘC sử dụng cú pháp modular (`import { getDatabase } from...`) để hỗ trợ tree-shaking. CẤM sử dụng cú pháp namespaced cũ (`firebase.database()`).

## Deployment
- **Platform**: GitHub Pages.
- **Data Persistence**: `localStorage` cho save states cục bộ, Firebase Realtime Database cho global data.
