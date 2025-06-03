from ekosuite.app.AppDB import AppDB
from ekosuite.plugins.core.PluginSelection import PluginSelection

class AppSettings:
    """
    This class holds the application settings.
    """
    def __init__(self, pluginSelection: PluginSelection):
        self._settings = {
            "version": "1.0.0",
            "debug": True,
        }
        self.pluginSelection = pluginSelection