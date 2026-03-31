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
    "START_ACTIVE_OPTIONS": "Op├º├Áes:",
    "START_ACTIVE_RESUME": "/resume ÔÇö continuar esta compra",
    "START_ACTIVE_NEW": "/new ÔÇö finalizar e come├ºar uma nova",

    # /resume command
    "RESUME_TITLE": "Compra retomada.",
    "RESUME_CREATED": "Criada em: {created_at}",
    "RESUME_ITEMS": "Itens: {item_count}",
    "RESUME_TOTAL": "Total: {total}",
    "RESUME_ACTIONS": "A├º├Áes:",
    "RESUME_ADD_ITEM": "/add_item ÔÇö adicionar item",
    "RESUME_LIST_ITEMS": "/list_items ÔÇö mostrar todos os itens",
    "RESUME_FINISH": "/finish ÔÇö finalizar compra",
    "RESUME_NO_PURCHASE": "Nenhuma compra ativa. Use /start para come├ºar.",
    "RESUME_NOT_FOUND": "Compra n├úo encontrada.",
    "RESUME_FINISHED": "Esta compra foi finalizada. Use /start para come├ºar uma nova compra.",

    # /new command
    "NEW_PREVIOUS_FINISHED": "Compra anterior finalizada.",
    "NEW_TOTAL": "Total: {total}",
    "NEW_ITEMS": "Itens: {item_count}",
    "NEW_STARTED": "Lista de compras iniciada.",
    "NEW_HELP": "Use /add_item para adicionar itens | Use /list_items para ver todos os itens",
    "NEW_ERROR": "Ocorreu um erro. Tente novamente mais tarde.",
    "NEW_NO_PURCHASE": "Nenhuma compra ativa. Use /start para come├ºar.",

    # /add_item command
    "ADD_ITEM_SUCCESS": "Item adicionado.",
    "ADD_ITEM_TOTAL": "Total: {total}",
    "ADD_ITEM_USAGE": "Use:\n/add_item Nome | qty | pre├ºo\n\nExemplo:\n/add_item Leite | 2 | 5.50",
    "ADD_ITEM_NO_PURCHASE": "Nenhuma compra ativa. Use /start para come├ºar.",
    "ADD_ITEM_INVALID_FORMAT": "Formato inv├ílido.",
    "ADD_ITEM_INVALID_FORMAT_HELP": "Use:\n/add_item Nome | qty | pre├ºo\n\nExemplo:\n/add_item Leite | 2 | 5.50",

    # /list_items command
    "LIST_ITEMS_TITLE": "Itens",
    "LIST_ITEMS_EMPTY": "Nenhum item ainda.",
    "LIST_ITEMS_EMPTY_HELP": "Use /add_item para adicionar seu primeiro item.",
    "LIST_ITEMS_NO_PURCHASE": "Nenhuma compra ativa. Use /start para come├ºar.",
    "LIST_ITEMS_TOTAL": "Total: {total}",
    "LIST_ITEMS_ACTIONS": "A├º├Áes:",
    "LIST_ITEMS_DELETE_ITEM": "/delete_item N ÔÇö remover item",
    "LIST_ITEMS_EDIT_ITEM": "/edit_item N qty pre├ºo ÔÇö modificar item",

    # /view_total command
    "VIEW_TOTAL_PREFIX": "Total: {total}",
    "VIEW_TOTAL_ITEMS": "Itens: {item_count}",
    "VIEW_TOTAL_NO_PURCHASE": "Nenhuma compra ativa. Use /start para come├ºar.",

    # /delete_item command
    "DELETE_ITEM_SUCCESS": "Item removido.",
    "DELETE_ITEM_NEW_TOTAL": "Novo total: {total}",
    "DELETE_ITEM_USAGE": "Uso: /delete_item [├¡ndice]\nExemplo: /delete_item 1",
    "DELETE_ITEM_INVALID_INDEX": "├ìndice inv├ílido. Use um n├║mero.",
    "DELETE_ITEM_INVALID_INDEX_HELP": "O ├¡ndice deve ser 1 ou maior.",
    "DELETE_ITEM_NO_PURCHASE": "Nenhuma compra ativa. Use /start para come├ºar.",
    "DELETE_ITEM_NOT_FOUND": "Erro: {error}",

    # /edit_item command
    "EDIT_ITEM_SUCCESS": "Item atualizado.",
    "EDIT_ITEM_NEW_TOTAL": "Novo total: {total}",
    "EDIT_ITEM_USAGE": "Uso: /edit_item [├¡ndice] [nova_quantidade] [novo_pre├ºo]\nExemplo: /edit_item 1 3 2.00",
    "EDIT_ITEM_INVALID_INPUT": "Entrada inv├ílida. ├ìndice e quantidade devem ser n├║meros inteiros, pre├ºo um n├║mero.",
    "EDIT_ITEM_INVALID_INDEX": "O ├¡ndice deve ser 1 ou maior.",
    "EDIT_ITEM_NO_PURCHASE": "Nenhuma compra ativa. Use /start para come├ºar.",
    "EDIT_ITEM_NOT_FOUND": "Erro: {error}",

    # /finish command
    "FINISH_TITLE": "Compra finalizada.",
    "FINISH_TOTAL": "Total: {total}",
    "FINISH_ITEMS": "Itens: {item_count}",
    "FINISH_NEW_PURCHASE": "/start ÔÇö come├ºar uma nova compra",
    "FINISH_NO_PURCHASE": "Nenhuma compra ativa. Use /start para come├ºar.",

    # /help command
    "HELP_TITLE": "Comandos Dispon├¡veis",
    "HELP_SESSION_TITLE": "Sess├úo",
    "HELP_START": "/start ÔÇö iniciar ou retomar uma compra",
    "HELP_RESUME": "/continue ÔÇö continuar compra ativa",
    "HELP_NEW": "/new ÔÇö finalizar e come├ºar uma nova compra",
    "HELP_FINISH": "/finish ÔÇö finalizar compra atual",
    "HELP_LANG": "/lang [en|ptbr] ÔÇö mudar idioma",
    "HELP_ITEMS_TITLE": "Itens",
    "HELP_ADD_ITEM": "/add Nome | qty | pre├ºo",
    "HELP_EDIT_ITEM": "/edit ├¡ndice qty pre├ºo",
    "HELP_DELETE_ITEM": "/delete ├¡ndice",
    "HELP_OVERVIEW_TITLE": "Vis├úo Geral",
    "HELP_VIEW_TOTAL": "/total ÔÇö mostrar total",
    "HELP_LIST_ITEMS": "/list ÔÇö mostrar todos os itens",

    # /lang command
    "LANG_SET_EN": "Language set to English.",
    "LANG_SET_PTBR": "Idioma alterado para Portugu├¬s.",
    "LANG_INVALID": "Idioma inv├ílido. Use: /lang en ou /lang ptbr",
    "LANG_USAGE": "Uso: /lang [en|ptbr]\n\nExemplo:\n/lang ptbr ÔÇö mudar para Portugu├¬s\n/lang en ÔÇö mudar para Ingl├¬s",

    # General/errors
    "ERROR_GENERIC": "Ocorreu um erro. Tente novamente mais tarde.",
    "HELP_HINT": "Precisa de ajuda? Use /help",
}
