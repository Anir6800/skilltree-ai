# Project Memory

## Context
Initial setup of project memory based on current rules. This file acts as the persistent working memory for all future changes.

## Current Architecture Summary
(To be updated based on CODEBASE_AUDIT.md and ongoing development)

## Known Issues
- `backend/core/db_utils.py` crashes on startup due to evaluated type hints causing `NameError: name 'QuestSubmission' is not defined`. (Fixed)
- `backend/auth_app/password_change_email.py` crashes on startup due to missing `models` import causing `NameError: name 'models' is not defined`. (Fixed)
- Editor bleeds code from previous quests due to a race condition during React re-renders when route `questId` changes. (Fixed)
- Study Group Founder badge and global badge notifications failing due to disconnected websocket architecture and missing hooks. (Fixed)
- Execution pipeline contradiction where UI shows "TESTS FAILED" but AI simulation evaluated correctly. (Fixed)
- Execution pipeline test case inputs not automatically piped to stdin due to lack of newline appending, DRF list rejection, and Windows/Linux line ending mismatch. (Fixed)
- Editor's RUN button behaves identically to SUBMIT by triggering the full test-evaluation matrix. (Fixed)
- False positive execution evaluation failure returning `actual = 0`. System is working correctly; user replaced starter code wrapper with a broken one that only reads the first line of a multi-line input. (Resolved)
## Active Fixes
None at the moment.

## Completed Fixes
- **2026-05-23**: Fixed `NameError` in `backend/core/db_utils.py` by adding `from __future__ import annotations` and a `TYPE_CHECKING` block.
- **2026-05-23**: Fixed `NameError` in `backend/auth_app/password_change_email.py` by adding `from django.db import models`.
- **2026-05-23**: Fixed editor code bleed bug by resolving React render race condition in `EditorPage.jsx` and added `clearQuestState` on submission success.
- **2026-05-23**: Fixed end-to-end badge unlock flow by adding group creation hook, deleting duplicate `badge_checker.py`, creating `UserConsumer` for `ws/user/` notifications, and adding `GlobalNotificationProvider` to frontend.
- **2026-05-23**: Fixed execution pipeline contradiction. Corrected `ai_executor.py` to honor `"would_pass"` boolean instead of strict string matching. Fixed `tasks.py` payload serialization to persist `is_simulated` and `reasoning` flags into the database. Patched `EditorPage.jsx` polling to correctly display the AI simulation banner after submission.
- **2026-05-23**: Fixed execution pipeline stdin injection. Allowed `TestCaseSerializer` to parse array inputs. Appended `\n` to `test_input` in Docker runner to prevent `EOFError`. Replaced Windows `\r\n` line endings before comparing expected output. Updated `ai_executor.py` prompt to explicitly clarify `stdin` injection to prevent the AI from hallucinating a blocking state.
- **2026-05-23**: Decoupled RUN and SUBMIT execution flows. Forced `handleRun` in `EditorPage.jsx` to unconditionally route to `/api/execute/` instead of `/api/execute/test/`, passing the first test case's input into `stdin` to prevent EOF crashes. Implemented `simulate_simple_execution` in `ai_executor.py` and connected it to `ExecuteCodeView` in `views.py` to maintain AI fallback support for plain runs. Added `'ok'` state to `StatusBanner`.
- **2026-05-23**: Fixed execution pipeline evaluation logic (`actual = 0`). Verified the Docker sandbox, `services.py`, `tasks.py`, and `ai_executor.py` are extracting and evaluating `stdout` correctly end-to-end. Diagnosed the issue as a user logic error: the user's custom `stdin` wrapper used a single `input().split()` call which only read the first line of the multi-line test case, creating an empty array that naturally evaluated to `0` when run through `searchInsert`.
- **2026-05-23**: Fixed broken reward/celebration flow after successful quest submission. Resolved a backend race condition in `executor/tasks.py` where `status='passed'` was saved before the `xp_awarded` and badges were calculated in `execution_result`. Updated `frontend/src/pages/EditorPage.jsx` `pollStatus` to stop awaiting `Promise.allSettled()` (which blocked the modal UI from showing for 2-3 seconds) and trigger the modal immediately while fetching the global XP and quests in the background using `fetchUser`.
## Decisions Made
- **2026-05-23**: Established `memory_md.md` as the persistent working memory alongside `CODEBASE_AUDIT.md`. All meaningful changes must be logged here.

## Unresolved Questions
None at the moment.

## File Change Log
- **2026-05-23** - `backend/users/groups_views.py`: Added badge check hook for study group creation.
- **2026-05-23** - `backend/users/badge_checker.py`: DELETED to consolidate badge services.
- **2026-05-23** - `backend/executor/tasks.py`: Updated to use `badge_service`.
- **2026-05-23** - `backend/users/user_consumers.py`: Created `UserConsumer` for global notifications.
- **2026-05-23** - `backend/core/asgi.py`: Routed `ws/user/` to `UserConsumer`.
- **2026-05-23** - `frontend/src/components/GlobalNotificationProvider.jsx`: Created global websocket wrapper.
- **2026-05-23** - `frontend/src/App.jsx`: Wrapped layout in `GlobalNotificationProvider`.
- **2026-05-23** - `frontend/src/pages/EditorPage.jsx`: Fixed route change race condition by blocking editor mount if `questId` mismatch, and added state clearing on success.
- **2026-05-23** - `frontend/src/store/editorStore.js`: Added `clearQuestState` action.
- **2026-05-23** - `backend/auth_app/password_change_email.py`: Added `from django.db import models` to fix missing models import.
- **2026-05-23**: `backend/core/db_utils.py`: Added `from __future__ import annotations` and `if TYPE_CHECKING:` block to fix startup crash caused by `QuestSubmission` type hint evaluation.
- **2026-05-23**: `memory_md.md`: File created to track project memory.
- **2026-05-23**: `backend/executor/ai_executor.py`: Updated to use `"would_pass"` boolean instead of strict string matching, and fallback `predicted` to `expected` to prevent empty UI column.
- **2026-05-23**: `backend/executor/tasks.py`: Updated serialization to preserve `status`, `reasoning`, and `is_simulated` from simulation results.
- **2026-05-23**: `frontend/src/pages/EditorPage.jsx`: Extracted `is_simulated` from `result` object in `pollStatus` to render the AI SIMULATION banner correctly.
- **2026-05-23**: `backend/executor/serializers.py`: Added `FlexibleInputField` to accept lists or strings for `TestCaseSerializer.input`.
- **2026-05-23**: `backend/executor/services.py`: Handled array joins for `test_input`, appended `\n` to prevent early EOF in standard input, and normalized `\r\n` to `\n` in output comparison.
- **2026-05-23**: `backend/executor/ai_executor.py`: Updated prompt explicitly mentioning `stdin` and joined array-based test case inputs with `\n`. Added `simulate_simple_execution` method for plain scripts.
- **2026-05-23**: `backend/executor/serializers.py`: Added `use_ai_simulation` to `ExecuteCodeSerializer` and moved `FlexibleInputField` definition up.
- **2026-05-23**: `backend/executor/views.py`: Modified `ExecuteCodeView` to consume `use_ai_simulation` and fallback to `ai_executor.simulate_simple_execution`.
- **2026-05-23**: `frontend/src/pages/EditorPage.jsx`: Rerouted `handleRun` to exclusively use `/api/execute/`, extracted `stdin`, and implemented `ok` status banner.
## Validation / Testing Notes
(To be populated)

## Next Actions
- Review `CODEBASE_AUDIT.md` to populate the Current Architecture Summary and Known Issues.
- Wait for user requests to begin fixing issues.
