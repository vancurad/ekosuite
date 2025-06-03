from ekosuite.plugins.core.PluginLoader import PluginLoader
from .AppSettings import AppSettings
from ekosuite.plugins.core.PluginInterface import PluginInterface
from PyQt5.QtWidgets import QWidget, QBoxLayout, QRadioButton

class SelectPlugins(QWidget):
    def __init__(self, pluginLoader: PluginLoader, appSettings: AppSettings, update: lambda selection: list[type[PluginInterface]]):
        super().__init__()
        self.appSettings = appSettings
        self.setWindowTitle("Select Plugins")
        self.setGeometry(100, 100, 300, 200)
        self._update = update
        layout = QBoxLayout(QBoxLayout.TopToBottom)
        for plugin in pluginLoader.plugins:
            childLayout = QBoxLayout(QBoxLayout.LeftToRight)
            radioButton = QRadioButton()
            radioButton.setText(plugin.name())
            radioButton.setChecked(plugin in self.appSettings.pluginSelection.selectedPlugins)
            radioButton.toggled.connect(lambda checked, plugin=plugin: self.togglePlugin(plugin, checked))
            childLayout.addWidget(radioButton)
            layout.addLayout(childLayout)
        self.setLayout(layout)
    
    def togglePlugin(self, plugin, checked):
        selectedPlugins = self.appSettings.pluginSelection.selectedPlugins
        if checked and plugin not in self.appSettings.pluginSelection.selectedPlugins:
            selectedPlugins.append(plugin)
            self.appSettings.pluginSelection.selectedPlugins = selectedPlugins
            self._update(selectedPlugins)
        elif not checked and plugin in self.appSettings.pluginSelection.selectedPlugins:
            selectedPlugins.remove(plugin)
            self.appSettings.pluginSelection.selectedPlugins = selectedPlugins
            self._update(selectedPlugins)