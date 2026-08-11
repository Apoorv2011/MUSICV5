_styles: dict[int, int] = {}
_default: int = 4


def set_default(style: int) -> None:
    global _default
    _default = style


def get_style(chat_id: int) -> int:
    return _styles.get(chat_id, _default)


def set_style(chat_id: int, style: int) -> None:
    _styles[chat_id] = style
