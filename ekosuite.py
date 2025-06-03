import sys
from PyQt5.QtWidgets import QApplication, QLabel
import asyncio

from ekosuite.app.App import App

class AppLauncher:
    def __init__(self):
        pass
    
    async def launch(self):
        app = App()
        await app.run()

async def main():
    await AppLauncher().launch()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())