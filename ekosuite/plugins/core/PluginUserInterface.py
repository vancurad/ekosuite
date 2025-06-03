from PyQt5.QtWidgets import QWidget

class PluginUserInterface:
    """
    Interface for a QT view that can be embedded inside a window.
    """

    def __init__(self, parent=None):
        """
        Initialize the QT view.

        :param parent: The parent widget, if any.
        """
        super().__init__()

    def createUi(self) -> QWidget:
        """
        Set up the user interface components.
        Override this method to define the layout and widgets.
        """
        raise NotImplementedError("Subclasses must implement the setup_ui method.")
    
    def clearLayout(self, layout):
        while layout.count():  # Check if there are items in the layout
            item = layout.takeAt(0)  # Remove the first item
            widget = item.widget()  # Get the associated widget
            if widget is not None:
                widget.deleteLater()  # Schedule widget for deletion
            elif item.layout():  # If the item is another layout, clear it recursively
                self.clearLayout(item.layout())