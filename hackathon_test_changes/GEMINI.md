# GEMINI.md — Test Environment Integration

This document outlines how the **Gemini 3.1** dual-model strategy is tested within the `hackathon_test_changes` workflow.

## 🧪 Testing Tiers

### 🟢 Minor Tier Test Case
- **Target**: `auth_middleware.py`
- **Action**: Adding a simple field to the `validate_session` return object.
- **Expected Behavior**: Janitor triggers **Gemini 3.1 Flash**, patches `STRUCTURE.md` under the `auth_middleware.py` heading within < 2 seconds.

### 🔴 Major Tier Test Case
- **Target**: `data_processor.py`
- **Action**: Renaming the main processing class and changing the dependency on `Nia` context.
- **Expected Behavior**: Janitor triggers **Gemini 3.1 Pro**, generates a new **ADR** in `docs/adr/`, and updates `ARCHITECTURE.md` to reflect the paradigm shift.

## 🛠️ Verification Commands

```powershell
# Run the agent in 'test' mode to simulate these changes
python agent/main.py --test-folder hackathon_test_changes
```

---
*Note: This file is used for hackathon judges to verify real-time model switching between Flash and Pro.*
