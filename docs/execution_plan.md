# CartBot Execution Plan

## TL;DR

Build CartBot (a Telegram shopping list bot) incrementally following the Modular Monolith architecture. Each phase adds one capability layer—starting with project bootstrap, then infra, domain, services, handlers, and finally features. Each step takes 5–10 minutes and is independently testable. Phases respect the dependency direction: Handlers → Services → Domain ← Infra.

---

## How to Use This Plan

1. **Read the entire plan first** — understand the phases and dependencies
2. **Work through steps sequentially** — each step builds on the previous
3. **Follow the validation instructions** — confirm each step works before continuing
4. **Use "Stop condition" to know when it's safe to move forward** — don't skip validation
5. **Check "Common mistakes to avoid"** — these are AI hallucination guardrails
6. **Use the progress checklist** — mark off each step as you complete it
7. **Reference the .env file** — keep your environment variables consistent

---

## Phase 1: Bootstrap

### Step 1.1 — Create Project Skeleton

**Goal:** Basic folder structure and main entry point exist; no functionality yet.

**Files to create or modify:**
- `app/__init__.py` (empty, marks app as package)
- `app/main.py` (empty entry point)
- `tests/__init__.py` (empty)
- `.gitignore` (prevent tracking .db, .env, `__pycache__`)
- `.env` (template for environment variables)

**Instructions:**
1. Create folders: `app/`, `app/handlers/`, `app/services/`, `app/domain/`, `app/infra/`, `app/common/`, `tests/`, `data/`
2. Create empty `__init__.py` files in `app/`, `app/handlers/`, `app/services/`, `app/domain/`, `app/infra/`, `app/common/`, `tests/`
3. Create `app/main.py` with a single comment: `# CartBot entry point`
4. Create `.gitignore` with entries: `*.db`, `*.sqlite`, `.env`, `__pycache__/`, `.pytest_cache/`, `*.pyc`, `.venv/`, `venv/`
5. Create `.env` with template variables (see step 1.2)
6. Create `README.md` placeholder if not present (or verify existing one)

**Validation:**
- Folder structure matches the architecture diagram from docs
- All `__init__.py` files exist (run: `find . -name '__init__.py' | wc -l` — should be 8)
- `.gitignore` prevents `.db` files from being committed (test: create dummy `.db`, run `git status` — should not list it)

**Stop condition:**
- All folders created
- All `__init__.py` files in place
- `.env` file exists with placeholder variables
- `.gitignore` is effective

**Common mistakes to avoid:**
- ❌ Forgetting `__init__.py` in any subdirectory (breaks imports)
- ❌ Adding `.db` to version control instead of `.gitignore`
- ❌ Creating `app.py` instead of `app/` as a package
- ❌ Not creating the `data/` folder for runtime artifacts

---

### Step 1.2 — Create Config Loader

**Goal:** Centralized environment variable loading; single source of truth for configuration.

**Files to create or modify:**
- `app/infra/config.py` (read environment, expose as constants)
- `.env` (update with complete variable list)

**Instructions:**
1. Create `app/infra/config.py` that:
   - Imports `os`
   - Defines constants for `TELEGRAM_TOKEN`, `DATABASE_PATH` (default: `data/cartbot.db`), `LOG_LEVEL` (default: `INFO`)
   - Raises `ValueError` if `TELEGRAM_TOKEN` is missing
   - Exposes a dictionary or namespace (e.g., `Config` dataclass) with all values
2. Update `.env` template with:
   ```
   TELEGRAM_TOKEN=your_token_here
   DATABASE_PATH=data/cartbot.db
   LOG_LEVEL=INFO
   ```
3. Create `app/infra/__init__.py` with `from .config import Config` (or equivalent)

**Validation:**
- Import `Config` from `app.infra` — should not raise errors
- Print config values — should match `.env`
- Remove `TELEGRAM_TOKEN` from `.env`, run config loader — should raise clear `ValueError`
- Verify no `os.getenv()` calls scattered elsewhere yet

**Stop condition:**
- `Config` class/namespace loads without errors
- All required variables have defaults or are validated
- No environment variables hardcoded anywhere else

**Common mistakes to avoid:**
- ❌ Scattering `os.getenv()` calls throughout the codebase
- ❌ Failing silently if `TELEGRAM_TOKEN` is missing (causes mysterious runtime errors later)
- ❌ Not providing sensible defaults for `DATABASE_PATH` and `LOG_LEVEL`
- ❌ Putting config in `handlers/` or `services/` (it's an infra concern)

---

### Step 1.3 — Set Up Logging

**Goal:** Centralized logging configuration; all logs go through logging module, not print().

**Files to create or modify:**
- `app/infra/logger.py` (centralized logging setup)
- `app/main.py` (initialize logging)

**Instructions:**
1. Create `app/infra/logger.py`:
   - Import `logging` and `Config`
   - Create a function `setup_logging(level=Config.LOG_LEVEL)` that configures the root logger
   - Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
   - Add a `StreamHandler` (console output)
   - Return the logger or None (side effect is acceptable)
2. In `app/main.py`:
   - Import and call `setup_logging()` at the very top
   - Add a log line: `logger.info("CartBot starting...")`
3. Update `app/infra/__init__.py` to also export `setup_logging`

**Validation:**
- Run `app/main.py` (python app/main.py) — should print a log line with timestamp, no tracebacks
- Change `LOG_LEVEL` in `.env` to `DEBUG` — logs should appear in DEBUG level
- Verify no `print()` statements in code (scan existing files)

**Stop condition:**
- Logging initializes without errors
- Log output appears on console with correct format
- `Config.LOG_LEVEL` controls verbosity

**Common mistakes to avoid:**
- ❌ Using `print()` instead of logging module
- ❌ Setting up logging in multiple places (do it once in main)
- ❌ Logging inside domain classes (don't do this)
- ❌ Not using module-level loggers in each file (`logger = logging.getLogger(__name__)`)

---

## Phase 2: Infrastructure

### Step 2.1 — Initialize SQLite Database

**Goal:** Database file creation and schema setup; the database auto-creates if missing.

**Files to create or modify:**
- `app/infra/database.py` (SQLite connection and schema)
- `app/main.py` (call database initialization)

**Instructions:**
1. Create `app/infra/database.py`:
   - Import `sqlite3`, `os`, `logging`, `Config`
   - Create function `init_db(db_path=Config.DATABASE_PATH)`:
     - Create directory `data/` if it doesn't exist
     - Connect to SQLite at db_path
     - Create two tables if they don't exist:
       - `purchases` (id INT PRIMARY KEY, created_at TIMESTAMP, finished_at TIMESTAMP NULL)
       - `purchase_items` (id INT PRIMARY KEY, purchase_id INT FOREIGN KEY, item_name TEXT, quantity INT, unit_price REAL, created_at TIMESTAMP)
     - Commit and close connection
     - Log success: `logger.info(f"Database initialized at {db_path}")`
   - Create function `get_db_connection(db_path=Config.DATABASE_PATH)` that returns an open connection (for later use)
2. In `app/main.py`:
   - Import and call `init_db()` after logging setup
   - Add log: `logger.info("Database ready")`
3. Update `app/infra/__init__.py` to export `init_db` and `get_db_connection`

**Validation:**
- Run `app/main.py` — database file should appear at `data/cartbot.db`
- Inspect database: `sqlite3 data/cartbot.db ".tables"` — should list `purchases` and `purchase_items`
- Run again — should not error (idempotent)
- Delete database, run again — should recreate it
- Check schema: `sqlite3 data/cartbot.db ".schema purchases"` — should show table definition

**Stop condition:**
- Database file created at correct path
- Both tables exist with correct columns
- Init is idempotent (safe to run multiple times)
- No hardcoded paths (use Config)

**Common mistakes to avoid:**
- ❌ Committing `.db` files to git (should be in `.gitignore`)
- ❌ Not creating `data/` directory before creating database
- ❌ Using hardcoded paths instead of `Config.DATABASE_PATH`
- ❌ Not making init idempotent (CREATE TABLE IF NOT EXISTS)
- ❌ Forgetting FOREIGN KEY constraints

---

### Step 2.2 — Create Base Repository Interface

**Goal:** Define contract that all repositories must follow; no implementation yet.

**Files to create or modify:**
- `app/infra/repositories/base.py` (abstract base class)
- `app/infra/repositories/__init__.py` (empty marker)

**Instructions:**
1. Create folder `app/infra/repositories/`
2. Create `app/infra/repositories/__init__.py` (empty)
3. Create `app/infra/repositories/base.py`:
   - Import `abc` and `typing`
   - Define abstract class `BaseRepository`:
     - Abstract method `save(entity)` → None
     - Abstract method `get_by_id(id)` → entity or None
     - Abstract method `delete(id)` → None
   - Keep it minimal; add methods only as needed
4. Update `app/infra/__init__.py` to note where repositories live (comment only)

**Validation:**
- Import `BaseRepository` from `app.infra.repositories.base` — no errors
- Try to instantiate directly — should raise `TypeError` (abstract class)
- Verify no actual implementations yet

**Stop condition:**
- Abstract base class exists
- Cannot be instantiated directly
- Contract is clear (3-4 methods max)

**Common mistakes to avoid:**
- ❌ Over-designing the interface (add methods only when needed)
- ❌ Adding `__init__` or concrete logic to base class
- ❌ Mixing multiple responsibilities in one repository
- ❌ Not using `@abc.abstractmethod` decorator

---

### Step 2.3 — Implement SQLite Repositories

**Goal:** Persist and retrieve Purchase and PurchaseItem entities from SQLite.

**Files to create or modify:**
- `app/infra/repositories/purchase_repository.py` (CRUD for purchases and items)
- `app/infra/repositories/__init__.py` (export repositories)

**Instructions:**
1. Create `app/infra/repositories/purchase_repository.py`:
   - Import `BaseRepository`, `sqlite3`, `logging`
   - Create class `SQLitePurchaseRepository(BaseRepository)`:
     - `__init__(db_path)` — store path
     - `save(purchase)` — insert or update purchase and its items in DB
       - If `purchase.id` is None, insert new row and set ID
       - Delete existing items for this purchase, re-insert them
       - Commit transaction
     - `get_by_id(purchase_id)` — query DB, reconstruct Purchase object with items
       - Return None if not found
     - `delete(purchase_id)` — delete purchase and its items
   - Do NOT create domain classes yet; just sketch the data structure
2. Update `app/infra/repositories/__init__.py`:
   - Export `SQLitePurchaseRepository`

**Validation:**
- Import `SQLitePurchaseRepository` — no errors
- Create instance with database path — no errors
- Call `save()` with a mock object (dict works) — data should appear in DB
- Call `get_by_id()` on saved object — should retrieve it
- Call `delete()` — should remove from DB
- Verify schema alignment (columns match inserts)

**Stop condition:**
- Repository methods execute without errors
- Data persists in SQLite
- Retrieval reconstructs data accurately
- No business logic inside repository (just SQL + data marshaling)

**Common mistakes to avoid:**
- ❌ Hardcoding database paths (use passed-in path)
- ❌ Not closing connections properly (use context managers or explicit close)
- ❌ Putting validation or business logic in repository
- ❌ Forgetting to handle NULL values (e.g., `finished_at`)
- ❌ Mixing SQL queries with domain object creation (separate concerns)

---

## Phase 3: Domain Layer

### Step 3.1 — Create Purchase Domain Entity

**Goal:** Pure Python class representing a Purchase with invariants; no database or framework knowledge.

**Files to create or modify:**
- `app/domain/purchase.py` (Purchase entity and item value object)

**Instructions:**
1. Create `app/domain/purchase.py`:
   - Define class `PurchaseItem` (value object):
     - Fields: `name`, `quantity`, `unit_price` (all required)
     - Constructor validates that quantity > 0 and unit_price > 0
     - Method `total_price()` → quantity × unit_price
     - Immutable or use `@dataclass(frozen=True)`
   - Define class `Purchase` (aggregate root):
     - Fields: `id` (can be None initially), `items` (list of PurchaseItem), `created_at` (timestamp), `finished_at` (optional, None if active)
     - Constructor ensures `items` is a list
     - Method `add_item(name, quantity, unit_price)` → creates PurchaseItem, appends to list
     - Method `remove_item(index)` → removes item by index, validates index exists
     - Method `total()` → sum of all item totals
     - Method `item_count()` → count of items
     - Raise custom exceptions (NotFoundError, ValidationError) for invariant violations
2. Create `app/domain/__init__.py`:
   - Export `Purchase`, `PurchaseItem`

**Validation:**
- Import `Purchase` and `PurchaseItem` from `app.domain` — no errors
- Create a Purchase, add items manually → `total()` should calculate correctly
- Try to add item with negative quantity → should raise exception
- Try to remove non-existent item → should raise exception
- Verify no database or Telegram imports in file

**Stop condition:**
- Domain classes exist with basic invariants
- Methods execute correctly
- Pure Python, no external dependencies
- Exceptions are meaningful (not generic)

**Common mistakes to avoid:**
- ❌ Importing database or Telegram libraries into domain
- ❌ Adding `id` generation logic (that's infra responsibility)
- ❌ Not validating invariants (unit_price > 0, etc.)
- ❌ Allowing direct mutation of `items` list (use add_item/remove_item)
- ❌ Using mutable default arguments like `items=[]`

---

### Step 3.2 — Define Custom Exceptions

**Goal:** Consistent error handling; services and handlers can distinguish between error types.

**Files to create or modify:**
- `app/domain/exceptions.py` (domain-level exceptions)

**Instructions:**
1. Create `app/domain/exceptions.py`:
   - Define base exception `DomainError(Exception)`
   - Define `ValidationError(DomainError)` — for invariant violations
   - Define `NotFoundError(DomainError)` — for missing entities
   - Add docstring to each explaining when to use
2. Update `app/domain/__init__.py`:
   - Export all exceptions

**Validation:**
- Import exceptions from `app.domain` — no errors
- Raise `NotFoundError("Purchase not found")` in a test — should be catchable
- Verify inheritance: `except DomainError` should catch subclasses

**Stop condition:**
- Three custom exceptions defined
- Can be imported and used
- Inheritance structure is correct

**Common mistakes to avoid:**
- ❌ Creating too many exception types (keep it simple)
- ❌ Not providing helpful error messages
- ❌ Forgetting to export them from `__init__.py`

---

## Phase 4: Services Layer

### Step 4.1 — Create PurchaseService

**Goal:** Business logic for purchase operations; orchestrates domain and repository; framework-agnostic.

**Files to create or modify:**
- `app/services/purchase_service.py` (business operations)
- `app/services/__init__.py` (export service)

**Instructions:**
1. Create `app/services/purchase_service.py`:
   - Import `Purchase`, `PurchaseItem`, exceptions from domain; repository from infra
   - Create class `PurchaseService`:
     - `__init__(repository)` — store repository reference
     - `start_purchase()` → creates new Purchase, saves to repo, returns purchase ID
     - `add_item(purchase_id, name, quantity, unit_price)` → loads purchase, adds item, saves, returns updated total
     - `remove_item(purchase_id, item_index)` → loads purchase, removes item, saves, returns updated total
     - `get_purchase(purchase_id)` → loads and returns purchase (for UI/handlers)
     - `finish_purchase(purchase_id)` → loads purchase, sets `finished_at`, saves, returns total
     - All methods raise `NotFoundError` if purchase not found
     - All arithmetic/validation happens on domain objects, not in service
2. Update `app/services/__init__.py`:
   - Export `PurchaseService`

**Validation:**
- Import `PurchaseService` from `app.services` — no errors
- Create service with mock repository (dict-based or simple class)
- Call `start_purchase()` — should return an ID
- Call `add_item()` with valid data — should succeed
- Call `add_item()` with invalid data (negative quantity) — should raise exception
- Call `get_purchase()` on non-existent ID — should raise `NotFoundError`
- Verify no Telegram or database queries in service (only calls to repository)

**Stop condition:**
- Service methods work with mock repository
- Business logic is tested independently
- No framework-specific code
- Error handling is clear

**Common mistakes to avoid:**
- ❌ Putting SQL queries or database operations in service
- ❌ Calling `purchase.items[0]` instead of using domain methods
- ❌ Duplicating validation logic (let domain objects validate)
- ❌ Not raising exceptions for invalid operations
- ❌ Making service stateful (should be stateless)

---

## Phase 5: Telegram Adapter

### Step 5.1 — Set Up Telegram Bot Bootstrap

**Goal:** Bot initializes and connects to Telegram; basic message loop ready.

**Files to create or modify:**
- `app/handlers/telegram_bot.py` (bot initialization and dispatcher)
- `app/main.py` (wire up bot startup)
- `requirements.txt` (add python-telegram-bot dependency)

**Instructions:**
1. Create `requirements.txt`:
   - Add `python-telegram-bot==20.x` (latest stable, or specify version)
   - Add `python-dotenv` (for loading .env)
2. Create `app/handlers/telegram_bot.py`:
   - Import `logging`, `Config`, `Application` and `ContextTypes` from telegram.ext
   - Create function `create_app()` → returns `Application` instance configured with token
   - Create function `setup_handlers(app)` → placeholder for adding handlers later (add comment only)
   - Create function `run_bot(app)` → calls `app.run_polling()` with `drop_pending_updates=True`
   - Add logging: "Bot started", "Bot stopped"
3. Update `app/main.py`:
   - Import `create_app`, `setup_handlers`, `run_bot` from handlers
   - After DB init, create bot: `app = create_app()`
   - Call `setup_handlers(app)` (no-op for now)
   - Call `run_bot(app)` to start polling
4. Update `app/handlers/__init__.py`:
   - Export the three functions

**Validation:**
- Run `app/main.py` — bot should start and print "Bot started"
- Verify token is read from `Config.TELEGRAM_TOKEN`
- Kill process (Ctrl+C) — should log "Bot stopped" gracefully
- If `TELEGRAM_TOKEN` is invalid, bot should start but fail on first message (expected for now)

**Stop condition:**
- Bot initializes without crashing
- Logging shows startup/shutdown messages
- No handlers wired yet (that's next step)

**Common mistakes to avoid:**
- ❌ Using old `telegram.Bot` API instead of `Application`
- ❌ Not handling shutdown gracefully (use `run_polling`)
- ❌ Hardcoding token (use Config)
- ❌ Adding handlers before test (do it in a separate step)
- ❌ Forgetting to install `python-telegram-bot`

---

### Step 5.2 — Implement /start Handler

**Goal:** Respond to `/start` command; test handler + service integration.

**Files to create or modify:**
- `app/handlers/handlers.py` (command handlers)
- `app/handlers/telegram_bot.py` (register handler)

**Instructions:**
1. Create `app/handlers/handlers.py`:
   - Import `logging`, `Update`, `ContextTypes`, `CommandHandler` from telegram.ext
   - Import `PurchaseService` from services
   - Create function `start_handler(update, context)`:
     - Extract `user_id` from update (for future multi-user support; log it)
     - Call `context.bot_data['service'].start_purchase()` (service lives in bot context for now)
     - Send message to user: "Shopping list started. /add_item to begin."
     - Log: `logger.info(f"Purchase started for user {user_id}")`
   - Wrap in try/except; on exception, send "Error: [message]" to user
2. Update `app/handlers/telegram_bot.py`:
   - In `create_app()`, store service in `app.bot_data['service'] = PurchaseService(repository)`
     - Instantiate repo with path from Config
   - In `setup_handlers()`, register the `/start` handler
3. Update `app/handlers/__init__.py`:
   - Export handler functions (or leave closed for now)

**Validation:**
- Run bot, send `/start` — should respond with greeting
- Send `/start` again — should create a new purchase
- Check logs — should show purchase started messages
- If database is corrupted, handler should fail gracefully (error message to user)

**Stop condition:**
- Bot responds to `/start` command
- Service integration works (call to repository succeeds)
- Error handling is in place
- No hardcoded strings (use constants or config later)

**Common mistakes to avoid:**
- ❌ Passing service instance incorrectly (use context.bot_data)
- ❌ Not extracting user_id (needed for multi-user later)
- ❌ Letting exceptions bubble up to Telegram (crash bot)
- ❌ Not awaiting async functions (use `async def` and `await`)
- ❌ Forgetting to register handler in `setup_handlers()`

---

## Phase 6: Core Features (MVP)

### Step 6.1 — Implement /add_item Handler

**Goal:** Users can add items to active purchase; update totals.

**Files to create or modify:**
- `app/handlers/handlers.py` (add new handler)
- `app/handlers/telegram_bot.py` (register handler)

**Instructions:**
1. In `app/handlers/handlers.py`:
   - Create function `add_item_handler(update, context)`:
     - Parse input: `/add_item [name] [quantity] [unit_price]`
       - Validate: 3 arguments, quantity and price are numbers
       - Send usage message if invalid
     - Call `service.add_item(purchase_id, name, quantity, unit_price)`
       - Store purchase_id in `context.user_data['purchase_id']` (from /start)
     - On success, send: "Item added. Total: $[total]"
     - On error, send: "Error: [message]"
   - Log each operation
2. Update `start_handler()`:
   - After creating purchase, store ID in context: `context.user_data['purchase_id'] = purchase_id`
3. Update `setup_handlers()` in telegram_bot.py:
   - Register `/add_item` handler
4. Update `.env` template (if needed for currency or limits)

**Validation:**
- Run bot, send `/start`
- Send `/add_item milk 2 1.50` — should respond with total
- Send `/add_item` (no args) — should show usage
- Send `/add_item item abc 2.0` — should reject (invalid quantity type)
- Send multiple items — total should accumulate

**Stop condition:**
- Items are added to the purchase
- Totals calculate correctly
- Error handling is clear (invalid input rejected)
- State (purchase_id) persists in conversation

**Common mistakes to avoid:**
- ❌ Not storing purchase_id in context (can't find purchase in add_item)
- ❌ Not validating input (crash on invalid number)
- ❌ Forgetting to pass arguments correctly to service
- ❌ Not handling the case where /start hasn't been called yet (no purchase_id)

---

### Step 6.2 — Implement /view_total Handler

**Goal:** Show current total and item count.

**Files to create or modify:**
- `app/handlers/handlers.py` (add handler)
- `app/handlers/telegram_bot.py` (register)

**Instructions:**
1. In `app/handlers/handlers.py`:
   - Create function `view_total_handler(update, context)`:
     - Get `purchase_id` from `context.user_data`
     - Call `service.get_purchase(purchase_id)`
     - Format response: "Total: $[amount] | Items: [count]"
     - On error (no purchase), send: "No active purchase. Use /start to begin."
   - Log retrieval
2. Register handler in `setup_handlers()`

**Validation:**
- Start purchase, add items, send `/view_total` — should show correct total
- Send `/view_total` without starting purchase — should show "no active purchase" message

**Stop condition:**
- Correct totals displayed
- Graceful error if no purchase active

**Common mistakes to avoid:**
- ❌ Not checking if purchase_id exists in user_data
- ❌ Division by zero if no items (check item_count > 0)

---

### Step 6.3 — Implement /list_items Handler

**Goal:** Show all items in current purchase.

**Files to create or modify:**
- `app/handlers/handlers.py` (add handler)
- `app/handlers/telegram_bot.py` (register)

**Instructions:**
1. In `app/handlers/handlers.py`:
   - Create function `list_items_handler(update, context)`:
     - Get purchase, call `service.get_purchase(purchase_id)`
     - Format each item: "1. Milk × 2 @ $1.50 = $3.00"
     - Send formatted list or "No items yet" if empty
   - Log
2. Register handler

**Validation:**
- Add items, send `/list_items` — should show all with indices
- Start fresh purchase, send `/list_items` — should show "no items"

**Stop condition:**
- All items listed with correct format
- Indices align with removal (step 6.5)

**Common mistakes to avoid:**
- ❌ 0-indexed vs 1-indexed (user-facing should be 1-indexed, like "1.", "2.")
- ❌ Forgetting unit prices in output

---

### Step 6.4 — Implement /edit_item Handler

**Goal:** Modify an existing item (quantity or price).

**Files to create or modify:**
- `app/services/purchase_service.py` (add edit method)
- `app/handlers/handlers.py` (add handler)
- `app/handlers/telegram_bot.py` (register)

**Instructions:**
1. In `app/services/purchase_service.py`:
   - Add method `edit_item(purchase_id, item_index, quantity=None, unit_price=None)`:
     - Load purchase
     - If quantity is provided, validate and update
     - If price is provided, validate and update
     - Save and return updated total
     - Raise exception if item_index invalid
2. In handlers:
   - Create function `edit_item_handler(update, context)`:
     - Parse: `/edit_item [index] [new_quantity] [new_price]`
     - Validate index is in range
     - Call service, respond with new total
   - Log
3. Register handler

**Validation:**
- Add item, edit quantity, send `/list_items` — should show updated quantity
- Edit price, total should update
- Try to edit non-existent index — should error

**Stop condition:**
- Edits persist correctly
- Totals recalculate

**Common mistakes to avoid:**
- ❌ Mixing 0-indexed (internal) and 1-indexed (UI)
- ❌ Not re-saving after edit

---

### Step 6.5 — Implement /delete_item Handler

**Goal:** Remove an item from the list.

**Files to create or modify:**
- `app/handlers/handlers.py` (add handler)
- `app/handlers/telegram_bot.py` (register)

**Instructions:**
1. In handlers:
   - Create function `delete_item_handler(update, context)`:
     - Parse: `/delete_item [index]`
     - Call `service.remove_item(purchase_id, index)`
     - Confirm: "Item deleted. New total: $[amount]"
   - Log
2. Register handler

**Validation:**
- Add items, delete one, verify total and list update

**Stop condition:**
- Items removed correctly
- Total updates

---

### Step 6.6 — Implement /finish Handler

**Goal:** Complete purchase and show final summary.

**Files to create or modify:**
- `app/services/purchase_service.py` (ensure finish method exists)
- `app/handlers/handlers.py` (add handler)
- `app/handlers/telegram_bot.py` (register)

**Instructions:**
1. In handlers:
   - Create function `finish_handler(update, context)`:
     - Call `service.finish_purchase(purchase_id)`
     - Send summary: "Purchase finished. Total: $[amount] | Items: [count]"
     - Clear purchase_id from context (for next purchase)
     - Log
   - Add prompt: "Use /start to begin a new purchase"
2. Register handler

**Validation:**
- Complete a purchase, verify it's marked as finished in DB
- Start new purchase after finishing — should have fresh purchase_id

**Stop condition:**
- Purchases marked complete
- Conversation reset for new purchase

**Common mistakes to avoid:**
- ❌ Not clearing context after finish (next /add_item will fail mysteriously)
- ❌ Not saving finished_at timestamp

---

## Phase 7: Polish

### Step 7.1 — Error Handling and User-Friendly Messages

**Goal:** All errors are caught and translated to user-friendly messages; no tracebacks shown to user.

**Files to create or modify:**
- `app/handlers/handlers.py` (wrap all handlers)
- `app/handlers/telegram_bot.py` (optional: error handler)

**Instructions:**
1. Create a decorator in `app/handlers/handlers.py`:
   - `def safe_handler(func)` → wraps handler to catch exceptions
   - Logs exception at ERROR level
   - Sends "An error occurred. Please try again." to user (or specific message for known errors)
2. Apply decorator to all handlers
3. Optionally, add global error handler in `telegram_bot.py` for uncaught exceptions

**Validation:**
- Corrupt database, send command — user sees friendly message, logs show full traceback
- Intentionally raise exception in handler — user protected from stack trace

**Stop condition:**
- No raw exceptions visible to user
- Logs contain full details for debugging

**Common mistakes to avoid:**
- ❌ Showing raw exception messages to user
- ❌ Not logging exceptions (can't debug)

---

### Step 7.2 — Improve Logging

**Goal:** Strategic logging at key points; helps with debugging and understanding flow.

**Files to create or modify:**
- All handlers and services (add log statements)

**Instructions:**
1. Add logging at entry/exit of key operations:
   - INFO: "Purchase started", "Item added", "Purchase finished"
   - WARNING: "Invalid input", "Item not found" (still handled gracefully)
   - ERROR: Unhandled exceptions
2. Use format: `logger.info(f"Action: {purchase_id}, Items: {item_count}")`
3. Avoid logging inside domain classes

**Validation:**
- Run through happy path, check logs are informative
- Intentionally break something, verify logs help diagnose

**Stop condition:**
- Key operations logged
- Logs are readable and useful

---

### Step 7.3 — UX Improvements in Messages

**Goal:** Messages are clear, concise, and helpful.

**Files to create or modify:**
- `app/handlers/handlers.py` (refine response messages)
- Consider: `app/handlers/messages.py` (optional: centralize message templates)

**Instructions:**
1. Review all user-facing messages:
   - Confirm instructions are clear (e.g., `/add_item milk 2 1.50`)
   - Use consistent formatting (currency, indentation)
   - Add helpful hints (e.g., "Use /list_items to see all items")
2. Optional: Create `app/handlers/messages.py` with message constants:
   - `PURCHASE_STARTED = "Shopping list started..."`
   - `ITEM_ADDED = "Item added. Total: ${total}"`
   - Import and use in handlers

**Validation:**
- Walk through entire user flow; messages make sense
- Formatting is consistent

**Stop condition:**
- All user messages are clear and helpful

---

## Phase 8: UX & Localization (V2)

> This phase refines the MVP UX without changing core business rules.
> Focus areas: message clarity, formatting consistency, safer parsing, and localization.
> No database refactors. No architectural overhauls. Pure UX evolution.

> Scope
> This phase improves user experience without modifying:
> - Database schema
> - Domain rules
> - Core services
>
> All changes must remain backward-compatible at the data level.

---

### Step 8.1 — Message Formatting Layer ✅

**Goal:** Remove duplicated formatting logic and standardize how messages look.

**Files to create or modify:**
- `app/common/formatters.py` (new helpers module)
- `app/handlers/handlers.py` (update all messages to use helpers)

**Instructions:**
1. Create `app/common/formatters.py` with helpers:
   - `format_currency(value: float) -> str`: Format money with a language-specific currency symbol
     - English: `U$ 5.00`
     - Portuguese: `R$ 5.00`
     - 11.567 → `U$ 11.57` or `R$ 11.57` depending on language
   - `append_help_hint(text: str) -> str`: Add footer with help link
     - Always appends: `—\nNeed help? Use /help`
   - `format_command_block(commands: list[str]) -> str`: Format command lists
     - Commands start on new line
     - Use bullet points (•) or numbers
2. Update all handlers to use these helpers
3. Remove manual formatting strings from handlers

**Validation:**
- Test `format_currency()`: verify rounding (11.567 → 11.57)
- Test `append_help_hint()`: verify footer appears on all messages
- Run /add_item, /list_items, /view_total — all should use helpers
- Messages should look identical across all handlers

**Stop condition:**
- All formatting logic centralized in formatters.py
- No handler hardcodes money format or help hint
- All messages are consistent

**Common mistakes to avoid:**
- ❌ Forgetting to import helpers in handlers
- ❌ Still having hardcoded R$ strings in handlers after refactor
- ❌ Rounding errors in currency (use Decimal for precise math)
- ❌ Not testing edge cases (0.00, 999.995, etc.)

**Example BEFORE:**
```
Total: R$ 25.00 Use /list_items to see details
```

**Example AFTER:**
```
Total: R$ 25.00

Use /list_items to see details

—
Need help? Use /help
```
---

### Step 8.2 — Global Help Command ✅

**Goal:** Make commands discoverable and self-documenting.

**Files to create or modify:**
- `app/handlers/handlers.py` (add /help handler)
- `app/handlers/telegram_bot.py` (register /help)

**Instructions:**
1. Create `help_handler(update, context)` that sends:
   ```
   Available Commands
   
   Session
   /start — start or resume a purchase
   /finish — finish current purchase
   
   Items
   /add_item Name | qty | price
   /edit_item index qty price
   /delete_item index
   
   Overview
   /view_total — show total
   /list_items — show all items
   ```
2. Use message formatter to append help hint
3. Format commands using `format_command_block()` helper
4. Ensure mobile readability (short lines, clear structure)
5. Register `/help` command in setup_handlers()

**Validation:**
- Run `/help` — should receive structured command list
- On mobile (simulate narrow screen) — should be readable
- All command descriptions match actual functionality

**Stop condition:**
- /help command works and lists all available commands
- No emojis or technical jargon
- User can understand every command

**Common mistakes to avoid:**
- ❌ Using emojis (requested: professional tone only)
- ❌ Listing commands that don't exist yet
- ❌ Help text too long or cluttered
- ❌ Forgetting to register handler in telegram_bot.py

---

### Step 8.3 — Resume / New Purchase Flow

**Goal:** Prevent multiple active purchases and make sessions explicit.

**Files to create or modify:**
- `app/handlers/handlers.py` (update /start logic)
- `app/services/purchase_service.py` (add session helpers if needed)

**Instructions:**
1. Update `start_handler()` to check for active purchase:
   - Query repository: does user have unfinished purchase?
   - If NO: send "New purchase started. Use /add_item to add your first item."
   - If YES: show resume prompt:
     ```
     You have an active purchase from:
     Market: Carrefour
     Date: 2026-03-01
     
     Type:
     • /resume — continue this purchase
     • /new — finish and start a new one
     ```
2. Create `resume_handler(update, context)`: Restore session and show total
   - Load existing purchase from context or query by user
   - Display full purchase details
   - Show /add_item prompt
3. Create `new_handler(update, context)`: Finish current, start fresh
   - Call `service.finish_purchase(current_purchase_id)`
   - Create and store new purchase_id
   - Send "New purchase started" message
4. Update context storage: maintain purchase_id for session

**Validation:**
- Start purchase, send /start without finishing — should see resume prompt
- Run /resume — should restore session
- Run /new — should finish old purchase and start new one
- Verify DB: old purchase marked as finished, new one active

**Stop condition:**
- Only ONE active purchase per user
- /start shows resume options if purchase exists
- /resume and /new work correctly
- All sessions clear on /finish

**Common mistakes to avoid:**
- ❌ Creating duplicate active purchases
- ❌ Not persisting purchase_id properly in context
- ❌ Losing old purchase data when starting new one
- ❌ Forgetting to update /start handler logic

**Example (NO active purchase):**
```
New purchase started.

Use /add_item to add your first item.

—
Need help? Use /help
```

**Example (ACTIVE purchase exists):**
```
You have an active purchase from:
Market: Carrefour
Date: 2026-03-01

Type:
• /resume — continue this purchase
• /new — finish and start a new one

—
Need help? Use /help
```

---

### Step 8.4 — Pipe-Based Item Parsing ✅

**Goal:** Fix parsing ambiguity and support numbers in names.

**Files to create or modify:**
- `app/handlers/handlers.py` (update add_item_handler parsing)
- `app/common/validators.py` (add pipe parser)

**Instructions:**
1. Create parser in `app/common/validators.py`:
   ```python
   def parse_add_item_input(text: str) -> tuple[str, int, float]:
       parts = text.split('|')
       if len(parts) != 3:
           raise ValueError("Expected format: Name | qty | price")
       name = parts[0].strip()
       qty = int(parts[1].strip())
       price = float(parts[2].strip())
       return name, qty, price
   ```
2. Update `add_item_handler()` to use pipe parser, with a
   backward-compatible fallback to original whitespace syntax.
3. Validation rules:
   - Split by `|` (pipe character)
   - Trim whitespace from each part
   - Accept integer and decimal prices: 5, 5.5, 5.50
   - Accept integer quantities only
   - Reject format: `/add_item Milk 2 5` (spaces instead of pipes)
4. On parse error, send:
   ```
   Invalid format.
   
   Use:
   /add_item Name | qty | price
   
   Example:
   /add_item Milk | 2 | 5.50
   
   —
   Need help? Use /help
   ```

**Validation:**
- Test valid: `/add_item Milk | 2 | 5`
- Test valid: `/add_item Banana | 1 | 3.5`
- Test valid: `/add_item Mortadela 200g | 1 | 11.50` (numbers in name OK)
- Test invalid: `/add_item Milk 2 5` (spaces instead of pipes) — should error
- Test invalid: `/add_item Milk | 2.5 | 5` (decimal qty) — should error

**Stop condition:**
- Pipe parsing works correctly
- Numbers in item names supported
- Backward compatibility preserved
- All invalid inputs rejected with helpful message

**Common mistakes to avoid:**
- ❌ Allowing decimal quantities (should be int only)
- ❌ Not trimming whitespace before conversion
- ❌ Catching exceptions too broadly (hide real parse errors)
- ❌ Forgetting to update help text in error message

**Valid inputs:**
```
/add_item Milk | 2 | 5
/add_item Banana | 1 | 3.5
/add_item Mortadela 200g | 1 | 11.50
```

**Invalid inputs:**
```
/add_item Milk 2 5
```

**Error response:**
```
Invalid format.

Use:
/add_item Name | qty | price

Example:
/add_item Milk | 2 | 5.50

—
Need help? Use /help
```

---

### Step 8.5 — UX Message Standardization ✅

**Goal:** Make all responses visually predictable.

**Files to create or modify:**
- `app/handlers/handlers.py` (all handlers)
- `app/common/formatters.py` (add message template helpers)

**Instructions:**
1. Establish message rules:
   - Main content first (e.g., item list, total)
   - Commands ALWAYS start on new line
   - Help hint ALWAYS at bottom (use `append_help_hint()`)
   - Use blank lines for spacing readability
2. Create template helpers for common patterns:
   - `format_item_list(items: list[Purchase]) -> str`
   - `format_total(purchase: Purchase) -> str`
   - `format_empty_state(context: str) -> str`
3. Audit all handlers and reformat messages:
   - /start, /add_item, /list_items, /edit_item, /delete_item, /view_total, /finish, /help
   - All must follow the same visual structure
4. Test on narrow screens to ensure readability

**Validation:**
- Run complete flow: /start → /add_item → /list_items → /edit_item → /view_total → /finish
- Every message should have:
  - Clear main content
  - Commands on new lines (if applicable)
  - Help hint at bottom
  - Consistent spacing
- No message should feel cramped or unstructured

**Stop condition:**
- All messages follow same visual structure
- Mobile readability confirmed
- Conversation feels natural and predictable

**Common mistakes to avoid:**
- ❌ Mixing message styles (some with hints, some without)
- ❌ Commands inline with text (should be own lines)
- ❌ Forgetting help hint on error messages
- ❌ Lines too long for mobile (keep < 50 chars where possible)

**Example (/list_items):**
```
Items

1. Milk × 2 @ R$ 5.00 = R$ 10.00
2. Bread × 1 @ R$ 8.00 = R$ 8.00

Total: R$ 18.00

Use:
• /delete_item 1
• /edit_item 2 3 7.50

—
Need help? Use /help
```

**Example (Empty state):**
```
No items yet.

Use /add_item to add your first item.

—
Need help? Use /help
```

---

### Step 8.6 — Localization Layer (EN + PT-BR)

**Goal:** Support bilingual UX without overengineering.
- Default language: EN
- Fallback language: EN

**Files to create or modify:**
- `app/common/messages/messages_en.py` (new)
- `app/common/messages/messages_ptbr.py` (new)
- `app/common/messages/__init__.py` (new)
- `app/handlers/handlers.py` (use message dictionaries)

**Instructions:**
1. Create message structure:
   ```python
   # messages_en.py
   MESSAGES = {
       'START_NEW': 'New purchase started.\\n\\n...',
       'START_RESUME': 'You have an active purchase from: ...',
       'HELP_INTRO': 'Available Commands',
       'HELP_HINT': 'Need help? Use /help',
       'INVALID_FORMAT': 'Invalid format. Use: ...',
       # ... all message keys
   }
   ```
2. Create same structure in `messages_ptbr.py` with PT-BR translations
   - Localize currency symbol by language: English users see `U$`, Portuguese users see `R$`
   - Keep command names as /start, /add_item, etc. (universal)
3. Create language manager:
   ```python
   def get_message(language: str, key: str) -> str:
       messages = MESSAGES_EN if language == 'en' else MESSAGES_PTBR
       return messages.get(key, f'[Missing: {key}]')
   ```
4. Store language per user: `context.user_data['language'] = 'ptbr'`
5. Update all handlers to use `get_message()` instead of hardcoded strings

**Validation:**
- Default language: English
- Complete flow in both languages — no hardcoded strings
- Commands themselves remain universal (/start, /add_item, etc.)

**Stop condition:**
- All user-facing text in message dictionaries
- Language switching works
- No hardcoded messages in handlers
- PT-BR and EN complete and coherent

**Common mistakes to avoid:**
- ❌ Translating command names (/start must stay /start)
- ❌ Translating command names (/start, /add_item, etc.)
- ❌ Ignoring language-based currency symbol selection
- ❌ Leaving some messages hardcoded in handlers
- ❌ Incomplete translations (missing keys)
- ❌ Not persisting language choice

**Example (PT-BR):**
```
Compra iniciada.

Use /add_item para adicionar um item.

—
Precisa de ajuda? Use /help
```

---

### Step 8.7 — Tests Update for V2

**Goal:** Preserve reliability while evolving UX.
- Tests should prioritize behavior over exact string matching to reduce brittleness during UX iterations.

**Files to create or modify:**
- `tests/test_*.py` (update all existing tests)
- Create new test files as needed

**Instructions:**
1. Update existing test expectations:
   - Message snapshots have new formatting (helpers, hints, etc.)
   - Adjust assertions to match new message format
   - Do NOT delete old tests
2. Add new test suites:
   - `tests/test_formatters.py`: Test `format_currency()`, `append_help_hint()`, etc.
   - `tests/test_parsing.py`: Test pipe parser with valid/invalid inputs
   - `tests/test_sessions.py`: Test /start, /resume, /new flows
   - `tests/test_localization.py`: Test language switching, fallback
3. Validation tests:
   - Pipe parsing: valid and invalid inputs
   - Currency rounding edge cases (0.00, 999.995, etc.)
   - Language switching: persist and apply correctly
   - Session management: only ONE active purchase per user
4. Maintain deterministic output:
   - All tests should pass consistently
   - No flaky time-based assertions
   - Snapshot tests: update expected messages to match new format

**Validation:**
- Run full test suite: `pytest` — all should pass
- No regressions from Phase 7
- New tests cover all new features (formatters, pipe parsing, sessions, i18n)
- Coverage report should show >80% coverage for handlers

**Stop condition:**
- All old tests updated and passing
- All new tests added and passing
- Zero regressions
- Coverage maintained or improved

**Common mistakes to avoid:**
- ❌ Deleting old tests instead of updating them
- ❌ Skipping tests with `.skip` decorator (remove after feature complete)
- ❌ Not updating snapshot assertions for new message format
- ❌ Missing edge case tests (decimal rounding, language fallback, etc.)
- ❌ Flaky tests that depend on timing or external state

# Phase 9: UX Optimization & Controlled Flow (V3)

## Goal

Finalize UX optimization, enforce controlled command-only flows,
introduce mandatory store name, support batch item input, and guarantee
deterministic behavior for future scalability.

This document is fully aligned with the official Phase 9 checklist
order.

------------------------------------------------------------------------

# 9.1 --- Domain Update (store_name required)

Purchase entity must include:

store_name: str (required)

Rules: - Required field - Trim whitespace - Non-empty validation - Raise
ValidationError if empty

No purchase can exist without a store name.

------------------------------------------------------------------------

# 9.2 --- Database Migration (store_name NOT NULL)

Changes required:

-   Add `store_name` column to purchases table
-   NOT NULL constraint
-   Migration script required

Migration must ensure no legacy null values remain.

------------------------------------------------------------------------

# 9.3 --- Repository Update (persist & load store_name)

Repository must:

-   Persist store_name
-   Load store_name
-   Include store_name in resume logic
-   Include store_name in finish summary

------------------------------------------------------------------------

# 9.4 --- Service Layer Update (create_purchase with store_name)

Update signature:

create_purchase(store_name: str)

Rules:

-   Cannot create purchase without store_name
-   Resume logic must return store_name
-   Service validates before persistence

------------------------------------------------------------------------

# 9.5 --- Command Simplification (single-word commands)

Final Command List:

/start /continue /new /add /edit /delete /list /total /finish /help

Rules:

-   Exactly one word after `/`
-   No aliases
-   No free-text interpretation
-   Legacy commands must stop working
-   All flows must respond only to commands

------------------------------------------------------------------------

# 9.6 --- /start Localization Parameter Support

Accepted formats:

/start /start ptbr /start enus

Rules:

-   Default locale if omitted
-   ptbr sets PT-BR
-   enus sets EN-US
-   Any other parameter → structured error

------------------------------------------------------------------------

# 9.7 --- Resume Control Commands (/continue, /new)

## /continue

-   Only works if active purchase exists
-   Returns to active purchase
-   Does not modify store_name
-   If none active → structured error

## /new

-   Only works if active purchase exists
-   Finishes current purchase
-   Triggers guided store name flow
-   If none active → structured error

------------------------------------------------------------------------

# 9.8 --- Guided Store Name Flow (Mandatory)

Triggered when:

-   No active purchase after /start
-   User selects /new

Prompt:

PT: Qual o nome do estabelecimento? EN: What is the store name?

Rules:

-   Required
-   Trim whitespace
-   Validated at domain level

------------------------------------------------------------------------

# 9.9 --- Comma-Based /add Format (Inline + Batch)

Accepted formats:

Inline: 
/add 19.90,feijao 
/add 19.90,3,feijao

Batch: 
/add 
19.90,feijao 
20.50,2,file de frango 
5.30,miojo

Parsing rules:

-   Separator: comma
-   Order: price, quantity(optional), name
-   Default quantity = 1
-   Quantity > 0 integer
-   Price > 0 decimal
-   Name non-empty
-   /add without body → structured error

------------------------------------------------------------------------

# 9.10 --- Add Handler Refactor (Dedicated Parser)

Create function:

parse_add_input(raw_text) -> List[ParsedItem]

Parser responsibilities:

-   Split multiline input
-   Validate each line
-   Apply default quantity
-   Convert price to decimal
-   Validate name
-   Raise structured errors

Handler responsibilities:

-   Call parser
-   Loop through parsed items
-   Call service
-   Return formatted response

------------------------------------------------------------------------

# 9.11 --- Physical Unit Counting Consistency

Example:

/add 5.90,3,feijao

System must:

-   Add 3 units
-   Respond: 3 items added
-   Increase total items by 3

Must reflect in:

-   /add
-   /total
-   /finish
-   Resume summary

------------------------------------------------------------------------

# 9.12 --- Post-Add Summary Redesign

EN:

X items added.

Total items: <physical_units_sum>
Total amount: <formatted_total>

PT:

X itens adicionados.

Total de itens: <physical_units_sum>
Valor total: <formatted_total>

Rules:

-   Items added = physical units
-   Total items = sum of quantities
-   Total amount = sum(quantity × price)
-   Locale formatting applied

------------------------------------------------------------------------

# 9.13 --- Unified Error Message Structure

EN:

❌ <Clear Title>

Short explanation.

Correct format: 
/command example_here

Type /help for more information.

PT:

❌ <Título claro>

Explicação curta.

Formato correto: 
/comando exemplo_aqui

Digite /help para mais informações.

Rules:

-   Always include command example
-   Always include help footer
-   Apply to all commands and invalid states

------------------------------------------------------------------------

# 9.14 --- /finish Summary Includes Store Name

PT:

Compra finalizada.

Estabelecimento: <store_name>
Total de itens: `<sum>
Valor final: <formatted_total>

EN equivalent required.

------------------------------------------------------------------------

# 9.15 --- Manual End-to-End Validation

Required scenarios:

1.  /start ptbr
2.  Active purchase → test /continue
3.  Active purchase → test /new
4.  Guided store flow
5.  Inline add
6.  Batch add
7.  Mixed quantities
8.  Error consistency (EN + PT)
9.  Full purchase cycle

Must confirm:

-   No legacy commands
-   No free-text interpretation
-   Store name always displayed
-   Batch predictable
-   Error structure identical everywhere
-   All tests passing

------------------------------------------------------------------------

END OF PHASE 9

---

## Progress Checklist

```
## Phase 1: Bootstrap
- [x] 1.1 — Project skeleton created
- [x] 1.2 — Config loader working
- [x] 1.3 — Logging initialized

## Phase 2: Infrastructure
- [x] 2.1 — SQLite database initialized
- [x] 2.2 — Base repository interface defined
- [x] 2.3 — SQLite repositories implemented

## Phase 3: Domain Layer
- [x] 3.1 — Purchase domain entity created
- [x] 3.2 — Custom exceptions defined

## Phase 4: Services Layer
- [x] 4.1 — PurchaseService implemented

## Phase 5: Telegram Adapter
- [x] 5.1 — Bot bootstrap complete
- [x] 5.2 — /start handler working

## Phase 6: Core Features (MVP)
- [x] 6.1 — /add_item handler
- [x] 6.2 — /view_total handler
- [x] 6.3 — /list_items handler
- [x] 6.4 — /edit_item handler
- [x] 6.5 — /delete_item handler
- [x] 6.6 — /finish handler

## Phase 7: Polish
- [x] 7.1 — Error handling complete
- [x] 7.2 — Logging improved
- [x] 7.3 — UX messages polished

## Phase 8: UX & Localization (V2)
- [x] 8.1 — Message formatting layer
- [x] 8.2 — Global help command
- [x] 8.3 — Resume / new purchase flow
- [x] 8.4 — Pipe-based item parsing
- [x] 8.5 — UX message standardization
- [x] 8.6 — Localization layer (EN + PT-BR)
- [x] 8.7 — Tests update for V2

## Phase 9: UX Optimization & Controlled Flow (V3)

- [ ] 9.1 — Domain update (store_name required)
- [ ] 9.2 — Database migration (store_name NOT NULL)
- [ ] 9.3 — Repository update (persist & load store_name)
- [ ] 9.4 — Service layer update (create_purchase with store_name)

- [ ] 9.5 — Command simplification (single-word commands)
- [ ] 9.6 — /start localization parameter support
- [ ] 9.7 — Resume control commands (/continue, /new)
- [ ] 9.8 — Guided store name flow (mandatory)

- [ ] 9.9 — Comma-based /add format (inline + batch)
- [ ] 9.10 — Add handler refactor (dedicated parser)

- [ ] 9.11 — Physical unit counting consistency
- [ ] 9.12 — Post-add summary redesign (units + total clarity)

- [ ] 9.13 — Unified error message structure
- [ ] 9.14 — /finish summary includes store name

- [ ] 9.15 — Manual end-to-end validation
```

---

## Safe Extensions After MVP

Once the MVP is complete and working, these extensions are safe and maintain the architecture:

### 1. **Multi-User Support**
- Add `user_id` to Purchase table
- Store in Telegram `update.effective_user.id`
- Filter purchases by user in service
- No layer changes needed

### 2. **Persistence Across Conversations**
- Load previous purchase from DB if user has unfinished one
- Check on /start command
- Use same service method

### 3. **REST API Layer**
- Create `app/api/` folder (parallel to handlers)
- Create API handlers that call same services
- No service changes needed

### 4. **Reports / Summaries**
- Add reporting service (call existing service, aggregate)
- No handler changes needed

### 5. **Categories or Tags**
- Add `category` field to Purchase
- Update domain model and repository schema
- Update handlers to accept category parameter
- Incremental and contained

### 6. **Recurring Purchases**
- Add template concept (service method: `create_from_template`)
- No layer changes

### 7. **Cloud Sync** (Supabase / Firebase)
- Replace SQLitePurchaseRepository with CloudRepository
- Implement same interface
- Services unchanged

### 8. **Web UI**
- Create `app/web/` folder with FastAPI or Flask
- Reuse services and domain
- No backend changes

### 9. **Database Migration (SQLite → Postgres)**
- Create PostgresRepository implementing BaseRepository
- Inject different repository at startup
- Zero handler/service changes

---

## Final Notes

- **Keep it simple:** Only implement what's in this plan until MVP is complete.
- **Respect the architecture:** Dependency direction is enforced by folder structure.
- **Test as you go:** Validate after each step before continuing.
- **Use the guardrails:** "Common mistakes" sections are AI hallucination guardrails—check them before moving forward.
- **Leverage AI:** Let Copilot write boilerplate and repetitive code, but guide it with the architecture and naming conventions.
- **Document decisions:** If you deviate from the plan, update `docs/` with why.
- **Currence Rules:** All monetary values must: Use BRL formatting (R$), Always display 2 decimal places, Never localize currency symbol (even in EN mode).

---

**This plan is ready for execution. Proceed step-by-step in sequence, validate after each step, and refer to the "Common mistakes to avoid" sections to stay on track.**
