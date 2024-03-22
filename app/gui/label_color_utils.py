from PyQt5.QtWidgets import QLabel, QGraphicsColorizeEffect
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

def set_green_label_color(label: QLabel):
    _set_label_color(label, Qt.darkGreen)

def set_red_label_color(label: QLabel):
    _set_label_color(label, Qt.darkRed)

def set_yellow_label_color(label: QLabel):
    _set_label_color(label, Qt.darkYellow)

def _set_label_color(label: QLabel, color: QColor):
    color_effect = QGraphicsColorizeEffect() 
    color_effect.setColor(color) 
    label.setGraphicsEffect(color_effect)