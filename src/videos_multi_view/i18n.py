"""Application text lookup, independent of Qt, filesystem access, and project data."""

from videos_multi_view.translations import ENGLISH

LANGUAGES = {"ko": "한국어", "en": "English"}
_language = "ko"


def language() -> str:
    return _language


def set_language(code: str) -> None:
    global _language
    if code not in LANGUAGES:
        raise ValueError(f"Unsupported language: {code}")
    _language = code


def tr(source: str, **values: object) -> str:
    """Translate a message template before substituting user-controlled values."""
    translated = ENGLISH.get(source, source) if _language == "en" else source
    return translated.format(**values) if values else translated
