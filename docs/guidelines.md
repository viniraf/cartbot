# CartBot Development Guidelines

This document defines coding standards, guardrails, and best practices for developing CartBot.

It is optimized for:
- High readability
- Consistent AI-assisted development
- Maintainable codebase
- Low cognitive load

These guidelines are intentionally pragmatic, not dogmatic.

---

# 1. General Philosophy

CartBot prioritizes:

- Clarity over cleverness
- Consistency over personal style
- Simplicity over abstraction
- Evolution over perfection

If unsure, choose the simplest solution that remains clean.

---

# 2. Language Rules

## 2.1 Code Language
All code must be written in English.

This includes:
- Class names
- Function names
- Variables
- File names
- Comments

Avoid mixing languages in the codebase.

## 2.2 Documentation Language
Technical docs should be written in English.

README may be bilingual.

---

# 3. Naming Conventions

## 3.1 Files
Use snake_case.

Examples:
- purchase_service.py
- sqlite_repository.py
- add_item_handler.py

Avoid:
- camelCase
- kebab-case

---

## 3.2 Classes
Use PascalCase.

Examples:
- Purchase
- PurchaseItem
- PurchaseService
- SQLitePurchaseRepository

Classes should be nouns.

---

## 3.3 Functions and Methods
Use snake_case verbs.

Examples:
- add_item()
- remove_item()
- calculate_total()
- start_purchase()

Functions should express intent clearly.

Avoid vague names:
- process()
- handle()
- do_stuff()

---

## 3.4 Variables
Use descriptive names.

Good:
- total_amount
- unit_price
- purchase_id

Avoid:
- tmp
- data
- x

---

# 4. File Size Guidelines

Keep files small and focused.

Recommended limits:
- Handlers: < 200 lines
- Services: < 300 lines
- Domain models: < 200 lines

If a file grows too large:
Split by responsibility.

---

# 5. Function Design

## 5.1 Single Responsibility
Each function should do one thing.

Bad:
- parse input
- validate
- save
- format output

All in one function.

Good:
Separate steps clearly.

---

## 5.2 Function Length
Prefer short functions (5–25 lines).

If a function requires scrolling:
Consider extracting helpers.

---

## 5.3 Explicit Returns
Avoid implicit behavior.

Good:
Return structured results or domain objects.

Avoid:
Returning raw dicts everywhere without structure.

---

# 6. Class Design

## 6.1 Keep Classes Small
Classes should represent a clear concept.

Examples:
- Purchase
- PurchaseService
- SQLiteRepository

Avoid god classes.

---

## 6.2 Avoid Deep Inheritance
Prefer composition over inheritance.

Inheritance is rarely needed in this project.

---

# 7. Services Guidelines

Services are the most important layer.

Rules:

- Stateless when possible
- No Telegram imports
- No formatting logic
- No printing/logging directly
- No global state

Services should:
- Receive primitives or domain objects
- Return structured results

---

# 8. Handlers Guidelines

Handlers are adapters.

They may:
- Parse user input
- Manage conversation state
- Format responses

They must NOT:
- Contain business rules
- Access database directly
- Perform calculations

Handlers should be thin.

---

# 9. Domain Guidelines

Domain must remain pure.

Rules:
- No framework imports
- No database logic
- No logging
- No environment access

Domain contains:
- Entities
- Value objects
- Business invariants

Keep it deterministic and testable.

---

# 10. Infrastructure Guidelines

Infra handles technical concerns only.

Examples:
- Repositories
- SQLite access
- File IO
- Environment config

Infra should:
- Be replaceable
- Not contain business logic

---

# 11. Error Handling

## 11.1 Use Explicit Exceptions

Define meaningful exceptions:

- ValidationError
- NotFoundError
- DomainError

Avoid generic exceptions when possible.

---

## 11.2 Do Not Swallow Errors
Never silently ignore exceptions.

Fail fast in services.

Handlers may translate errors into user-friendly messages.

---

# 12. Logging

Logging rules:

- Use logging module, not print()
- Log at boundaries (handlers, infra)
- Avoid logging inside domain

Log levels:
- INFO for flows
- WARNING for recoverable issues
- ERROR for failures

---

# 13. Comments and Docstrings

## 13.1 Prefer Self-Documenting Code
Write code that explains itself.

Avoid excessive comments.

---

## 13.2 When to Use Comments
Use comments for:
- Non-obvious decisions
- Workarounds
- Trade-offs

Avoid obvious comments.

Bad:
# increment i
i += 1

---

## 13.3 Docstrings
Use docstrings for:
- Public services
- Complex domain logic

Keep them short and useful.

---

# 14. Formatting

Follow standard Python formatting:

- PEP8 compliance
- 4 spaces indentation
- Max ~100 characters per line

Use tools:
- black
- ruff (optional)

---

# 15. Imports

Order imports as:

1. Standard library
2. Third-party libraries
3. Local modules

Separate groups with blank lines.

Avoid circular imports.

---

# 16. Configuration Management

Rules:
- Use environment variables
- Centralize config loading
- Do not read env vars everywhere

Create a single config module.

---

# 17. State Management

Guidelines:

- UI state lives in handlers
- Business state lives in domain
- Persistence state lives in infra

Do not mix responsibilities.

---

# 18. Testing Guidelines

## 18.1 What to Test
Prioritize:
- Services
- Domain logic

Handlers can have lighter tests.

---

## 18.2 Test Style
Prefer:
- Clear Arrange / Act / Assert structure
- Descriptive test names

Example:
test_add_item_updates_total()

---

## 18.3 Avoid Over-Mocking
Mock only external dependencies.

Do not mock domain behavior.

---

# 19. AI-Assisted Development Rules

These rules ensure better AI output.

## 19.1 Always Maintain Naming Consistency
AI performs best with consistent naming patterns.

## 19.2 Avoid Half-Abstractions
Do not introduce patterns partially.

If introducing a concept:
Apply it consistently.

---

## 19.3 Keep Files Predictable
AI relies heavily on project structure.

Avoid random file placements.

---

## 19.4 Write Clear Intent
Clear function names dramatically improve AI suggestions.

Bad:
handle_data()

Good:
add_item_to_purchase()

---

# 20. Refactoring Rules

Refactor when:

- File becomes hard to navigate
- Function exceeds reasonable size
- Duplicate logic appears
- Naming becomes confusing

Refactor incrementally.

Avoid massive rewrites.

---

# 21. Anti-Patterns to Avoid

Do NOT:

- Mix languages in code
- Create god classes
- Hide logic in utils
- Overuse global variables
- Add premature abstractions
- Implement patterns just because they exist

Stay pragmatic.

---

# 22. Pull Request Mental Checklist

Before considering code "done":

- Is the naming clear?
- Is responsibility well-scoped?
- Is logic in the correct layer?
- Would future me understand this easily?
- Is it consistent with the architecture?

If yes, it is good enough.

---

# 23. Final Rule

This project values:

Consistency > Brilliance

A simple, consistent codebase will outlive a clever one.

Optimize for long-term clarity and ease of evolution.

- Never commit database files (.db, .sqlite)
- Treat database as runtime state, not source code
- Ensure automatic database creation on startup