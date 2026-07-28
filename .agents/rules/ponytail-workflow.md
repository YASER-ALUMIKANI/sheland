# Ponytail Workflow Rules: The Path of Least Friction

A lazy developer plans the execution path to minimize coding friction, avoiding restarts, debug loops, or complex rollback procedures.

---

## Workflow Guidelines

1. **Incremental Updates:**
   - Implement features incrementally. Compile and test code after every small, self-contained change.
   - Never implement huge chunks of functionality without validating the execution path.

2. **Automated Testing:**
   - Always verify changes with automated tests. Run existing tests (`pytest tests/`) to ensure no regressions were introduced.
   - When introducing new logic or fixing a bug, write a simple unit test in the `tests/` folder. A lazy developer writes tests once so they don't have to manually verify the code ten times.

3. **Planning & Execution:**
   - Only construct elaborate implementation plans for complex architectural changes. For simple bug fixes or visual tweaks, execute them immediately.
   - Keep communication brief and focus on explaining the rationale behind technical choices.

4. **Task & API Design:**
   - In a FastAPI + Celery architecture, keep the API endpoints light. Their primary job is input validation, task triggering, and immediate status response.
   - Place heavy computational logic (like image extraction, layout analysis, page parsing) inside Celery task workers to prevent blocking the web server event loop.
