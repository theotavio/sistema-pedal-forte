ESTILO_CLARO_MODERNO = """
QMainWindow {
    background-color: #F1F5F9;
}

QWidget {
    font-family: "Segoe UI", "Roboto", "Helvetica Neue", -apple-system, sans-serif;
    font-size: 13px;
    color: #1E293B;
}

QFrame#sidebar {
    background-color: #0F172A;
    border-right: 1px solid #1E293B;
    min-width: 250px;
    max-width: 250px;
}

QLabel#brandTitle {
    color: #38BDF8;
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 1px;
    padding: 22px 16px 4px 16px;
}

QLabel#brandSubtitle {
    color: #94A3B8;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 0px 16px 18px 16px;
    border-bottom: 1px solid #1E293B;
}

QPushButton.nav-btn {
    background-color: transparent;
    color: #CBD5E1;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 9px 14px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
    margin: 2px 10px;
    min-height: 20px;
}

QPushButton.nav-btn:hover {
    background-color: #1E293B;
    color: #F8FAFC;
    border-color: #334155;
}

QPushButton.nav-btn:checked {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: 700;
    border-color: #3B82F6;
    border-left: 4px solid #93C5FD;
}

QFrame.card {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 12px;
    padding: 18px;
}

QFrame.stat-card {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 12px;
    padding: 18px;
}

QFrame.stat-card:hover {
    border-color: #94A3B8;
}

QLabel.stat-title {
    color: #475569;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel.stat-value {
    color: #0F172A;
    font-size: 28px;
    font-weight: 800;
    margin-top: 4px;
}

QLabel.view-header-title {
    color: #0F172A;
    font-size: 22px;
    font-weight: 800;
}

QLabel.view-header-subtitle {
    color: #475569;
    font-size: 13px;
    font-weight: 500;
}

QPushButton {
    font-size: 13px;
    font-weight: 600;
    border-radius: 8px;
    padding: 7px 16px;
    min-height: 22px;
}

QPushButton.btn-primary {
    background-color: #2563EB;
    color: #FFFFFF;
    border: 1px solid #1D4ED8;
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
    min-height: 22px;
}

QPushButton.btn-primary:hover {
    background-color: #1D4ED8;
}

QPushButton.btn-primary:pressed {
    background-color: #1E40AF;
}

QPushButton.btn-primary:disabled {
    background-color: #CBD5E1;
    border-color: #CBD5E1;
    color: #94A3B8;
}

QPushButton.btn-secondary {
    background-color: #FFFFFF;
    color: #334155;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 13px;
    font-weight: 600;
    min-height: 22px;
}

QPushButton.btn-secondary:hover {
    background-color: #F1F5F9;
    border-color: #94A3B8;
    color: #0F172A;
}

QPushButton.btn-secondary:disabled {
    background-color: #F1F5F9;
    border-color: #E2E8F0;
    color: #CBD5E1;
}

QPushButton.btn-success {
    background-color: #059669;
    color: #FFFFFF;
    border: 1px solid #047857;
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
    min-height: 22px;
}

QPushButton.btn-success:hover {
    background-color: #047857;
}

QPushButton.btn-success:disabled {
    background-color: #A7F3D0;
    border-color: #A7F3D0;
    color: #FFFFFF;
}

QPushButton.btn-danger {
    background-color: #DC2626;
    color: #FFFFFF;
    border: 1px solid #B91C1C;
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 13px;
    font-weight: 600;
    min-height: 22px;
}

QPushButton.btn-danger:hover {
    background-color: #B91C1C;
}

QPushButton.btn-danger:disabled {
    background-color: #FECACA;
    border-color: #FECACA;
    color: #FFFFFF;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 6px 12px;
    color: #0F172A;
    font-size: 13px;
    min-height: 22px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #2563EB;
    padding: 5px 11px;
}

QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #F1F5F9;
    color: #94A3B8;
    border-color: #E2E8F0;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid #E2E8F0;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #EFF6FF;
    selection-color: #1E3A8A;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 7px 10px;
    border-radius: 6px;
    color: #1E293B;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #F1F5F9;
}

QTableWidget, QTableView {
    background-color: #FFFFFF;
    alternate-background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    gridline-color: #E2E8F0;
    selection-background-color: #DBEAFE;
    selection-color: #1E40AF;
    outline: none;
}

QTableWidget::item {
    padding: 6px 10px;
}

QTableWidget::item:selected {
    background-color: #DBEAFE;
    color: #1E40AF;
}

QHeaderView {
    background-color: #E2E8F0;
    border: none;
}

QHeaderView::section {
    background-color: #E2E8F0;
    color: #1E293B;
    font-weight: 700;
    font-size: 12px;
    padding: 9px 12px;
    border: none;
    border-bottom: 2px solid #CBD5E1;
    border-right: 1px solid #CBD5E1;
}

QHeaderView::section:horizontal {
    background-color: #E2E8F0;
    color: #1E293B;
}

QTableCornerButton::section {
    background-color: #E2E8F0;
    border: none;
    border-bottom: 2px solid #CBD5E1;
}

QScrollBar:vertical {
    background-color: #F1F5F9;
    width: 14px;
    margin: 0px;
    border-radius: 7px;
}

QScrollBar::handle:vertical {
    background-color: #CBD5E1;
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94A3B8;
}

QScrollBar::handle:vertical:pressed {
    background-color: #64748B;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    background: none;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #F1F5F9;
    height: 14px;
    margin: 0px;
    border-radius: 7px;
}

QScrollBar::handle:horizontal {
    background-color: #CBD5E1;
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #94A3B8;
}

QScrollBar::handle:horizontal:pressed {
    background-color: #64748B;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    background: none;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}

QTreeWidget {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 8px;
    outline: none;
}

QTreeWidget::item {
    padding: 7px 6px;
    border-radius: 6px;
}

QTreeWidget::item:hover {
    background-color: #F1F5F9;
}

QTreeWidget::item:selected {
    background-color: #DBEAFE;
    color: #1E40AF;
}

QTabWidget::pane {
    border: 1px solid #CBD5E1;
    background-color: #FFFFFF;
    border-radius: 10px;
    top: -1px;
}

QTabBar::tab {
    background-color: #E2E8F0;
    color: #475569;
    padding: 9px 18px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #2563EB;
    border: 1px solid #CBD5E1;
    border-bottom-color: #FFFFFF;
    border-top: 3px solid #2563EB;
    font-weight: 700;
}

QTabBar::tab:hover:!selected {
    background-color: #CBD5E1;
    color: #0F172A;
}

QSplitter::handle {
    background-color: #CBD5E1;
    height: 6px;
    width: 6px;
    border-radius: 3px;
    margin: 3px 0px;
}

QSplitter::handle:hover {
    background-color: #2563EB;
}

QDialog {
    background-color: #F1F5F9;
}

QMessageBox {
    background-color: #FFFFFF;
}

QMessageBox QLabel {
    color: #1E293B;
    font-size: 13px;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 7px 18px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
}

QToolTip {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}
"""

MODERN_LIGHT_STYLE = ESTILO_CLARO_MODERNO
