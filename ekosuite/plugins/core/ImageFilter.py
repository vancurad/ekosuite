from typing import Callable, List, Sequence, Set
from PyQt5.QtWidgets import QWidget

from ekosuite.app.AppDB import AppDB
from enum import Enum
from PyQt5.QtWidgets import QComboBox, QVBoxLayout, QLabel

from ekosuite.plugins.model.images.DBImage import DBImage
from ekosuite.plugins.model.images.Image import Image
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView
from PyQt5.QtCore import QModelIndex

class FilterType(Enum):
    NIGHT = "night"
    TARGET = "target"
    TELESCOPE = "telescope"
    CAMERA = "camera"
    FILTER = "filter"

class ImageType(Enum):
    LIGHT = 'LIGHT'
    DARK = 'DARK'
    BIAS = 'BIAS'
    FLAT = 'FLAT'
    MASTER_DARK = 'MASTER DARK'
    MASTER_BIAS = 'MASTER BIAS'

class ImageFilter(QWidget):
      
    def __init__(self, db: AppDB, 
                 onFilterChange: Callable[[Sequence[Image]], None], 
                 allowedFilters: List[FilterType] = [FilterType.NIGHT, FilterType.TARGET, FilterType.CAMERA, FilterType.TELESCOPE, FilterType.FILTER], 
                 allowedImageTypes: List[ImageType] = [ImageType.LIGHT, ImageType.DARK, ImageType.BIAS, ImageType.FLAT, ImageType.MASTER_DARK, ImageType.MASTER_BIAS]):
        super().__init__()
        self._db = db
        self._allowedFilters = allowedFilters
        self._allowedImageTypes = allowedImageTypes
        self._onFilterChange = onFilterChange
        self.makeDropdownMenu()
        self._selectedImageIds: list[int] = list()
    
    def makeDropdownMenu(self):
        layout = QVBoxLayout(self)

        tree_widget = QTreeWidget(self)
        tree_widget.setHeaderLabels(["Filter Type", "Options"])
        tree_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        tree_widget.setRootIsDecorated(True)
        tree_widget.setItemsExpandable(True)

        def disableTopLevelSelection(item: QTreeWidgetItem, column: int):
            if not item.parent():
                item.setSelected(False)
            else:
                self.selectionChanged(tree_widget.selectedItems())

        tree_widget.itemClicked.connect(disableTopLevelSelection)

        for filter_type in self._allowedFilters:
            parent_item = QTreeWidgetItem(tree_widget)
            parent_item.setText(0, self.dropdownNameFor(filter_type))

            for target in self.dropdownTargetsFor(filter_type):
                child_item = QTreeWidgetItem(parent_item)
                child_item.setText(1, target[0])

        layout.addWidget(tree_widget)

        self.itemCountLabel = QLabel()
        layout.addWidget(self.itemCountLabel)

        self.setLayout(layout)

        self.selectionChanged([])
    
    def dropdownNameFor(self, filterType: FilterType):
        return filterType.value.capitalize()
    
    def dropdownTargetsFor(self, filterType: FilterType) -> List[str]:
        match filterType:
            case FilterType.NIGHT:
                return self._db.fetchall("SELECT DISTINCT start_day FROM night_sessions ORDER BY 1 ASC")
            case FilterType.TARGET:
                return self._db.fetchall("SELECT DISTINCT object FROM targets ORDER BY 1 ASC")
            case FilterType.TELESCOPE:
                return self._db.fetchall("SELECT DISTINCT telescope || ' ' || focal_length || 'mm' FROM fits_files ORDER BY 1 ASC")
            case FilterType.CAMERA:
                return self._db.fetchall("SELECT DISTINCT instrument FROM fits_files ORDER BY 1 ASC")
            case FilterType.FILTER:
                return self._db.fetchall("SELECT DISTINCT filter FROM fits_files ORDER BY 1 ASC")
            case _:
                return "Unknown Filter"
    
    def selectionChanged(self, items: List[QTreeWidgetItem]):
        def getFilters(filterType: FilterType, items: List[QTreeWidgetItem]) -> List[QTreeWidgetItem]:
            return list(filter(
                lambda item:
                (
                    (parent := item.parent()) is not None
                    and parent.text(0) == self.dropdownNameFor(filterType)
                ), 
                items))
        
        def getQuery(match_type: str, values: List[QTreeWidgetItem]) -> str:
            stmts = []
            for value in values:
                stmts.append(match_type + " = '" + value.text(1) + "'")
            return '(' + ' OR '.join(stmts) + ')'

        query_elements = [f"""
        SELECT ff.id AS id 
        FROM fits_files AS ff 
        JOIN night_session_fits_files AS nsff 
            ON nsff.fits_file_id = ff.id
        JOIN night_sessions AS ns
            ON nsff.night_session_id = ns.id
        WHERE image_type_generic IN {'(' + ','.join([f"'{imageType}'" for imageType in self._allowedImageTypes]) + ')'}
        """]

        night_filters = getFilters(FilterType.NIGHT, items)
        if len(night_filters) > 0:
            query_elements.append(getQuery('ns.start_day', night_filters))
        
        filter_filters = getFilters(FilterType.FILTER, items)
        if len(filter_filters) > 0:
            query_elements.append(getQuery('ff.filter', filter_filters))
        
        target_filters = getFilters(FilterType.TARGET, items)
        if len(target_filters) > 0:
            query_elements.append(getQuery('ff.object', target_filters))
        
        telescope_filters = getFilters(FilterType.TELESCOPE, items)
        if len(telescope_filters) > 0:
            query_elements.append(getQuery("ff.telescope || ' ' || ff.focal_length || 'mm'", telescope_filters))
        
        camera_filters = getFilters(FilterType.CAMERA, items)
        if len(camera_filters) > 0:
            query_elements.append(getQuery('ff.instrument', camera_filters))
        
        self.selectedImages = list(map(lambda val: DBImage(val[0], self._db), self._db.fetchall(' AND '.join(query_elements))))
        self.itemCountLabel.setText(f'{len(self.selectedImages)} images selected')

        if self._onFilterChange:
            self._onFilterChange(self.selectedImages)
