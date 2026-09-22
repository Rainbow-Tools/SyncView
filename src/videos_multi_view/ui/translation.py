"""Explicit text bindings: never translate user-entered labels or filenames."""

from PySide6.QtCore import QObject, QSignalBlocker

from videos_multi_view.i18n import tr


def bind[T: QObject](widget: T, source: str, setter: str = "setText", **values: object) -> T:
    bindings = getattr(widget, "_text_bindings", {})
    bindings[setter] = (source, values)
    widget._text_bindings = bindings
    getattr(widget, setter)(tr(source, **values))
    return widget


def retranslate(root: QObject) -> None:
    """Update only registered presentation properties, without emitting edits."""
    for widget in [root, *root.findChildren(QObject)]:
        with QSignalBlocker(widget):
            for setter, (source, values) in getattr(widget, "_text_bindings", {}).items():
                getattr(widget, setter)(tr(source, **values))
