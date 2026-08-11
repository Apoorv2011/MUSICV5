_primary = "auto"


def set_primary(backend: str) -> None:
    global _primary
    _primary = backend


def get_primary() -> str:
    return _primary
