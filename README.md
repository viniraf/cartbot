# 🛒 CartBot

Telegram bot to record purchases in real time — track items, quantities, and amounts while shopping.

---

## 📌 Overview

CartBot simplifies everyday shopping. Record items while you shop at the market, see the total in real time, and have a history of all your purchases.

**No calculator. No spreadsheets. No friction.**

---

## 🤖 Create Your Telegram Bot (BotFather)

Before running CartBot, create a Telegram bot and copy its token:

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the naming steps
3. Copy the generated token and use it as `TELEGRAM_TOKEN`

For the official and complete guide, see:
[Creating a new bot (Telegram Docs)](https://core.telegram.org/bots/features#creating-a-new-bot)

---

## 💬 Commands

| Command | Description |
|---------|-------------|
| `/start` | Begin a new purchase (English) |
| `/start en` | Begin a new purchase (English) |
| `/start ptbr` | Begin a new purchase (Portuguese) |
| `/continue` | Resume an active purchase |
| `/new` | Start a new purchase (if one is active) |
| `/add` | Add items to your purchase |
| `/list` | View all items in current purchase |
| `/total` | See total amount and item count |
| `/edit` | Modify or remove items |
| `/delete` | Remove a specific item |
| `/finish` | Complete the purchase and save |
| `/help` | Show all available commands |

---

## 🚀 Getting Started

### Step 1 — Start a Purchase

```
/start
```

The bot will ask for the store name. (English by default, or use `/start ptbr` for Portuguese)

### Step 2 — Store Name

Type the store name (e.g., `Whole Foods`, `Trader Joe's`, `Local Market`)

### Step 3 — If You Already Have an Active Purchase

You'll see two options:

- `/continue` — Resume the current purchase
- `/new` — Start a fresh purchase

---

## ➕ Adding Items

### Inline Format (Quick)

Add one or more items without leaving the conversation:

```
/add 5.99,bread
/add 5.99,3,bread
/add 3.50,2,milk 1L
```

Format: `/add price,item` or `/add price,quantity,item`

**Rules:**
- Comma-separated (no spaces)
- Price first, then item name
- Quantity is optional (default = 1)
- Item names can include units (e.g., "rice 1kg", "chicken 500g")

### Batch Format (Multiple Items)

Add multiple items at once:

```
/add
5.99,bread
3.50,2,milk
2.99,3,eggs dozen
```

Just send `/add` and then list items on separate lines. Same format as inline.

---

## 📊 What the Bot Tracks

For each purchase:

- **Store name** — where you're shopping
- **Total items** — count of physical units (e.g., 3 boxes, 2 kg)
- **Total amount** — sum of all items
- **Item details** — name, quantity, unit price, subtotal
- **Active purchase** — your current shopping session

---

## 📋 Example Session

### Start

```
/start
```

Bot: `What's the store name?`

You: `Whole Foods`

Bot: `✅ Purchase started at Whole Foods`

### Add Items

```
/add 5.99,bread
```

Bot:
```
✅ Added 1 item

Total items: 1
Total amount: $5.99

--
Type /help for more information.
```

```
/add
3.50,milk
2.99,2,eggs
```

Bot:
```
✅ Added 3 items

Total items: 4
Total amount: $15.47

--
Type /help for more information.
```

### View List

```
/list
```

Bot:
```
Items

1. bread × 1 @ $5.99 = $5.99
2. milk × 1 @ $3.50 = $3.50
3. eggs × 2 @ $2.99 = $5.98

Total: $15.47

Actions:
/delete N — remove item
/edit N qty price — modify item

--
Type /help for more information.
```

### Finish

```
/finish
```

Bot: `✅ Purchase completed! Total: $15.47`

---

## ⚠️ Error Handling

**Invalid format:**
```
/add bread 5.99
```

Error:
```
❌ Invalid /add Format

Items must include price and name.

Correct format:
/add 5.99,bread
or
/add 5.99,2,bread
```

**Unknown command:**
```
/checkout
```

Response:
```
❌ Unknown command.

Use /help to see available commands.
```

**Tips:**
- Always start with a command (/)
- Use comma separators (no spaces)
- If unsure, type `/help`

---

## 🌍 Language Support

CartBot supports two languages:

- **EN-US** (English) — `/start` or `/start en`
- **PT-BR** (Brazilian Portuguese) — `/start ptbr`

All messages will be in your chosen language.

---

## 🛠 Developer Information

### Stack

- Python 3.13+
- python-telegram-bot
- SQLite

### Running Locally

1. Create virtual environment:
   ```
   python -m venv .venv
   venv\Scripts\activate.bat     # Windows
   source venv/bin/activate  # Linux/Mac
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```
   TELEGRAM_TOKEN=your_token_here
   ```

4. Run the bot:
   ```
   python -m app.main
   ```

### Testing

```
pytest
```

All tests are located in the `tests/` directory.