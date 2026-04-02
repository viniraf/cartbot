# 🛒 CartBot

Bot de Telegram para registrar compras em tempo real — rastreie itens, quantidades e valores enquanto compra.

---

## 📌 Visão Geral

CartBot simplifica as compras do dia a dia. Registre itens enquanto você compra no mercado, veja o total em tempo real e tenha um histórico de todas as suas compras.

**Sem calculadora. Sem planilhas. Sem fricção.**

---

## 💬 Comandos

| Comando | Descrição |
|---------|-----------|
| `/start` | Inicie uma nova compra (Português) |
| `/start en` | Inicie uma nova compra (Inglês) |
| `/start ptbr` | Inicie uma nova compra (Português) |
| `/continue` | Retome uma compra ativa |
| `/new` | Inicie uma nova compra (se houver uma ativa) |
| `/add` | Adicione itens à sua compra |
| `/list` | Veja todos os itens da compra atual |
| `/total` | Veja o total e a quantidade de itens |
| `/edit` | Modifique ou remova itens |
| `/delete` | Remova um item específico |
| `/finish` | Conclua a compra e salve |
| `/help` | Mostre todos os comandos disponíveis |

---

## 🚀 Comece Agora

### Passo 1 — Inicie uma Compra

```
/start ptbr
```

Ou `/start` para usar Inglês.

O bot pedirá o nome do mercado.

### Passo 2 — Nome do Mercado

Digite o nome do mercado (ex: `Assaí`, `Carrefour`, `Mercado Local`)

### Passo 3 — Se Você Já Tem uma Compra Ativa

Você verá duas opções:

- `/continue` — Retomar a compra atual
- `/new` — Iniciar uma nova compra

---

## ➕ Adicionando Itens

### Formato Inline (Rápido)

Adicione um ou mais itens sem sair da conversa:

```
/add 19.90,feijao
/add 19.90,3,feijao
/add 5.30,2,miojo 500g
```

Formato: `/add preco,item` ou `/add preco,quantidade,item`

**Regras:**
- Separado por vírgula (sem espaços)
- Preço primeiro, depois o nome do item
- Quantidade é opcional (padrão = 1)
- Nomes de itens podem incluir unidades (ex: "arroz 1kg", "frango 500g")

### Formato em Lote (Múltiplos Itens)

Adicione vários itens de uma vez:

```
/add
19.90,feijao
5.30,2,miojo
10.00,3,arroz
```

Apenas envie `/add` e liste os itens em linhas separadas. Usa o mesmo formato que inline.

---

## 📊 O Que o Bot Rastreia

Para cada compra:

- **Nome do mercado** — onde você está comprando
- **Total de itens** — contagem de unidades físicas (ex: 3 caixas, 2 kg)
- **Valor total** — soma de todos os itens
- **Detalhes dos itens** — nome, quantidade, preço unitário, subtotal
- **Compra ativa** — sua sessão de compras atual

---

## 📋 Exemplo de Sessão

### Iniciar

```
/start ptbr
```

Bot: `Qual o nome do mercado?`

Você: `Assaí`

Bot: `✅ Compra iniciada em Assaí`

### Adicionar Itens

```
/add 5.00,feijao
```

Bot:
```
✅ 1 item adicionado

Total de itens: 1
Valor total: R$ 5,00

--
Digite /help para mais informações.
```

```
/add
3.00,miojo
2.50,2,arroz
```

Bot:
```
✅ 3 itens adicionados

Total de itens: 4
Valor total: R$ 13,00

--
Digite /help para mais informações.
```

### Ver Lista

```
/list
```

Bot:
```
Items

1. feijão × 1 @ R$ 5,00 = R$ 5,00
2. miojo × 1 @ R$ 3,00 = R$ 3,00
3. arroz × 2 @ R$ 2,50 = R$ 5,00

Total: R$ 13,00

Actions:
/delete N — remove item
/edit N qty price — modify item

--
Digite /help para mais informações.
```

### Finalizar

```
/finish
```

Bot: `✅ Compra finalizada! Total: R$ 50,80`

---

## ⚠️ Tratamento de Erros

**Formato inválido:**
```
/add feijao 19.90
```

Erro:
```
❌ Formato inválido

Os itens devem incluir preço e nome.

Formato correto:
/add 19.90,feijao
ou
/add 19.90,2,feijao
```

**Comando desconhecido:**
```
/checkout
```

Resposta:
```
❌ Comando desconhecido.

Use /help para ver os comandos disponíveis.
```

**Dicas:**
- Sempre comece com um comando (/)
- Use separadores de vírgula (sem espaços)
- Se não tiver certeza, digite `/help`

---

## 🌍 Suporte a Idiomas

CartBot suporta dois idiomas:

- **PT-BR** (Português Brasileiro) — `/start` ou `/start ptbr`
- **EN-US** (Inglês) — `/start en`

Todas as mensagens estarão no idioma escolhido.

**Mudar idioma:** Chame `/start en` ou `/start ptbr` para mudar de idioma.

---

## 🛠 Informações para Desenvolvedores

### Stack

- Python 3.13+
- python-telegram-bot
- SQLite

### Rodando Localmente

1. Crie um ambiente virtual:
   ```
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente:
   ```
   TELEGRAM_TOKEN=seu_token_aqui
   ```

4. Execute o bot:
   ```
   python app/main.py
   ```

### Testes

```
pytest
```

Todos os testes estão localizados no diretório `tests/`.

---

## 📌 Status

**Versão Atual:** V3  
**Status:** Em Desenvolvimento Ativo  
**Última Atualização:** 2026-04  

Para reportar problemas, sugestões de funcionalidades ou contribuições, consulte a documentação na pasta `docs/`.
