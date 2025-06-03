import json
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QBoxLayout, QLayout, QPushButton, QGridLayout, QMainWindow

from .FileSystemObserver import FileSystemObserver, FileSystemImageChangeListener
from ekosuite.app.AppDB import AppDB
from ekosuite.app.AppSettings import AppSettings
from ekosuite.plugins.core.PluginLoader import PluginLoader
from ekosuite.plugins.core.PluginSelection import PluginSelection
from ekosuite.plugins.core.PluginInterface import PluginInterface
from .SelectPlugins import SelectPlugins
from .DataStream import DataStream

from ekosuite.plugins.model.project.ProjectDB import ProjectDB
import asyncio
from threading import Thread
from PyQt5.QtWidgets import QFileDialog

class App:
    def __init__(self):
        self.title = "EkoSuite"
        self.version = "1.0.0"
        self.author = "Daniel Vancura"
        self.db = AppDB()
        self.projectDB = ProjectDB(self.db)
        self.fileSystemObserver = FileSystemObserver(self.db)
        
        self.pluginLoader = PluginLoader()
        self.pluginLoader.queryPlugins()

        self.appSettings = AppSettings(pluginSelection=PluginSelection(self.pluginLoader, db=self.db))
        self.selectPluginWindow: SelectPlugins | None = None

        self._app = QApplication(sys.argv)

        self.activePlugins: list[PluginInterface] = []
        for selection in self.appSettings.pluginSelection.selectedPlugins:
            if selection in self.pluginLoader.plugins:
                self.activePlugins.append(selection(self.db))
    
    def _receiveImage(self, image):
        for plugin in self.activePlugins:
            plugin.execute(image, self.db)
    
    @property
    def activePlugins(self) -> list[PluginInterface]:
        return self._activePlugins
    
    @activePlugins.setter
    def activePlugins(self, value: list[PluginInterface]):
        self._activePlugins = value

    async def run(self):
        # Start listening to file updates in active folders
        def insertImage(image):
            print(f"Received new image: {image.filename}")
            asyncio.run(self.projectDB.insertImage(image))

        self.fileSystemObserver.addListener(FileSystemImageChangeListener(lambda image: insertImage(image)))

        self._mainWindow = QMainWindow()
        self._mainWindow.setGeometry(100, 100, 800, 600)
        self.resetUi()
        self._mainWindow.setWindowTitle(self.title)
        self._mainWindow.setCentralWidget(self._mainWidget)
        self._mainWindow.show()
        sys.exit(self._app.exec_())
    
    def resetUi(self):
        self._mainWidget = QWidget()
        self._mainWidget.setLayout(self.mainLayout())
        self._mainWindow.setCentralWidget(self._mainWidget)
    
    def mainLayout(self) -> QLayout:
        layout = QBoxLayout(QBoxLayout.TopToBottom)
        
        menu = QBoxLayout(QBoxLayout.LeftToRight)
        plugin_selection = self.pluginSelection()
        menu.addWidget(plugin_selection)
        folder_list = self.createFolderListButton()
        menu.addWidget(folder_list)
        folder_selection = self.createFolderPickerButton()
        menu.addWidget(folder_selection)
        
        menu.addStretch()

        layout.addLayout(menu)
        layout.addLayout(self.pluginLayout())
        return layout
    
    def pluginLayout(self) -> QLayout:
        layout = QGridLayout()

        for plugin in self.activePlugins:
            widget = plugin.getUserInterface().createUi()
            layout.addWidget(widget)
        return layout

    def createFolderListButton(self) -> QPushButton:
        button = QPushButton("Show Selected Folders")
        button.setMinimumHeight(30)
        button.clicked.connect(self.showFolderListWindow)
        return button

    def showFolderListWindow(self):
        folder_list_window = QMainWindow(self._mainWindow)
        folder_list_window.setWindowTitle("Selected Folders")
        folder_list_window.setGeometry(150, 150, 400, 300)

        widget = QWidget()
        layout = QBoxLayout(QBoxLayout.TopToBottom)

        for folder in self.projectDB.selectedFolders:
            folder_button = QPushButton(folder)
            folder_button.setEnabled(False)
            layout.addWidget(folder_button)

        widget.setLayout(layout)
        folder_list_window.setCentralWidget(widget)
        folder_list_window.show()

    def createFolderPickerButton(self) -> QPushButton:
        button = QPushButton("Select Folder")
        button.setMinimumHeight(30)
        button.clicked.connect(self.openFolderPicker)
        return button

    def openFolderPicker(self):
        folder = QFileDialog.getExistingDirectory(self._mainWindow, caption="Select Folder")
        if folder:
            selected_folders = self.projectDB.selectedFolders
            if folder not in selected_folders:
                selected_folders.append(folder)
            self.projectDB.selectedFolders = selected_folders
            self.fileSystemObserver.setupObservers()

    def pluginSelection(self) -> QWidget:
        button = QPushButton("Select Plugins")
        button.setMinimumHeight(30)
        button.clicked.connect(self.selectPlugins)
        return button
    
    def selectPlugins(self):
        self.selectPluginWindow = SelectPlugins(self.pluginLoader, self.appSettings, lambda selection : self.didUpdateSelection(selection))
        
        self.selectPluginWindow.show()

    def didUpdateSelection(self, selection: list[type[PluginInterface]]):
        for selected in self.activePlugins:
            if type(selected) not in selection:
                self.activePlugins.remove(selected)
        for newly_added in selection:
            if newly_added not in self.activePlugins:
                self.activePlugins.append(newly_added(self.db))

        self.resetUi()