# Ponytail Style Rules: Clean, Clear, and Concise

Code readability directly impacts maintainability. A lazy senior developer writes self-documenting code that requires minimal explanation, saving time in the long run.

---

## Coding Conventions

1. **Naming & Style:**
   - Follow PEP 8 guidelines for Python code.
   - Use descriptive, action-oriented names for functions (e.g., `extract_pdf_metadata`, `build_docx_layout`).
   - Use snake_case for functions, methods, and variables; PascalCase for classes; UPPER_CASE for constants.

2. **Typing & Type Hints:**
   - Use Python type hints (`int`, `str`, `dict`, `list`, or `typing` module equivalents) for public function signatures and API parameters.
   - Type hints serve as native documentation and enable automatic validation in Pydantic.

3. **Functions & Classes:**
   - Keep functions focused on a single responsibility. If a function is too long (e.g., > 50 lines), consider refactoring it.
   - Avoid creating classes if a module-level function will suffice. Prefer simple data classes/Pydantic models for structured data rather than complex class hierarchies.

4. **Comments & Documentation:**
   - Do not write comments that describe *what* the code does; write comments that describe *why* a particular approach was taken (especially when handling quirks in libraries like PyMuPDF or python-docx).
   - Use `# ponytail: [reason]` for intentional shortcuts or simplifications to make it clear that the simplicity was deliberate.
