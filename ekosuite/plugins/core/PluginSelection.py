import json
from ekosuite.app.AppDB import AppDB
from ekosuite.plugins.core.PluginInterface import PluginInterface
from ekosuite.plugins.core.PluginLoader import PluginLoader

class PluginSelection:
    """
    Class to manage the selection of plugins.
    """

    def __init__(self, pluginLoader: PluginLoader, db: AppDB):
        self.availablePlugins: list[type[PluginInterface]] = pluginLoader.plugins
        self.db = db
        self._didUpdate = {}
    
    def didUpdateSelection(self, callback):
        """
        Register a callback to be called when the plugin selection is updated.
        """
        self._didUpdate.add(callback)
    
    @property
    def selectedPlugins(self) -> list[type[PluginInterface]]:
        plugins: list[str] = self.db.execute("SELECT name FROM plugin_selection ORDER BY idx ASC").fetchall()

        result = []
        for available in self.availablePlugins:
            for plugin in plugins:
                name = available.name()
                if name == plugin[0]:
                    result.append(available)
                    break
        return result

    @selectedPlugins.setter
    def selectedPlugins(self, plugins: list[type[PluginInterface]]):
        self.db.execute("DELETE FROM plugin_selection")
        for index in range(len(plugins)):
            self.db.execute("INSERT INTO plugin_selection (name, idx) VALUES (?, ?)", (plugins[index].name(), index))
        for callback in self._didUpdate:
            callback(plugins)
