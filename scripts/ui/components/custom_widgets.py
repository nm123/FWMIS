from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QComboBox


class NoWheelComboBox(QComboBox):
    """Custom QComboBox that ignores mouse wheel events unless focused"""

    def wheelEvent(self, event):
        """Override wheel event to only accept when widget has focus"""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            # Ignore wheel event when not focused
            event.ignore()
