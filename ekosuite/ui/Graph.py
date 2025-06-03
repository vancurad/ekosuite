from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QPen
from PyQt5.QtCore import Qt
import sys

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import pandas as pd
import numpy as np

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
    
class Graph(QWidget):
    def __init__(self, x_data, y_data, x_label='X', y_label='Y'):
        super().__init__()
        sc = MplCanvas(self, width=5, height=4, dpi=100)
        
        data = pd.DataFrame({
            y_label: y_data
        }, index=x_data)
        

        df = pd.DataFrame(data, columns=[x_label, y_label])
        df.plot(ax=sc.axes, kind='line', legend=False, color='blue', marker='o', markersize=5, linewidth=2, rot=10)

        layout = QVBoxLayout()
        layout.addWidget(sc)

        self.setLayout(layout)
