"""Portuguese (Brazil) message strings for CartBot.

All user-facing messages are centralized here for:
1. Consistency across the bot
2. Easy translation to other languages
3. Easier maintenance and updates

Currency (R$) is NOT translated - always displayed as R$ in all languages.
Command names (/start, /add_item, etc.) are also NOT translated.
"""

MESSAGES = {
    # /start command
    "START_NEW": "Lista de compras iniciada.",
    "START_NEW_HELP": "Use /add_item para adicionar itens | Use /list_items para ver todos os itens",
    "START_ACTIVE": "Voc├¬ tem uma compra ativa.",
    "START_ACTIVE_CREATED": "Criada em: {created_at}",
    "START_ACTIVE_ITEMS": "Itens: {item_count}",
    "START_ACTIVE_TOTAL": "Total: {total}",
    "START_ACTIVE_OPTIONS": "Opções:",
    "START_ACTIVE_RESUME": "/resume - continuar esta compra",
    "START_ACTIVE_NEW": "/new - finalizar e começar uma nova",

    # /resume command
    "RESUME_TITLE": "Compra retomada.",
    "RESUME_CREATED": "Criada em: {created_at}",
    "RESUME_ITEMS": "Itens: {item_count}",
    "RESUME_TOTAL": "Total: {total}",
    "RESUME_ACTIONS": "Ações:",
    "RESUME_ADD_ITEM": "/add_item - adicionar item",
    "RESUME_LIST_ITEMS": "/list_items - mostrar todos os itens",
    "RESUME_FINISH": "/finish - finalizar compra",
    "RESUME_NO_PURCHASE": "Nenhuma compra ativa. Use /start para começar.",
    "RESUME_NOT_FOUND": "Compra não encontrada.",
    "RESUME_FINISHED": "Esta compra foi finalizada. Use /start para começar uma nova compra.",

    # /new command
    "NEW_PREVIOUS_FINISHED": "Compra anterior finalizada.",
    "NEW_TOTAL": "Total: {total}",
    "NEW_ITEMS": "Itens: {item_count}",
    "NEW_STARTED": "Lista de compras iniciada.",
    "NEW_HELP": "Use /add_item para adicionar itens | Use /list_items para ver todos os itens",
    "NEW_ERROR": "Ocorreu um erro. Tente novamente mais tarde.",
    "NEW_NO_PURCHASE": "Nenhuma compra ativa. Use /start para começar.",

    # /add_item command
    "ADD_ITEM_SUCCESS": "Item adicionado.",
    "ADD_ITEM_TOTAL": "Total: {total}",
    "ADD_ITEM_USAGE": "Use:\n/add_item Nome | qty | preço\n\nExemplo:\n/add_item Leite | 2 | 5.50",
    "ADD_ITEM_NO_PURCHASE": "Nenhuma compra ativa. Use /start para começar.",
    "ADD_ITEM_INVALID_FORMAT": "Formato inválido.",
    "ADD_ITEM_INVALID_FORMAT_HELP": "Use:\n/add_item Nome | qty | preço\n\nExemplo:\n/add_item Leite | 2 | 5.50",

    # /add command (Phase 9.12)
    "ADD_ITEMS_COUNT": "{count} itens adicionados.",
    "ADD_TOTAL_ITEMS": "Total de itens: {item_count}",
    "ADD_TOTAL_AMOUNT": "Valor total: {total}",

    # /list_items command
    "LIST_ITEMS_TITLE": "Itens",
    "LIST_ITEMS_EMPTY": "Nenhum item ainda.",
    "LIST_ITEMS_EMPTY_HELP": "Use /add_item para adicionar seu primeiro item.",
    "LIST_ITEMS_NO_PURCHASE": "Nenhuma compra ativa. Use /start para começar.",
    "LIST_ITEMS_TOTAL": "Total: {total}",
    "LIST_ITEMS_ACTIONS": "Ações:",
    "LIST_ITEMS_DELETE_ITEM": "/delete_item N - remover item",
    "LIST_ITEMS_EDIT_ITEM": "/edit_item N qty preço - modificar item",

    # /view_total command
    "VIEW_TOTAL_PREFIX": "Total: {total}",
    "VIEW_TOTAL_ITEMS": "Itens: {item_count}",
    "VIEW_TOTAL_NO_PURCHASE": "Nenhuma compra ativa. Use /start para começar.",

    # /delete_item command
    "DELETE_ITEM_SUCCESS": "Item removido.",
    "DELETE_ITEM_NEW_TOTAL": "Novo total: {total}",
    "DELETE_ITEM_USAGE": "Uso: /delete_item índice]\nExemplo: /delete_item 1",
    "DELETE_ITEM_INVALID_INDEX": "Índice inválido. Use um número.",
    "DELETE_ITEM_INVALID_INDEX_HELP": "O índice deve ser 1 ou maior.",
    "DELETE_ITEM_NO_PURCHASE": "Nenhuma compra ativa. Use /start para começar.",
    "DELETE_ITEM_NOT_FOUND": "Erro: {error}",

    # /edit_item command
    "EDIT_ITEM_SUCCESS": "Item atualizado.",
    "EDIT_ITEM_NEW_TOTAL": "Novo total: {total}",
    "EDIT_ITEM_USAGE": "Uso: /edit_item [├¡ndice] [nova_quantidade] [novo_preço]\nExemplo: /edit_item 1 3 2.00",
    "EDIT_ITEM_INVALID_INPUT": "Entrada inválida. Índice e quantidade devem ser números inteiros, preço um número.",
    "EDIT_ITEM_INVALID_INDEX": "O índice deve ser 1 ou maior.",
    "EDIT_ITEM_NO_PURCHASE": "Nenhuma compra ativa. Use /start para começar.",
    "EDIT_ITEM_NOT_FOUND": "Erro: {error}",

    # /finish command (Phase 9.14 - store name in summary)
    "FINISH_TITLE": "Compra finalizada.",
    "FINISH_STORE": "Estabelecimento: {store_name}",
    "FINISH_TOTAL_ITEMS": "Total de itens: {item_count}",
    "FINISH_TOTAL_AMOUNT": "Valor final: {total}",
    "FINISH_NEW_PURCHASE": "/start - começar uma nova compra",
    "FINISH_NO_PURCHASE": "Nenhuma compra ativa. Use /start para começar.",

    # /help command
    "HELP_TITLE": "Comandos Disponíveis",
    "HELP_SESSION_TITLE": "Sessão",
    "HELP_START": "/start - iniciar ou retomar uma compra",
    "HELP_RESUME": "/continue - continuar compra ativa",
    "HELP_NEW": "/new - finalizar e começar uma nova compra",
    "HELP_FINISH": "/finish - finalizar compra atual",
    "HELP_LANG": "/lang [en|ptbr] - mudar idioma",
    "HELP_ITEMS_TITLE": "Itens",
    "HELP_ADD_ITEM": "/add preço,item ou /add preço,qtd,item",
    "HELP_EDIT_ITEM": "/edit índice qty preço",
    "HELP_DELETE_ITEM": "/delete índice",
    "HELP_OVERVIEW_TITLE": "Visão Geral",
    "HELP_VIEW_TOTAL": "/total - mostrar total",
    "HELP_LIST_ITEMS": "/list - mostrar todos os itens",

    # /lang command
    "LANG_SET_EN": "Language set to English.",
    "LANG_SET_PTBR": "Idioma alterado para Português.",
    "LANG_INVALID": "Idioma inválido. Use: /lang en ou /lang ptbr",
    "LANG_USAGE": "Uso: /lang [en|ptbr]\n\nExemplo:\n/lang ptbr - mudar para Português\n/lang en - mudar para Inglês",

    # Store name input
    "STORE_PROMPT": "Qual o nome do estabelecimento?",
    "STORE_INVALID": "O nome do estabelecimento não pode estar vazio. Tente novamente.",
    "STORE_CREATED": "Estabelecimento: {store_name}",
    "STORE_NEXT_STEPS_TITLE": "Próximos passos:",
    "STORE_ADD_GUIDE": "/add preço,item — adicionar itens",
    "STORE_LIST_GUIDE": "/list — ver itens",
    "STORE_FINISH_GUIDE": "/finish — finalizar compra",

    # Phase 9.13 - Unified error message structure
    # All errors follow format: TITLE, EXPLANATION, EXAMPLE, FOOTER

    # No active purchase
    "ERROR_NO_ACTIVE_PURCHASE_TITLE": "❌ Nenhuma Compra Ativa",
    "ERROR_NO_ACTIVE_PURCHASE_EXPLANATION": "Você precisa iniciar uma compra primeiro.",
    "ERROR_NO_ACTIVE_PURCHASE_EXAMPLE": "Uso correto: /start",

    # Invalid /add format
    "ERROR_INVALID_ADD_FORMAT_TITLE": "❌ Formato /add Inválido",
    "ERROR_INVALID_ADD_FORMAT_EXPLANATION": "Os itens devem incluir preço e nome.",
    "ERROR_INVALID_ADD_FORMAT_EXAMPLE": "Formato correto:\n/add 19.90,item\nou\n/add 19.90,2,item",

    # Invalid delete index
    "ERROR_INVALID_DELETE_INDEX_TITLE": "❌ Índice de Item Inválido",
    "ERROR_INVALID_DELETE_INDEX_EXPLANATION": "O índice deve ser um número maior que 0.",
    "ERROR_INVALID_DELETE_INDEX_EXAMPLE": "Formato correto: /delete 1",

    # Invalid edit input
    "ERROR_INVALID_EDIT_INPUT_TITLE": "❌ Formato /edit Inválido",
    "ERROR_INVALID_EDIT_INPUT_EXPLANATION": "Índice e quantidade devem ser números inteiros, preço deve ser um decimal.",
    "ERROR_INVALID_EDIT_INPUT_EXAMPLE": "Formato correto: /edit 1 2 3,50",

    # Invalid language
    "ERROR_INVALID_LANG_TITLE": "❌ Idioma Inválido",
    "ERROR_INVALID_LANG_EXPLANATION": "Os idiomas suportados são Inglês (en) e Português (ptbr).",
    "ERROR_INVALID_LANG_EXAMPLE": "Formato correto: /lang en ou /lang ptbr",

    # Invalid locale at /start
    "ERROR_INVALID_LOCALE_TITLE": "❌ Localidade Inválida",
    "ERROR_INVALID_LOCALE_EXPLANATION": "As localidades suportadas são Inglês (en) e Português (ptbr).",
    "ERROR_INVALID_LOCALE_EXAMPLE": "Formato correto: /start en ou /start ptbr",

    # Empty store name
    "ERROR_STORE_EMPTY_TITLE": "❌ Nome do Estabelecimento Vazio",
    "ERROR_STORE_EMPTY_EXPLANATION": "O nome do estabelecimento não pode estar vazio.",
    "ERROR_STORE_EMPTY_EXAMPLE": "Por favor, forneça um nome de estabelecimento.",

    # Generic error
    "ERROR_GENERIC_TITLE": "❌ Ocorreu um Erro",
    "ERROR_GENERIC_EXPLANATION": "Algo inesperado aconteceu.",
    "ERROR_GENERIC_EXAMPLE": "Por favor, tente novamente mais tarde.",

    # Error help footer
    "ERROR_HELP_FOOTER": "Digite /help para mais informações.",

    # Unknown command
    "UNKNOWN_COMMAND_TITLE": "❌ Comando desconhecido.",
    "UNKNOWN_COMMAND_MESSAGE": "Use /help para ver os comandos disponíveis.",

    # General/errors (kept for backward compatibility)
    "ERROR_GENERIC": "Ocorreu um erro. Tente novamente mais tarde.",
    "HELP_HINT": "Precisa de ajuda? Use /help",
}
