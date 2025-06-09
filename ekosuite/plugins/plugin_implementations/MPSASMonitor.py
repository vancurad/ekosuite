from ekosuite.app.AppDB import AppDB
from ekosuite.plugins.core.PluginInterface import PluginInterface
from ekosuite.plugins.core.PluginUserInterface import PluginUserInterface
from ekosuite.plugins.model.images import Image
from PyQt5.QtWidgets import QWidget, QBoxLayout, QPushButton, QListWidget, QListWidgetItem, QSizePolicy
from PyQt5.QtCore import QSize
from ekosuite.app.AppDB import AppDB

from ekosuite.ui.Graph import Graph

class MPSASMonitor(PluginInterface):
    def __init__(self, db: AppDB):
        self._db = db
        super().__init__()

        self._ui = MPSASMonitorUI(self._db)

    def initialize(self):
        """Initialize the plugin."""
        # Initialization logic goes here
        pass

    def name() -> str:
        """Return the name of the plugin."""
        return "MPSAS Monitor"
    
    def description() -> str:
        """Return the description of the plugin."""
        return "Record and display MPSAS (magnitude per square arcsecond) if recorded and saved on FITS files."
    
    def getUserInterface(self) -> PluginUserInterface:
        """Return the user interface for the plugin or `None` if it doesn't apply."""
        return self._ui
    
    def execute(self, input: Image, db: AppDB):
        """Execute the plugin's main functionality."""
        self._ui.updateUi()

    def terminate(self):
        """Clean up resources and terminate the plugin."""
        # Cleanup logic goes here
        pass

class MPSASMonitorUI(PluginUserInterface):
    def __init__(self, db: AppDB, parent=None):
        """
        Initialize the QT view.

        :param parent: The parent widget, if any.
        """
        super().__init__(parent)
        
        self._widget = QWidget()
        self._values = list[float]()
        self._night_icon = QPushButton()
        self._db = db
        self._chosenNight = None
    
    @property
    def values(self) -> list[float]:
        """
        Get the values to be displayed in the graph.
        """
        return self._values
    @values.setter
    def values(self, values: list[float]):
        """
        Set the values to be displayed in the graph.
        """
        self._values = values
        self.updateUi()

    def createUi(self) -> QWidget:
        """
        Set up the user interface components.
        Override this method to define the layout and widgets.
        """
        query = self._db.execute("SELECT start_day FROM night_sessions ORDER BY start_day DESC LIMIT 1")
        latest_night = query.fetchone()
        if latest_night and self._chosenNight is None:
            self._chosenNight = latest_night[0]
        
        self._layout = QBoxLayout(QBoxLayout.TopToBottom, self._widget)
        self._widget.setLayout(self._layout)
        
        self.updateUi()

        return self._widget

    def updateUi(self):
        self.clearLayout(self._layout)

        if type(self._chosenNight) is str:
            keys = self._db.execute("""
                SELECT DATETIME(im.create_time, 'localtime')
                    FROM 
                        fits_files as im,
                        night_sessions as ns,
                        night_session_fits_files nsff
                    WHERE 
                        im.id = nsff.fits_file_id
                        AND nsff.night_session_id = ns.id
                        AND ns.start_day = ?
                    ORDER BY DATETIME(im.create_time) ASC
            """, (self._chosenNight, )).fetchall()
            values = self._db.execute("""
                SELECT im.mpsas 
                    FROM 
                        fits_files as im,
                        night_sessions as ns,
                        night_session_fits_files nsff
                    WHERE 
                        im.id = nsff.fits_file_id
                        AND nsff.night_session_id = ns.id
                        AND ns.start_day = ?
                    ORDER BY DATETIME(im.create_time) ASC
            """, (self._chosenNight, )).fetchall()
        else:
            keys = []
            values = []

        if values is None or keys is None:
            values = []
            keys = []

        self._layout.addWidget(Graph(
            [k[0] for k in keys], # range(1, len(values) + 1),
            [v[0] for v in values],
        ))
        night_icon = QPushButton()
        night_icon.setText(self._chosenNight)
        night_icon.setMinimumHeight(30)
        night_icon.clicked.connect(self.pickNight)
        self._layout.addWidget(night_icon)
        print("Updating UI with values:", self.values)
    
    def pickNight(self):
        self.widget = QWidget()
        self.widget.setWindowTitle("Choose a night")
        self.widget.setGeometry(150, 150, 400, 300)

        layout = QBoxLayout(QBoxLayout.TopToBottom)

        nights = self._db.execute("SELECT start_day FROM night_sessions ORDER BY start_day DESC").fetchall()
        if not nights:
            print("No nights found in database.")
            return

        list_view = QListWidget()  # Use QListWidget instead of QListView for simplicity.
        for night in nights:
            button = QPushButton(text=str(night[0]))  # Ensure night[0] is converted to string.
            button.clicked.connect(lambda checked, n=night: self.selectNight(n[0]))
            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(0, 50))
            list_view.addItem(list_item)
            list_view.setItemWidget(list_item, button)

        layout.addWidget(list_view)
        self.widget.setLayout(layout)
        self.widget.show()
    
    def selectNight(self, night: str):
        self._chosenNight = night
        self.updateUi()