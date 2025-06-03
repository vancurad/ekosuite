from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from ekosuite.app.AppDB import AppDB
from ekosuite.plugins.core.PluginUserInterface import PluginUserInterface

Input = TypeVar('Input')
class PluginInterface(ABC, Generic[Input]):
    @abstractmethod
    def initialize(self, db: AppDB):
        """Initialize the plugin."""
        pass
    
    @abstractmethod
    def name() -> str:
        """Return the name of the plugin."""
        pass

    @abstractmethod
    def description() -> str:
        """Return the description of the plugin."""
        pass

    @abstractmethod
    def getUserInterface(self) -> PluginUserInterface:
        """Return the user interface for the plugin or `None` if it doesn't apply."""
        return None

    @abstractmethod
    def execute(self, input: Input, db: AppDB):
        """Execute the plugin's main functionality."""
        pass

    @abstractmethod
    def terminate(self):
        """Clean up resources and terminate the plugin."""
        pass