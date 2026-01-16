---
trigger: model_decision
description: Apply when user requests creating new feature, component, or module
---

# 🏗️ Build Mode (Universal)

**Goal:** Create new code that meets standards and is maintainable.

## Process

1.  **Confirm Scope & Acceptance Criteria**
2.  **Propose Structure:** (File hierarchy / Class design / Node architecture)
3.  **Implementation Order:**
    *   **Interface/Types/Headers** (Define contract first)
    *   **Core Logic/Algorithms**
    *   **Integration/Wiring**
4.  **Verification:** Run build/tests before delivery
5.  **Documentation:** Explain complex logic

## Output Format

```markdown
## 🏗️ BUILD: [Feature name]

**Scope:** [description]

**Acceptance Criteria:**
- [ ] AC1: [criterion 1]
- [ ] AC2: [criterion 2]

---

### Code:
**File: `[path]`**
```[language]
// Code here
```

---

### ✅ Checklist:
- [x] Type/Memory Safe (No warnings)
- [x] Complete error handling
- [x] No hardcoded values (Use define/const/config)
- [x] Comments for complex logic
```

## Principles

| ❌ DON'T | ✅ DO |
|----------|-------|
| Add features outside scope | Do exactly what's requested |
| Use implicit types (`void*`, `any`) | Declare explicit types/interfaces |
| Hardcode values | Use constants/config files |
| Skip error handling | Handle exceptions/errors and edge cases |
| Write Monolithic Blocks | Split into small functions/classes/nodes |