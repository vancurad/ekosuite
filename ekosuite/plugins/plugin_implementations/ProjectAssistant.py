from typing import Callable
from ekosuite.app.AppDB import AppDB
from ekosuite.plugins.core.ImageFilter import ImageFilter
from ekosuite.plugins.model.images.DBImage import DBImage
from ekosuite.plugins.core.PluginInterface import PluginInterface
from ekosuite.plugins.core.PluginUserInterface import PluginUserInterface
from ekosuite.plugins.model.images import Image
from PyQt5.QtWidgets import \
    QWidget, QBoxLayout, QPushButton, QLabel, \
    QTreeWidgetItem, QTreeWidget, QAbstractItemView, \
    QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, \
    QScrollArea, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QDoubleValidator
from ekosuite.app.AppDB import AppDB
import os

class Item:
        def __init__(self, id: int, filename: str, gain: float | None, temperature: float | None, bias: float | None):
            self.id = id
            self.filename = filename
            self.gain = gain
            self.temperature = temperature
            self.offset = bias

class MissingDarkInfoSettings(QWidget):

    def __init__(self, db: AppDB):
        super().__init__()
        self._db = db
        self.faulty_darks = list(map(lambda it: Item(it[0], it[1], it[2], it[3], it[4]), self._db.fetchall("""
        SELECT id, filename, gain, sensor_temperature, bias
        FROM fits_files
        WHERE image_type_generic IN ('MASTER DARK', 'MASTER BIAS')
        ORDER BY gain IS NULL DESC, sensor_temperature IS NULL DESC, bias IS NULL DESC, create_time DESC;
        """)))
        self.create_numeric_list_widget(self.faulty_darks)

    def create_numeric_list_widget(self, items):
        main_layout = QVBoxLayout(self)
        scroll_layout = QVBoxLayout()
        pos_double_validator = QDoubleValidator()
        pos_double_validator.setBottom(0)
        max_str_len = 150
        
        for i in range(0, len(items)):
            # Create container widget for each row
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            
            # Main label
            main_label = QLabel(('...' + items[i].filename[len(items[i].filename) - max_str_len:]) if len(items[i].filename) > max_str_len else items[i].filename)
            main_label.setToolTip(items[i].filename)
            main_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            row_layout.addWidget(main_label, stretch=1)
            
            # Create two-column input section
            input_widget = QWidget()
            input_layout = QHBoxLayout(input_widget)
            input_layout.setContentsMargins(0, 0, 0, 0)
            
            # Left input group
            left_group = QWidget()
            left_layout = QVBoxLayout(left_group)
            left_layout.addWidget(QLabel('Gain'))
            left_layout.addWidget(QLabel('Offset'))
            left_layout.addWidget(QLabel('CCD Temperature'))
            
            # Right input group
            right_group = QWidget()
            right_layout = QVBoxLayout(right_group)

            gain_widget = QWidget()
            gain_layout = QHBoxLayout(gain_widget)

            offset_widget = QWidget()
            offset_layout = QHBoxLayout(offset_widget)

            temp_widget = QWidget()
            temp_layout = QHBoxLayout(temp_widget)

            gain_input = QLineEdit()
            gain_input.setText('' if items[i].gain is None else f'{items[i].gain}')
            gain_input.setValidator(pos_double_validator)

            offset_input = QLineEdit()
            offset_input.setText('' if items[i].offset is None else f'{items[i].offset}')
            offset_input.setValidator(pos_double_validator)

            temp_input = QLineEdit()
            temp_input.setText('' if items[i].temperature is None else f'{items[i].temperature}')
            temp_input.setValidator(QDoubleValidator())

            def _update(i, gain_input, temp_input, offset_input):
                if len(gain_input.text()):
                    self._db.execute(f"""
                    UPDATE OR IGNORE fits_files
                    SET gain = {gain_input.text()}
                    WHERE id = {items[i].id}
                    """)
                if len(temp_input.text()):
                    self._db.execute(f"""
                    UPDATE OR IGNORE fits_files
                    SET sensor_temperature = {temp_input.text()}
                    WHERE id = {items[i].id}
                    """)
                
                if len(offset_input.text()):
                    self._db.execute(f"""
                    UPDATE OR IGNORE fits_files
                    SET bias = {offset_input.text()}
                    WHERE id = {items[i].id}
                    """)
            update_button = QPushButton()
            update_button.setText('Update')
            update_button.clicked.connect(lambda _, i=i, gain_input=gain_input, temp_input=temp_input, offset_input=offset_input: _update(i, gain_input, temp_input, offset_input))

            gain_layout.addWidget(gain_input)
            gain_layout.addWidget(update_button)

            offset_layout.addWidget(offset_input)
            temp_layout.addWidget(temp_input)

            right_layout.addWidget(gain_widget)
            right_layout.addWidget(offset_widget)
            right_layout.addWidget(temp_widget)
            
            # Add input groups to layout
            input_layout.addWidget(left_group)
            input_layout.addWidget(right_group)
            
            # Add input section to row
            row_layout.addWidget(input_widget, stretch=2)
            
            # Add row to main layout
            scroll_layout.addWidget(row_widget)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)

        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)


class ProjectAssistant(PluginInterface):
    def __init__(self, db: AppDB):
        self._db = db
        super().__init__()

        self._ui = ProjectAssistantUI(self._db)

    def initialize(self, db: AppDB):
        self._db = db
        super().__init__()

        self._ui = ProjectAssistantUI(self._db)
    
    def name() -> str:
        """Return the name of the plugin."""
        return "Project Assistant"

    def description() -> str:
        """Return the description of the plugin."""
        return """
        This plugin helps you prepare a project by matching light frames with the right calibration
        frames and creating a folder structure for a project to prepare for stacking & editing.
        """

    def getUserInterface(self) -> PluginUserInterface:
        """Return the user interface for the plugin or `None` if it doesn't apply."""
        return self._ui

    def execute(self, input: Image, db: AppDB):
        """Execute the plugin's main functionality."""
        self._ui.updateUi()

    def terminate(self):
        """Clean up resources and terminate the plugin."""
        pass

class Option:
    def __init__(self, title: str, on_click: Callable, is_selected: bool):
        self.title = title
        self.onClick = on_click
        self.isSelected = is_selected

class Settings:
    def __init__(self, title: str, options: list[Option]):
        self.title = title
        self.options = options

class ProjectAssistantUI(PluginUserInterface):
    
    @property
    def _selectedDarkValidity(self) -> str:
        selected_option = self._db.fetchall("SELECT value FROM user_settings WHERE item == 'dark_validity'")
        if selected_option is None or len(selected_option) == 0:
            self._db.execute('INSERT OR REPLACE INTO user_settings VALUES ("dark_validity", "3 months")')
            selected_option = self._db.fetchall("SELECT IFNULL(value, '3 months') value FROM user_settings WHERE item == 'dark_validity'")[0]
        return selected_option[0][0] if selected_option is not None and len(selected_option) > 0 else '3 months'

    def _settings(self) -> list[Settings]:
        def setDarkValidity(time: str):
            self._db.execute(f'INSERT OR REPLACE INTO user_settings VALUES ("dark_validity", "{time}")')
            self.updateUi()        

        return [
            Settings('How long are dark and bias frames valid?', [
                Option('8 hours', lambda: setDarkValidity('8 hours'), self._selectedDarkValidity == '8 hours'),
                Option('1 day', lambda: setDarkValidity('1 day'), self._selectedDarkValidity == '1 day'),
                Option('7 days', lambda: setDarkValidity('7 days'), self._selectedDarkValidity == '7 days'),
                Option('1 month', lambda: setDarkValidity('1 month'), self._selectedDarkValidity == '1 month'),
                Option('3 months', lambda: setDarkValidity('3 months'), self._selectedDarkValidity == '3 months'),
                Option('6 months', lambda: setDarkValidity('6 months'), self._selectedDarkValidity == '6 months'),
                Option('1 year', lambda: setDarkValidity('1 year'), self._selectedDarkValidity == '1 year')
            ])
        ]

    def __init__(self, db: AppDB, parent=None):
        """
        Initialize the QT view.

        :param parent: The parent widget, if any.
        """
        super().__init__(parent)
        
        self._widget = QWidget()
        self._values = list[float]()

        self._db = db
        self._chosenNight = None
        self._selectedImages = []

    def createUi(self) -> QWidget:
        self._layout = QBoxLayout(QBoxLayout.TopToBottom, self._widget)
        self._widget.setLayout(self._layout)
        
        self.updateUi()

        return self._widget
    
    def _toggleSettings(self):
        if self._settings_window.isVisible():
            return
        
        widget = QWidget()
        
        tree_widget = QTreeWidget(widget)
        tree_widget.setHeaderLabels(["Settings", "Options"])
        tree_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        tree_widget.setRootIsDecorated(True)
        tree_widget.setItemsExpandable(True)

        settings = self._settings()

        def selectionChanged(item: QTreeWidgetItem):
            settings[item.parent().type()].options[item.type()].onClick()

        def disableTopLevelSelection(item: QTreeWidgetItem, column: int):
            if not item.parent():
                item.setSelected(False)
            else:
                selectionChanged(item)

        tree_widget.itemClicked.connect(disableTopLevelSelection)

        i = 0
        for setting in settings:
            parent_item = QTreeWidgetItem(tree_widget, type=i)
            i += 1
            parent_item.setText(0, setting.title)

            j = 0
            for option in setting.options:
                child_item = QTreeWidgetItem(parent_item, type=j)
                j += 1
                child_item.setText(1, option.title)
                child_item.setSelected(option.isSelected)

        layout = QBoxLayout(QBoxLayout.TopToBottom)
        layout.addWidget(tree_widget)
        widget.setLayout(layout)

        self._settings_window.setCentralWidget(widget)
        self._settings_window.show()
    
    def _selectImages(self, images: list[DBImage]):
        self._selectedImages = images
        self._runValidations()

    def updateUi(self):
        self.clearLayout(self._layout)

        self._warningLabel = QLabel()
        self._warningLabel.setText('')
        self._warningLabel.setHidden(True)

        missing_dark_info_button = QPushButton()
        missing_dark_info_button.setText('Add missing info for master dark/bias frames')
        def _onTapMissingDarkButton():
            if self._add_missing_dark_info_window.isVisible():
                return
            
            settings = MissingDarkInfoSettings(self._db)
            self._add_missing_dark_info_window.setCentralWidget(settings)
            self._add_missing_dark_info_window.show()

        missing_dark_info_button.clicked.connect(lambda _: _onTapMissingDarkButton())

        self._prepareProjectButton = QPushButton()
        self._prepareProjectButton.setText('Prepare Project')
        self._prepareProjectButton.setEnabled(False)
        self._prepareProjectButton.clicked.connect(lambda _: self._start_project())

        self._settings_window = QMainWindow(self._widget.window())
        self._settings_window.setWindowTitle("Settings")
        self._settings_window.setGeometry(150, 150, 400, 300)

        self._add_missing_dark_info_window = QMainWindow(self._widget.window())
        self._add_missing_dark_info_window.setWindowTitle("Add missing info")
        self._add_missing_dark_info_window.setGeometry(150, 150, 1200, 300)

        self._settingsButton = QPushButton()
        self._settingsButton.setText('Settings')
        self._settingsButton.clicked.connect(lambda _: self._toggleSettings())

        image_filter = ImageFilter(self._db, lambda images: self._selectImages(images), allowedImageTypes=['LIGHT'])
        image_filter.setMaximumHeight(300)
        self._layout.addWidget(self._settingsButton)
        self._layout.addWidget(image_filter)
        self._layout.addWidget(self._warningLabel)
        self._layout.addWidget(missing_dark_info_button)
        self._layout.addWidget(self._prepareProjectButton)
    
    def _validateTargetNames(self) -> list[str]:
        query = f"""
        SELECT DISTINCT(t.id) 
        FROM targets AS t
        INNER JOIN fits_files AS ff
        ON ff.object = t.object
        WHERE ff.id IN ({', '.join(map(lambda image: str(image._id), self._selectedImages))})
        """
        distinct_targets = self._db.fetchall(query)
        return list(map(lambda tup: tup[0], distinct_targets))
    
    def _createDarkQuery(self, light_ids: list[int], fields: str = 'DISTINCT(ld.id)') -> str:
        params = ', '.join(map(lambda id: f'{id}', light_ids))

        return f"""
        WITH light_dates AS (
            SELECT id, filename, create_time, exptime, gain, bias, sensor_temperature
            FROM fits_files
            WHERE id in ({params}) AND image_type_generic = 'LIGHT'
        )
        SELECT {fields}
        FROM light_dates ld
        JOIN fits_files ff
        WHERE ld.create_time 
            BETWEEN DATETIME(ff.create_time, '-{self._selectedDarkValidity}') 
            AND DATETIME(ff.create_time, '+{self._selectedDarkValidity}')
            AND ff.image_type_generic = 'MASTER DARK'
            AND ff.gain = ld.gain
            AND ff.bias = ld.bias
            AND ff.exptime > (ld.exptime - 0.5)
            AND ff.exptime < (ld.exptime + 0.5)
            AND ff.sensor_temperature > (ld.sensor_temperature - 1)
            AND ff.sensor_temperature < (ld.sensor_temperature + 1)
        """

    def _createBiasQuery(self, light_ids: list[int], fields: str = 'DISTINCT(ld.id)') -> str:
        params = ', '.join(map(lambda id: f'{id}', light_ids))

        return f"""
        WITH light_dates AS (
            SELECT id, filename, create_time, exptime, gain, bias, sensor_temperature
            FROM fits_files
            WHERE id in ({params}) AND image_type_generic = 'LIGHT'
        )
        SELECT {fields}
        FROM light_dates ld
        JOIN fits_files ff
        WHERE ld.create_time 
            BETWEEN DATETIME(ff.create_time, '-{self._selectedDarkValidity}') 
            AND DATETIME(ff.create_time, '+{self._selectedDarkValidity}')
            AND ff.image_type_generic = 'MASTER BIAS'
            AND ff.gain = ld.gain
            AND ff.sensor_temperature > (ld.sensor_temperature - 1)
            AND ff.sensor_temperature < (ld.sensor_temperature + 1)
        """
    
    def _validateDarkFrames(self) -> set[int]:
        query_filters = self._createDarkQuery(list(map(lambda image: str(image._id), self._selectedImages)))
        matching_darks = set(map(lambda val: val[0], self._db.fetchall(query_filters)))
        images_without_darks = set(map(lambda val: val._id, self._selectedImages))
        for dark in matching_darks:
            images_without_darks.discard(dark)
        return images_without_darks
    
    def _validateBiasFrames(self) -> set[int]:
        params = ', '.join(map(lambda image: str(image._id), self._selectedImages))

        query_filters = f"""
        WITH light_dates AS (
            SELECT id, create_time, exptime, gain, bias, sensor_temperature
            FROM fits_files
            WHERE id in ({params}) AND image_type_generic = 'LIGHT'
        )
        SELECT DISTINCT(ld.id)
        FROM light_dates ld
        JOIN fits_files ff
        WHERE ld.create_time 
            BETWEEN DATETIME(ff.create_time, '-{self._selectedDarkValidity}') 
            AND DATETIME(ff.create_time, '+{self._selectedDarkValidity}')
            AND ff.image_type_generic = 'MASTER BIAS'
            AND ff.gain = ld.gain
            AND ff.sensor_temperature > (ld.sensor_temperature - 1)
            AND ff.sensor_temperature < (ld.sensor_temperature + 1)
        """
        matching_bias = set(map(lambda val: val[0], self._db.fetchall(query_filters)))
        images_without_bias = set(map(lambda val: val._id, self._selectedImages))
        for dark in matching_bias:
            images_without_bias.discard(dark)
        return images_without_bias
    
    def _validateFlatFrames(self) -> set[int]:
        params = ', '.join(map(lambda image: str(image._id), self._selectedImages))
        
        # Query filters and sessions where those filters were used for all selected light frames
        query_filters = f"""
        WITH light_frames AS (
            SELECT ff.id AS id, ff.filter AS filter, nsff.night_session_id AS session_id
            FROM fits_files AS ff
            INNER JOIN night_session_fits_files AS nsff
            ON nsff.fits_file_id = ff.id
            WHERE ff.image_type_generic = 'LIGHT'
            AND ff.id IN ({params})
        ), flat_frames AS (
            SELECT ff.filter AS filter, nsff.night_session_id AS session_id
            FROM fits_files AS ff
            INNER JOIN night_session_fits_files AS nsff
            ON nsff.fits_file_id = ff.id
            WHERE ff.image_type_generic = 'FLAT' OR ff.image_type_generic = 'MASTER FLAT'
        )
        SELECT lf.id
        FROM light_frames lf
        WHERE NOT EXISTS (
            SELECT 1
            FROM flat_frames ff
            WHERE ff.filter = lf.filter 
            AND ff.session_id = lf.session_id
        )
        """
        lights_without_flats = self._db.fetchall(query_filters)
        return set(map(lambda row: row[0], lights_without_flats))
    
    def _runValidations(self):
        warning_messages = ''
        criticality = 0

        if len(self._selectedImages) == 0:
            criticality = max(criticality, 2)
            warning_messages += 'Error: Your filters do not match any images.\n'

        target_validation = self._validateTargetNames()
        if len(target_validation) > 1:
            criticality = max(criticality, 2)
            warning_messages += f'Error: You have selected images of {len(target_validation)} target objects.\n'
        
        flat_validation = self._validateFlatFrames()
        if len(flat_validation) > 0:
            criticality = max(criticality, 1)
            warning_messages += f'Warning: {len(flat_validation)} night sessions are lacking flat frames that match the used filters.\n'
        
        dark_validation = self._validateDarkFrames()
        if len(dark_validation) > 0:
            criticality = max(criticality, 1)
            warning_messages += f'Warning: {len(dark_validation)} images are lacking suitable dark frames.\n'
        
        bias_validation = self._validateBiasFrames()
        if len(bias_validation) > 0:
            criticality = max(criticality, 1)
            warning_messages += f'Warning: {len(bias_validation)} images are lacking suitable bias frames.\n'
        
        if len(warning_messages) > 0:
            self._warningLabel.setText(warning_messages)
            self._warningLabel.setStyleSheet("color: white" if criticality == 0 else "color: orange;" if criticality == 1 else "color: red;")
            self._warningLabel.setHidden(False)
        else:
            self._warningLabel.setText('')
            self._warningLabel.setHidden(True)
        
        self._prepareProjectButton.setEnabled(criticality <= 1)

    def _start_project(self):
        project_folder = self._pick_project_folder()
        if project_folder is None:
            return
        
        night_sessions = self._get_night_sessions()
        flats = self._get_flat_frames()
        
        for session in night_sessions:
            session_folder = os.path.join(project_folder, 'Night_' + session[0])
            light_folder = os.path.join(session_folder, 'light')
            dark_folder = os.path.join(session_folder, 'dark')
            bias_folder = os.path.join(session_folder, 'bias')
            flat_folder = os.path.join(session_folder, 'flat')
            try:
                os.makedirs(session_folder, exist_ok=True)
                for subfolder in [light_folder, dark_folder, bias_folder, flat_folder]:
                    os.makedirs(subfolder, exist_ok=True)
            except:
                if self._warningLabel:
                    self._warningLabel.setText('Error: Failed to create folders for project')
                    self._warningLabel.setStyleSheet("color: red;")
                return
            
            for sourceImage in session[1]:
                symlink = os.path.join(light_folder, os.path.basename(sourceImage))
                if not os.path.lexists(symlink):
                    os.symlink(sourceImage, symlink)
            
            for flat in flats.get(session[0], []):
                symlink = os.path.join(flat_folder, os.path.basename(flat))
                if not os.path.lexists(symlink):
                    os.symlink(flat, symlink)
            
            dark_query = self._createDarkQuery(session[2], 'DISTINCT(ff.filename)')
            darks = self._db.fetchall(dark_query)
            for dark in darks:
                symlink = os.path.join(dark_folder, os.path.basename(dark[0]))
                if not os.path.lexists(symlink):
                    os.symlink(dark[0], symlink)
            
            bias_query = self._createBiasQuery(session[2], 'DISTINCT(ff.filename)')
            biases = self._db.fetchall(bias_query)
            for bias in biases:
                symlink = os.path.join(bias_folder, os.path.basename(bias[0]))
                if not os.path.lexists(symlink):
                    os.symlink(bias[0], symlink)
    
    def _pick_project_folder(self) -> str | None:
        return QFileDialog.getExistingDirectory(self._widget, "Select a folder to create your project")
    
    def _get_night_sessions(self) -> list[(str, list[str], list[int])]:
        params = ', '.join(map(lambda image: str(image._id), self._selectedImages))
        results = self._db.fetchall(f"""
        SELECT ns.start_day, ff.filename, ff.id
        FROM fits_files AS ff
        JOIN night_session_fits_files AS nsff
        ON nsff.fits_file_id = ff.id
        JOIN night_sessions AS ns
        ON ns.id = nsff.night_session_id
        WHERE ff.image_type_generic = 'LIGHT'
        AND ff.id IN ({params})
        ORDER BY 1
        """)
        rows = list[(str, list[str], list[int])]()
        for result in results:
            if len(rows) > 0 and result[0] == rows[-1][0]:
                rows[-1][1].append(result[1])
                rows[-1][2].append(result[2])
            else:
                rows.append((result[0], [result[1]], [result[2]]))

        return rows
    
    def _get_flat_frames(self) -> dict[str, list[str]]:
        params = ', '.join(map(lambda image: str(image._id), self._selectedImages))

        query = f"""
        WITH light_frames AS (
            SELECT ff.id AS id, ff.filter AS filter, nsff.night_session_id AS session_id
            FROM fits_files AS ff
            INNER JOIN night_session_fits_files AS nsff
            ON nsff.fits_file_id = ff.id
            WHERE ff.image_type_generic = 'LIGHT'
            AND ff.id IN ({params})
        ), flat_frames AS (
            SELECT ff.filename AS filename, ff.filter AS filter, nsff.night_session_id AS session_id
            FROM fits_files AS ff
            INNER JOIN night_session_fits_files AS nsff
            ON nsff.fits_file_id = ff.id
            WHERE ff.image_type_generic = 'FLAT' OR ff.image_type_generic = 'MASTER FLAT'
        )
        SELECT ns.start_day, ff.filename AS filename, ff.session_id AS session_id
        FROM flat_frames ff
        JOIN light_frames lf
        ON lf.session_id = ff.session_id
            AND lf.filter = ff.filter
        JOIN night_sessions ns
        ON ns.id = ff.session_id
        """
        results = self._db.fetchall(query)

        matches = dict[str, list[str]]()
        for result in results:
            if matches.get(result[0]) is None:
                matches[result[0]] = [result[1]]
            else:
                matches[result[0]].append(result[1])

        return matches