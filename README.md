# 🛒 CartBot

Bot de Telegram para registrar compras em tempo real — rastreie itens, quantidades e valores enquanto compra.

---

## 📌 Overview

CartBot simplifica as compras do dia a dia. Registre itens enquanto você compra no mercado, veja o total em tempo real e tenha um histórico de todas as suas compras.

**Sem calculadora. Sem planilhas. Sem fricção.**

---

## 💬 Commands

| Command | Description |
|---------|-------------|
| `/start [ptbr\|enus]` | Begin a new purchase (set language) |
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
/start ptbr
```

or

```
/start enus
```

The bot will ask for the store name.

### Step 2 — Store Name

Type the store name (e.g., `Assaí`, `Carrefour`, `Mercado Local`)

### Step 3 — If You Already Have an Active Purchase

You'll see two options:

- `/continue` — Resume the current purchase
- `/new` — Start a fresh purchase

---

## ➕ Adding Items

### Inline Format (Quick)

Add one or more items without leaving the conversation:

```
/add 19.90,feijao
/add 19.90,3,feijao
/add 5.30,2,miojo 500g
```

Format: `/add price,item` or `/add price,quantity,item`

**Rules:**
- Comma-separated (no spaces)
- Price first, then item name
- Quantity is optional (default = 1)
- Item names can include units (e.g., "arroz 1kg", "frango 500g")

### Batch Format (Multiple Items)

Add multiple items at once:

```
/add
19.90,feijao
5.30,2,miojo
10.00,3,arroz
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
/start ptbr
```

Bot: `Qual o nome do mercado?`

You: `Assaí`

Bot: `✅ Compra iniciada em Assaí`

### Add Items

```
/add 19.90,2,arroz
```

Bot: `✅ Item adicionado: 2x arroz | R$ 39,80`

```
/add
5.00,feijao
3.00,2,miojo
```

Bot: `✅ 2 itens adicionados`

### View List

```
/list
```

Bot:
```
📦 Compra - Assaí

Arroz (2) ................ R$ 39,80
Feijão (1) ............... R$ 5,00
Miojo (2) ................ R$ 6,00

Total: 5 itens | R$ 50,80
```

### Finish

```
/finish
```

Bot: `✅ Compra finalizada! Total: R$ 50,80`

---

## ⚠️ Error Handling

**Invalid format:**
```
/add feijao 19.90
```

Error: `❌ Invalid format.\n\nUse: /add price,item or /add price,quantity,item\n\nExamples:\n/add 19.90,arroz\n/add 5.30,2,miojo`

**Unknown command:**
```
/checkout
```

Response: `❌ Unknown command.\n\nUse /help to see available commands.`

**Tips:**
- Always start with a command (/)
- Use comma separators (no spaces)
- If unsure, type `/help`

---

## 🌍 Language Support

CartBot supports two languages:

- **PT-BR** (Brazilian Portuguese) — `/start ptbr`
- **EN-US** (English) — `/start enus`

All messages will be in your chosen language.

**Change language:** Call `/start` again and select a different language.

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
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
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
   python app/main.py
   ```

### Testing

```
pytest
```

All tests are located in the `tests/` directory.

---

## 📌 Status

**Current Version:** V3  
**Status:** Active Development  
**Last Updated:** 2026-04  

For issues, feature requests, or contributions, please refer to the documentation in the `docs/` folder.
