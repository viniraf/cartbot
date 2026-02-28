# 🛒 CartBot

Bot pessoal de Telegram para registrar compras em tempo real e acompanhar o valor total durante o mercado — simples, rápido e focado em uso real.

---

## ✨ Visão Geral

O CartBot nasceu de uma necessidade simples: parar de usar calculadora no mercado e ainda lembrar quanto cada item custou.

Com ele, você registra os produtos enquanto compra e acompanha o total em tempo real direto no Telegram.

Sem planilhas.  
Sem apps complexos.  
Sem fricção.

---

## 🎯 Objetivo

Ajudar durante compras do dia a dia permitindo:

- Registrar itens rapidamente
- Acompanhar o total acumulado
- Ver detalhes da compra a qualquer momento
- Corrigir erros facilmente
- Manter histórico simples

Tudo via chat.

---

## 🚀 Funcionalidades (MVP)

### 🟢 Compra

- Iniciar uma compra com:
  - Nome do mercado
  - Data automática
- Adicionar itens com:
  - Nome livre
  - Quantidade
  - Preço unitário
- Ver total atualizado a cada item

---

### 📊 Visualização

- Resumo rápido com total atual
- Detalhamento completo com:
  - Nome do item
  - Quantidade
  - Valor unitário
  - Subtotal
  - Total geral

---

### ✏️ Edição

- Editar qualquer item
- Remover itens
- Navegar entre menus sem perder estado

---

### 🗂 Histórico

- Salvar compras localmente
- Permitir futuras análises simples

---

## 🧠 Casos de Uso

- Acompanhar gasto no mercado em tempo real
- Evitar surpresas no caixa
- Conferir itens antes de pagar
- Ter histórico básico de compras

---

## 🏗 Arquitetura (Visão Geral)

O projeto segue uma arquitetura simples e evolutiva:

- Fácil de entender
- Baixa carga cognitiva
- Preparado para crescer

### Princípios

- Domínio isolado da interface Telegram
- Código legível e testável
- Estrutura modular sem overengineering
- Preparado para relatórios futuros

Detalhes completos de arquitetura serão documentados posteriormente.

---

## 🧩 Estrutura Inicial

A definir.

---

## 🛠 Stack

- Python 3.11+
- python-telegram-bot
- SQLite

---

## ▶️ Como Rodar Localmente

### Criar ambiente virtual

python -m venv .venv  
source .venv/bin/activate  (Linux/Mac)  
.venv\Scripts\activate     (Windows)

### Instalar dependências

pip install -r requirements.txt

### Configurar variáveis

Crie um arquivo .env com:

TELEGRAM_TOKEN=seu_token_aqui

### Rodar o bot

python app/main.py

---

## 🚀 Deploy

O projeto foi pensado para rodar gratuitamente em plataformas como:

- Railway
- Render
- Fly.io

Com deploy simples via Docker ou Python puro.

Guia de deploy detalhado será adicionado na documentação.

---

## 🧪 Testes

Foco em:

- Regras de negócio isoladas
- Serviços testáveis
- Lógica desacoplada do Telegram

Execução:

pytest

---

## 🔮 Roadmap Futuro

Possíveis evoluções:

- Relatórios de preço por item
- Histórico e gráficos
- Lista de compras integrada
- Busca por compras antigas
- Backup em nuvem
- Multiusuário (família)
- Versão web

---

## 🤖 Filosofia do Projeto

O CartBot segue três pilares:

Simplicidade  
Resolver um problema real sem complexidade desnecessária.

Clareza  
Código legível acima de abstrações excessivas.

Evolução  
Começar pequeno, crescer com propósito.


## 📌 Status

Em desenvolvimento inicial (MVP)
