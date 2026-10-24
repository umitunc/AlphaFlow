# -*- coding: utf-8 -*-
"""
Single Responsibility: Karanlık stüdyo arayüz teması (Qt StyleSheet).
"""

STUDIO_DARK_QSS = """
QMainWindow, QWidget {
    background-color: #111318;
    color: #E6E8EE;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #181B22;
    border: 1px solid #282D3A;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px;
    font-weight: 600;
    color: #D5A853;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QPushButton {
    background-color: #232834;
    border: 1px solid #363D4E;
    border-radius: 6px;
    padding: 8px 16px;
    color: #F0F2F8;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #2E3545;
    border-color: #D5A853;
}
QPushButton#PrimaryConvertBtn {
    background-color: #C89B3C;
    border: 1px solid #E5B95C;
    color: #111318;
    font-size: 14px;
    font-weight: 700;
    padding: 10px 22px;
}
QPushButton#PrimaryConvertBtn:hover {
    background-color: #DFB252;
}
QPushButton#PrimaryConvertBtn:disabled {
    background-color: #2B2F3A;
    border-color: #3A3F4D;
    color: #6C7280;
}
QComboBox, QLineEdit {
    background-color: #1E222B;
    border: 1px solid #323846;
    border-radius: 5px;
    padding: 6px 10px;
    color: #EAECEF;
}
QProgressBar {
    background-color: #1B1F27;
    border: 1px solid #2E3442;
    border-radius: 6px;
    text-align: center;
    height: 22px;
    font-weight: 600;
    color: #FFFFFF;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9E7322, stop:1 #E0B354);
    border-radius: 5px;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #252A36;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #C89B3C;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #F0C869;
    width: 14px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 7px;
}
"""
