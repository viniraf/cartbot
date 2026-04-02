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
| `/start [ptbr\|enus]` | Inicie uma nova compra (escolha o idioma) |
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

ou

```
/start enus
```

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
/add 19.90,2,arroz
```

Bot: `✅ Item adicionado: 2x arroz | R$ 39,80`

```
/add
5.00,feijao
3.00,2,miojo
```

Bot: `✅ 2 itens adicionados`

### Ver Lista

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

Erro: `❌ Formato inválido.\n\nUse: /add preco,item ou /add preco,quantidade,item\n\nExemplos:\n/add 19.90,arroz\n/add 5.30,2,miojo`

**Comando desconhecido:**
```
/checkout
```

Resposta: `❌ Comando desconhecido.\n\nUse /help para ver os comandos disponíveis.`

**Dicas:**
- Sempre comece com um comando (/)
- Use separadores de vírgula (sem espaços)
- Se não tiver certeza, digite `/help`

---

## 🌍 Suporte a Idiomas

CartBot suporta dois idiomas:

- **PT-BR** (Português Brasileiro) — `/start ptbr`
- **EN-US** (Inglês) — `/start enus`

Todas as mensagens estarão no idioma escolhido.

**Mudar idioma:** Chame `/start` novamente e selecione um idioma diferente.

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
