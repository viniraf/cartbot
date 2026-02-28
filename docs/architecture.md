# CartBot Architecture

This document describes the architectural decisions, structure, and guardrails for the CartBot project.

The goal is to provide a clean, simple, and evolvable architecture that is easy to understand, maintain, and extend — without overengineering.

---

# 1. Architectural Goals

CartBot follows a pragmatic architecture designed for:

- Simplicity over theoretical purity
- Fast iteration with AI assistance
- High readability and low cognitive load
- Easy refactoring and evolution
- Long-term maintainability

This is not a strict Clean Architecture or DDD implementation.

Instead, it uses a **Modular Monolith with lightweight layering**.

---

# 2. Architectural Style

## Modular Monolith (Layered)

The system is a single deployable unit with clear internal boundaries.

We use logical layers, not hard abstractions.

Transport (Telegram)
↓
Application Services (Use cases)
↓
Domain (Business logic)
↓
Infrastructure (Persistence, external concerns)

Each layer has a single responsibility and minimal coupling.

---

# 3. Core Principles

## 3.1 Separation of Responsibilities
Each layer has a clearly defined role and should not leak concerns.

## 3.2 Low Coupling
Dependencies should point inward (toward domain logic).

## 3.3 High Readability
Code should be obvious to understand without deep mental mapping.

## 3.4 No Overengineering
Avoid:
- Unnecessary interfaces
- Premature abstractions
- Framework-driven design

## 3.5 Evolution First
The architecture must support:
- Reports
- API exposure
- Multi-user support
- Web UI
Without requiring a rewrite.

---

# 4. Folder Structure

app/
├── main.py
├── handlers/
├── services/
├── domain/
├── infra/
└── common/ (optional)

Additional folders:

data/      → local storage (SQLite, files)
tests/     → automated tests
docs/      → architecture and decisions

---

# 5. Layer Responsibilities

## 5.1 Handlers Layer (Transport)

Location:
app/handlers/

Purpose:
Handle Telegram interactions and conversation flow.

Responsibilities:
- Receive messages and commands
- Manage conversation state
- Validate raw user input
- Call application services
- Format responses

Must NOT:
- Contain business logic
- Access database directly
- Perform calculations

Think of handlers as controllers/adapters.

---

## 5.2 Services Layer (Application Layer)

Location:
app/services/

This is the heart of the system.

Services implement use cases such as:

- start_purchase()
- add_item()
- edit_item()
- remove_item()
- get_purchase_summary()
- calculate_total()

Responsibilities:
- Orchestrate domain objects
- Enforce business rules
- Coordinate repositories
- Return structured results

Services SHOULD be:
- Stateless
- Easily testable
- Framework-agnostic

This is the primary testing surface.

---

## 5.3 Domain Layer

Location:
app/domain/

Contains the core business model.

Examples:
- Purchase
- PurchaseItem
- Money (future)
- Value objects

Responsibilities:
- Represent business entities
- Encapsulate invariants
- Provide domain behaviors

Rules:
- No Telegram imports
- No database logic
- No framework dependencies

Pure Python only.

---

## 5.4 Infrastructure Layer

Location:
app/infra/

Contains technical implementations.

Examples:
- SQLite repositories
- File storage
- Config loaders
- Logging
- Environment handling

Responsibilities:
- Persistence
- IO operations
- External integrations

Infra implements contracts used by services.

---

## 5.5 Common Layer (Optional)

Location:
app/common/

Shared utilities such as:
- Time helpers
- Formatting
- Constants
- Small utilities

Avoid putting business logic here.

---

# 6. Dependency Rules

Strict dependency direction:

handlers → services → domain
                    ↘
                     infra (via composition)

Rules:

1. Handlers may depend on services only.
2. Services may depend on domain and infra.
3. Domain must depend on nothing.
4. Infra must not depend on handlers.

If unsure:
Move logic inward.

---

# 7. Data Flow

Example: Add item flow

1. User sends message in Telegram
2. Handler parses input
3. Handler calls AddItemService
4. Service loads Purchase from repository
5. Service updates domain objects
6. Service persists changes
7. Service returns DTO/result
8. Handler formats response

This keeps transport concerns separate from business logic.

---

# 8. Persistence Strategy

Initial approach:
- SQLite for simplicity
- Single file database

Why:
- Zero setup
- Portable
- Easy backups

Future options:
- Postgres
- Cloud sync
- Multi-device storage

Persistence should be abstracted behind repositories.

---

# 9. Testing Strategy

Primary testing target:
Services layer.

Test types:
- Unit tests for services
- Domain behavior tests
- Minimal handler tests

Avoid:
- Heavy integration tests early
- Mocking everything

Focus on business correctness.

---

# 10. Naming Conventions

All code must use English naming.

Examples:

Classes:
- Purchase
- PurchaseItem
- PurchaseService

Methods:
- add_item
- remove_item
- calculate_total

Files:
snake_case only.

Avoid mixed languages in code.

---

# 11. Error Handling

Principles:
- Fail fast in services
- Use explicit exceptions
- Avoid silent failures

Recommended:
- DomainError
- ValidationError
- NotFoundError

Handlers should translate exceptions into user-friendly messages.

---

# 12. State Management

Conversation state lives in handlers.

Business state lives in domain objects.

Never mix:
- UI state
- Domain state

This keeps logic portable to future interfaces (API, Web).

---

# 13. Logging

Logging belongs in infrastructure.

Recommended:
- Structured logs
- Info for flows
- Error for failures

Avoid logging inside domain.

---

# 14. Configuration

All configuration must come from environment variables.

Examples:
- TELEGRAM_TOKEN
- DATABASE_PATH
- ENVIRONMENT

Use a central config loader.

Do not scatter env reads across the codebase.

---

# 15. Extensibility

This architecture supports future growth:

## Reports
Add reporting services without touching handlers.

## REST API
Add api/ layer parallel to handlers.

## Web UI
Reuse services and domain.

## Multi-user
Introduce User entity and ownership rules.

## Cloud sync
Replace repository implementations.

No rewrite required.

---

# 16. Anti-Patterns to Avoid

Do NOT:

- Put business logic in handlers
- Use global state
- Create unnecessary interfaces
- Overuse dependency injection frameworks
- Introduce microservices early
- Mix Portuguese in code naming

Keep it simple and consistent.

---

# 17. When to Refactor

Refactor when:

- Services exceed ~300 lines
- Domain rules become complex
- Multiple storage strategies appear
- Multiple interfaces (API + Bot) exist

Refactor incrementally, not all at once.

---

# 18. Architectural Decisions

Key decisions:

- Modular Monolith over Microservices
- Layered design over Clean Architecture purity
- SQLite first, scale later
- English-only codebase
- Services as the primary abstraction

These decisions favor pragmatism over ideology.

---

# 19. Final Notes

This architecture is intentionally:

- Simple
- Explicit
- Pragmatic
- Evolvable

If in doubt, choose:

Clarity > Cleverness

Readable code today is more valuable than perfect architecture tomorrow.

Keep the system understandable for your future self.

## Persistence Strategy

The SQLite database is a runtime artifact and must not be versioned.
Each environment manages its own database instance.

The application must be capable of creating the database automatically
if it does not exist.