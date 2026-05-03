# SkillTree AI Pre-Production Audit Report

## 1. Data Integrity & State Management

**The "Missing Link" Check**:
- **Critical:** In `backend/skills/views.py`, the `user.level` derivation calculation is bypassed by `update_fields` when awarding XP. In `QuestSubmission` evaluation in `backend/quests/views.py`, the `user.save()` is executed correctly *without* `update_fields`, but in `backend/multiplayer/consumers.py` (`MatchConsumer.award_xp`) and `backend/executor/pipeline.py` (`_award_xp_sync`), XP is added and saved without triggering `user.save()` overrides, meaning levels are not consistently re-calculated on the backend. This leads to the UI and Backend being disconnected on the user's current level.

**State Synchronization**:
- **Logic Gap:** The Frontend uses `setInterval` polling for Execution status in `frontend/src/hooks/useExecution.js` and `EditorPage.jsx`. When multiple network errors happen, it resets the poll interval or duplicates the request interval if `clearPoll` is not perfectly synchronized.
- **Race Condition:** In `EditorPage.jsx`, if the user switches quests rapidly, the previous execution poll might resolve and overwrite the current quest state because the polling mechanism relies on a single `executionId` ref without validating that the returned `quest_id` matches the current editor's quest.

## 2. Error Handling & Edge Cases

**The "Silent Killer" Search**:
- **Critical:** In `backend/multiplayer/consumers.py`, the `MatchConsumer` silently catches exceptions when awarding XP or updating participant scores (`except (Match.DoesNotExist, User.DoesNotExist): pass`). If the match object is deleted mid-game or a user disconnects aggressively, errors are hidden, causing silent data drops.
- **Critical:** In `backend/executor/services.py`, the `CompileExecutor._cleanup_sandbox` catches and suppresses exceptions (`except Exception as e: print(...)`). This causes a severe disk leak over time if Docker containers hang or file permission errors arise, filling the host machine with zombie sandbox directories.
- **Logic Gap:** In `backend/leaderboard/services.py`, exceptions when converting user XP or updating rankings are suppressed with `except (ValueError, TypeError): pass`.

**Boundary Testing**:
- **Logic Gap:** In `frontend/src/pages/MatchPage.jsx`, the WebSocket retry counter `retryCountRef` goes into an infinite connection loop if the server explicitly denies connection via 403, flooding the Django Channels service.
- **Performance:** In `frontend/src/api/api.js`, multiple concurrent HTTP requests that fail with 401 will *all* attempt to hit the `refreshAccessToken` endpoint simultaneously, rather than queuing behind a single token refresh request (the `refreshPromise` mechanism isn't cleanly locking for all interceptor firings).

## 3. Security & Environment Safety

**Hardcoded Secrets**:
- **Security Risk:** In `backend/core/settings.py`, the `SECRET_KEY` falls back to a hardcoded development string `'django-skilltree-ai-immersive-platform-v1-production-ready-key-replace-this'` if `os.getenv` fails. This is explicitly meant for development, but leaving it as a fallback in production allows cryptographic bypass if the `.env` fails to mount.

**Injection Risks**:
- **Security Risk:** In `backend/executor/views.py`, the `ExecuteCodeSerializer` doesn't sanitize `stdin_input` for arbitrary shell payloads, and `services.py` passes it into `docker run -i` without bounds checking. A payload designed to exploit terminal escape sequences or interactive TTYs could compromise the Docker daemon if Alpine isn't strictly locked down.
- **Security Risk:** In `backend/admin_panel/views.py`, the `AdminContentViewSet` accepts Markdown via `body = models.TextField()`. If this Markdown is rendered directly via `dangerouslySetInnerHTML` on the frontend (like in `HintPanel.jsx` or Quest descriptions), it's highly susceptible to Stored XSS. Note: Checked Frontend for `dangerouslySetInnerHTML`, while currently not widespread, standard Markdown renderers must enforce DOMPurify.

## 4. Performance & Scalability

**Optimization**:
- **Quick Win (N+1 Query):** In `backend/multiplayer/serializers.py`, `MatchListSerializer.get_participants` uses `obj.matchparticipant_set.all()` without `prefetch_related` in `Match.objects.all()`, leading to a severe N+1 query problem when loading the matchmaking lobby.
- **Quick Win (N+1 Query):** In `backend/skills/views.py` `get_prerequisites_count`, it queries `prerequisites.all()` individually for every skill serialized.
- **Performance:** `backend/admin_panel/views.py` triggers an N+1 query when listing submissions: `submissions = AssessmentSubmission.objects.all()` then serializing related users/questions without `.select_related()`.

**Memory Leaks**:
- **Critical:** In `frontend/src/hooks/useWebSocket.js`, the WebSocket event listeners are not properly cleaned up if the component unmounts *during* the connection phase (`ws.readyState === WebSocket.CONNECTING`), leading to dangling WebSockets.

## 5. Architectural Consistency

**Naming Conventions**:
- **Logic Gap:** Inconsistent casing and naming for AI results. The backend sends `ai_detection_score`, `feedback`, `is_simulated`. The frontend expects `detectionScore`, `aiFeedback`. This results in `undefined` states in `EditorPage.jsx` when handling execution responses.

**Dependency Health**:
- **Security Risk:** The Docker Execution Sandbox mounts volumes using `-v {docker_volume}:/sandbox`. If the user submits malicious paths, they could escape the intended directory, especially on Windows environments where path sanitization in `_get_docker_volume_path` is fragile.
- **Architectural:** The DB schema relies heavily on `ChromaDB` for Vector syncing, but `core/chroma_client.py` swallows `ChromaDB` connection errors (`except Exception: pass`). This violates eventual consistency guarantees, leaving the Vector Store permanently out of sync with Postgres until a manual script is run.

---
**Summary of Immediate Action Items:**
1. Fix `user.save()` overrides in Celery tasks to sync `level` and `xp`.
2. Fix the N+1 queries in Multiplayer and Skill serializers using `prefetch_related`.
3. Enhance `CompileExecutor._cleanup_sandbox` to forcefully kill hanging Docker processes.
4. Remove the fallback `SECRET_KEY` in `settings.py`.
5. Properly handle ChromaDB synchronization errors.
