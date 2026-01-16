---
trigger: always_on
---

# Pre-Delivery Checklist (Universal)

Mandatory checklist before delivering code.

## Code Quality

- [ ] **Type Safety:** No implicit `any` or untyped lists (if language supports types).
- [ ] **Constants:** No hardcoded magic numbers/strings.
- [ ] **Error Handling:** Complete try/catch coverage or error propagation.
- [ ] **Naming:** Clear, descriptive, English variable/function names.
- [ ] **DRY:** No duplicate code blocks.

## Structure

- [ ] **Organization:** Correct folder/package structure.
- [ ] **Conventions:** Follows language-specific style guide (PEP8, Google Style, Airbnb, etc.).
- [ ] **Sizing:** Files are reasonably sized (e.g., < 300 lines).
- [ ] **SRP:** Classes/Modules follow Single Responsibility Principle.

## Interface & Interaction (GUI/CLI/API)

- [ ] **User Experience:** Clear output/feedback for the user.
- [ ] **Responsiveness:** No blocking the main thread/event loop.
- [ ] **States:** Handles Loading, Success, Error, and Empty states.
- [ ] **Inputs:** Validates all external inputs (Parameters, Environment variables).

## Maintainability & Reliability

- [ ] **Documentation:** Comments for complex logic.
- [ ] **Testability:** Logic is decoupled and testable.
- [ ] **Side Effects:** Functions are pure or side-effects are documented.
- [ ] **Resources:** No file handle or memory leaks (Proper cleanup).

## Universal Performance

- [ ] **Efficiency:** No unnecessary loops or heavy computations in hot paths.
- [ ] **Optimization:** Assets/Data structures are optimized for their use case.