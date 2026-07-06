# Implementation Prompt for Claude

Copy and paste this prompt when asking Claude to fix the SkillTree AI project:

---

<role>Senior Full-Stack Engineer & Bug Fix Specialist</role>

<task>Fix critical blocking bugs in SkillTree AI college project to make it demo-ready. Follow the comprehensive technical audit document to resolve 5 critical issues that prevent the application from functioning end-to-end.</task>

<context>
This is a gamified developer learning platform built with:
- **Frontend:** React 19 + Vite, Tailwind CSS, Three.js, Monaco Editor
- **Backend:** Django 6.0, PostgreSQL, Redis, Celery, ChromaDB
- **Features:** AI-powered code evaluation, real-time multiplayer, skill trees (DAGs), gamification (XP/badges/streaks)

The project is 65% complete with solid architecture but has 5 critical bugs blocking all core functionality. A comprehensive technical audit (COMPREHENSIVE_TECHNICAL_AUDIT.md) has identified all issues with detailed fixes.

**Current Location:** `c:\personal project\skilltree-ai\`
**Audit Document:** `c:\personal project\skilltree-ai\COMPREHENSIVE_TECHNICAL_AUDIT.md`
</context>

<constraints>
**DO:**
- Read the COMPREHENSIVE_TECHNICAL_AUDIT.md document thoroughly before starting
- Fix bugs in place; don't refactor entire modules
- Follow existing code patterns (Django services, DRF views, Zustand stores)
- Test each fix with: Register → Login → Submit Quest → Check XP/Badge
- Add comprehensive docstrings to new functions
- Use existing models and patterns
- Add error handling to all new code

**DON'T:**
- Rewrite entire modules - fix specific bugs only
- Change database schema without migrations
- Break existing working features
- Add new dependencies unless absolutely necessary
- Change API response formats (breaks frontend)
- Skip testing after each fix

**CRITICAL PATH (Fix in this order):**
1. AI Detection Sync Wrapper (30 min) - BLOCKS ALL SUBMISSIONS
2. Badge Criteria Evaluation (3 hrs) - BLOCKS GAMIFICATION
3. Code Execution Fallback (2 hrs) - BLOCKS DEMO WITHOUT DOCKER
4. Leaderboard Pagination (1 hr) - BLOCKS SCALABILITY
5. Error Boundaries & Polish (2 hrs) - PREVENTS CRASHES
</constraints>

<format>
For each fix, provide:

1. **File to modify/create:** Full path from project root
2. **Code implementation:** Complete, working code
3. **Explanation:** Brief description of what the fix does
4. **Testing steps:** How to verify the fix works
5. **Related files:** Any other files that need updates

After all critical fixes:
- Provide a summary of what was fixed
- List remaining known issues
- Suggest next steps for polish

**Code Style:**
- Python: Follow PEP 8, use type hints where helpful
- JavaScript/React: Use modern ES6+, functional components
- Comments: Explain WHY, not WHAT
- Error handling: Always include try/catch with logging
</format>

---

## CRITICAL ISSUES TO FIX (Priority Order)

### 🔴 ISSUE #1: AI Detection Async/Await Mismatch
**File:** `backend/ai_detection/services.py`
**Problem:** Method `detect_sync()` called but doesn't exist; all submissions crash
**Fix:** Add synchronous wrapper using `asyncio.run_until_complete()`
**Test:** Submit quest → verify pipeline reaches step 5 without AttributeError

### 🔴 ISSUE #2: Badge System Non-Functional  
**File:** `backend/quests/badge_hooks.py` (CREATE NEW)
**Problem:** Function `check_badges_on_quest_completion()` doesn't exist
**Fix:** Create badge evaluation logic matching Badge.unlock_condition JSON schema
**Test:** Complete quest → verify UserBadge record created and notification appears

### 🔴 ISSUE #3: Code Execution Fallback Broken
**File:** `backend/executor/services.py`
**Problem:** No MockExecutor class; demo fails without Docker
**Fix:** Create MockExecutor with heuristic-based test simulation
**Test:** Stop Docker → submit quest → verify simulation mode activates

### 🔴 ISSUE #4: Leaderboard Pagination Missing
**Files:** `backend/leaderboard/views.py`, `frontend/src/pages/LeaderboardPage.jsx`
**Problem:** Loads entire leaderboard; browser OOM with 1000+ users
**Fix:** Add page/pageSize parameters and pagination UI
**Test:** Create 1000 test users → verify only 50 render per page

### 🔴 ISSUE #5: Component Duplication & Error Boundaries
**Files:** `frontend/src/components/`, `frontend/src/App.jsx`
**Problem:** Duplicate badge components; no error boundaries cause white screen crashes
**Fix:** Remove duplicates, add React.ErrorBoundary to main pages
**Test:** Trigger error → verify fallback UI appears instead of white screen

---

## SUCCESS CRITERIA

✅ **User can complete this flow without crashes:**
1. Register account
2. Login
3. View skill tree
4. Select quest
5. Submit code solution
6. See pipeline progress (7 steps)
7. Receive XP and level up
8. Earn first badge
9. See updated leaderboard rank

✅ **No console errors on happy path**
✅ **Works without Docker running (MockExecutor)**
✅ **Leaderboard handles 1000+ users**
✅ **All error states show friendly messages**

---

**Additional Resources:**
- Full technical audit: `COMPREHENSIVE_TECHNICAL_AUDIT.md` (read this first!)
- Project README: `README.md`
- Development guide: `AGENTS.md`

**Questions to ask yourself:**
- Did I read the full audit document?
- Did I test my fix end-to-end?
- Did I follow existing code patterns?
- Did I add error handling?
- Did I document my changes?

---

**Ready to implement? Start by reading COMPREHENSIVE_TECHNICAL_AUDIT.md Section 12 (AI Handoff Report).**
