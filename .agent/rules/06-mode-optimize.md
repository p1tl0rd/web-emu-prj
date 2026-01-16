---
trigger: model_decision
description: Apply when user requests refactoring, optimization, or performance improvement
---

# ⚡ Optimize Mode (Universal)

**Goal:** Improve quality **WITHOUT changing behavior**.

## Process

1.  **Measure Baseline:** Capture current performance metrics.
2.  **Identify Bottleneck:** Use profilers (cProfile, Valgrind, etc.) or log analysis.
3.  **Propose Improvements:** Estimate impact.
4.  **Refactor:** Apply changes by priority.
5.  **Compare:** Verify improvement against baseline.
6.  **Regression Check:** Ensure all tests still pass.

## Evaluation Criteria (Examples)

| Criterion | Tool (Generic) | Good Threshold |
|-----------|----------------|----------------|
| **Executable Size** | Build System / Compiler | < Target Limit |
| **Latency / Loop Rate** | Profiler / Logs | < Target ms (or > Hz) |
| **Memory Usage** | Memory Monitor / Leaks Check | Stable (No Leaks) |
| **Complexity** | Linter / Static Analysis | Low Cyclomatic |

## Output Format

```markdown
## ⚡ OPTIMIZE

**Issue:** [slow / high cpu / memory leak / spaghetti code]

**Baseline:**
- Size: X MB
- Latency: X ms
- CPU: X %

---

### Bottleneck:
| Issue | Location | Severity |
|-------|----------|----------|
| [Description] | `file:line` | 🔴 High |

### Proposal:
| Item | Before | After | Δ |
|------|--------|-------|---|
| Latency | 100ms | 15ms | -85% |

### Regression Check:
- [ ] Tests still pass
- [ ] Behavior unchanged
```

## Principles

| ❌ DON'T | ✅ DO |
|----------|-------|
| Optimize prematurely | Measure first, optimize later |
| Change behavior | Keep behavior unchanged (Refactoring) |
| Prioritize cleverness | Readability > Performance (unless critical) |
| Skip tests | Re-run verification/tests |