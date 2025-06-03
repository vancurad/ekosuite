import importlib
import os

from ekosuite.plugins.core.PluginInterface import PluginInterface

class PluginLoader:
    def __init__(self):
        self.plugins: list[type[PluginInterface]] = []
    
    def queryPlugins(self):
        # Directory where plugins are stored
        plugins_dir = "ekosuite/plugins/plugin-implementations"

        # Dynamically load and execute plugins
        for filename in os.listdir(plugins_dir):
            if filename.endswith(".py"):
                module_name = filename[:-3]
                module = importlib.import_module(f"ekosuite.plugins.plugin-implementations.{module_name}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type):  # Ensure it's a class
                        if issubclass(attr, PluginInterface) and attr is not PluginInterface:
                            print(f"Found plugin: {attr.__name__}")
                            self.plugins.append(attr)