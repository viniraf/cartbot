# CartBot AI Instructions

This document defines how AI assistants (Copilot, ChatGPT, Cursor, etc.) should behave when generating code for CartBot.

The goal is to ensure:
- Consistent architecture
- Predictable code generation
- High readability
- Minimal rework

This file acts as an operational contract for AI-assisted development.

---

# 1. Core Behavior

When generating code for CartBot, always prioritize:

1. Clarity over cleverness
2. Consistency with existing files
3. Simplicity over abstraction
4. Architecture compliance

Do not introduce unnecessary complexity.

---

# 2. Architecture Compliance

AI must follow the architecture defined in:

docs/architecture.md

Respect the layered modular monolith:

handlers → services → domain → infra

Never violate dependency direction.

---

# 3. Layer Rules

## 3.1 Handlers
Located in:
app/handlers/

Must:
- Handle Telegram input/output
- Manage conversation state
- Call services

Must NOT:
- Contain business logic
- Access database directly
- Perform calculations

---

## 3.2 Services
Located in:
app/services/

This is the main logic layer.

Must:
- Implement use cases
- Be framework-agnostic
- Be easily testable

Must NOT:
- Import Telegram libraries
- Format UI responses
- Use print statements

---

## 3.3 Domain
Located in:
app/domain/

Must:
- Contain pure business logic
- Be deterministic
- Have no external dependencies

Must NOT:
- Import infra or handlers
- Access environment variables
- Perform IO

---

## 3.4 Infrastructure
Located in:
app/infra/

Must:
- Handle persistence and IO
- Implement repositories
- Be replaceable

Must NOT:
- Contain business rules

---

# 4. Naming Rules

All generated code must be in English.

Use:

Classes:
PascalCase nouns
Example:
PurchaseService

Functions:
snake_case verbs
Example:
add_item

Files:
snake_case

Avoid mixed languages.

---

# 5. Code Style

AI should generate:

- Small, focused functions
- Explicit names
- Readable control flow
- Minimal nesting

Prefer straightforward implementations over smart tricks.

---

# 6. Function Generation Rules

When generating functions:

- One responsibility per function
- Avoid long parameter lists (>5 args)
- Prefer explicit inputs
- Return structured results

If complexity grows:
Extract helpers.

---

# 7. Class Generation Rules

When generating classes:

- Keep them small and cohesive
- Avoid inheritance unless clearly necessary
- Prefer composition

Avoid god classes.

---

# 8. Error Handling

Use explicit exceptions:

- ValidationError
- NotFoundError
- DomainError

Do not silently swallow errors.

Handlers may translate exceptions into user-friendly messages.

---

# 9. Comments and Docstrings

AI should:

- Prefer self-documenting code
- Add docstrings to public services
- Avoid obvious comments

Use comments only when explaining intent or trade-offs.

---

# 10. Imports

Follow import order:

1. Standard library
2. Third-party
3. Local modules

Avoid circular imports.

---

# 11. State Management

Respect state boundaries:

- Conversation state → handlers
- Business state → domain
- Persistence state → infra

Never mix these concerns.

---

# 12. Logging

If adding logs:

- Use logging module
- Avoid print()
- Do not log inside domain

Log at system boundaries only.

---

# 13. Configuration

If configuration is needed:

- Use environment variables
- Centralize config access
- Avoid scattered os.getenv calls

Prefer a single config module.

---

# 14. Testing Awareness

When generating code:

- Keep services easily testable
- Avoid hard dependencies
- Avoid hidden side effects

Favor deterministic behavior.

---

# 15. File Creation Rules

When creating new files:

- Place them in the correct layer
- Follow existing naming patterns
- Avoid creating new top-level folders without reason

Maintain predictable structure.

---

# 16. Refactoring Behavior

When asked to refactor:

- Preserve behavior
- Improve readability
- Reduce complexity
- Avoid architectural rewrites unless requested

Refactor incrementally.

---

# 17. Avoid These Anti-Patterns

AI must NOT:

- Introduce microservices
- Add unnecessary interfaces
- Over-abstract early
- Mix Portuguese in code
- Add global mutable state
- Collapse layers into one file

Stay aligned with project scale.

---

# 18. When Unsure

If the request is ambiguous:

Prefer:
- Simpler implementation
- Explicit naming
- Fewer abstractions

Always bias toward maintainability.

---

# 19. Example Service Pattern

When generating a new use case, follow this structure:

- Create a service class in app/services
- Inject repository via constructor
- Implement a single public method
- Return structured data

Keep the implementation clean and linear.

---

# 20. Example Handler Pattern

When generating handlers:

- Parse user input
- Validate basic format
- Call service
- Format response text

Handlers should remain thin adapters.

---

# 21. Evolution Awareness

Code should be written assuming future features:

- Reports
- REST API
- Web UI
- Multi-user

Avoid tightly coupling logic to Telegram.

---

# 22. Consistency Rule

Above all:

Match the style of existing code.

If the project uses:
- Certain naming patterns
- Certain file structures
- Certain return types

Follow them strictly.

Consistency is more important than personal preference.

---

# 23. Final Instruction

When generating code for CartBot:

Be boring.
Be clear.
Be consistent.

Readable code that fits the architecture is always the correct answer.

Never suggest committing SQLite databases.
Always assume databases are environment-specific and created at runtime.
If persistence is needed, implement automatic database initialization.