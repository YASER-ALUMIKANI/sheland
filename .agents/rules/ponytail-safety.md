---
trigger: always_on
---

# Ponytail Safety Rules: Lazy but Safe.

"Lazy" in Ponytail mode does not mean negligent. A lazy senior developer writes code that doesn't break, because fixing broken code is more work. Never compromise correctness, security, validation, or error handling in the name of terseness.

---

## Safety & Security Guidelines

1. **Input Validation:**
   - Always validate untrusted input. Use Pydantic schemas for FastAPI endpoints.
   - For file uploads, check file headers, MIME types, and sizes before processing them (especially PDF uploads to prevent zip bombs or resource exhaustion).

2. **File & Path Safety:**
   - Avoid path traversal vulnerabilities. When resolving file paths from user inputs, sanitize them using standard path validation libraries (e.g., `os.path.abspath` or `pathlib.Path.resolve` and check if they are within the expected base directory).

3. **Exception Handling:**
   - Never write blank exception blocks (`except: pass`). Always log exceptions or handle them specifically.
   - Gracefully catch library-specific errors (e.g., PyMuPDF decryption/corruption errors, python-docx layout failures) and return structured, meaningful error messages instead of leaking traceback stack traces.

4. **Resource Management:**
   - Always use context managers (`with` statements) for opening files, database sessions, and other resources to ensure they are cleaned up and closed even if errors occur.
   - Clean up temporary files in both success and error branches (e.g., inside `finally` blocks).

5. **Concurrency & Thread Safety:**
   - Ensure Celery tasks are idempotent.
   - Do not store state globally in worker environments; rely on the database or Redis backend.
