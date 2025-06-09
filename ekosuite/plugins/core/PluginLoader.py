import importlib
import sys
import pkgutil

from ekosuite.plugins.core.PluginInterface import PluginInterface

import ekosuite.plugins.plugin_implementations
from ekosuite.plugins.plugin_implementations import ProjectAssistant

class PluginLoader:
    def __init__(self):
        self.plugins: list[type[PluginInterface]] = []
    
    def queryPlugins(self):
        
        # If running in a PyInstaller bundle, return hard-coded plugins, else development plugins
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            self.plugins = [ProjectAssistant.ProjectAssistant]
            return

        package = ekosuite.plugins.plugin_implementations
        for finder, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
            full_name = package.__name__ + '.' + name if '.' not in name else name
            plugin = importlib.import_module(full_name)
            for attr_name in dir(plugin):
                attr = getattr(plugin, attr_name)
                if isinstance(attr, type):  # Ensure it's a class
                    if issubclass(attr, PluginInterface) and attr is not PluginInterface:
                        print(f"Found plugin: {attr.__name__}")
                        self.plugins.append(attr)