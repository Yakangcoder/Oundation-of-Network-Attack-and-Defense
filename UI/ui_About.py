# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'About.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file! = dototodo
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QSizePolicy, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(480, 270)
        Dialog.setMinimumSize(QSize(320, 240))
        Dialog.setMaximumSize(QSize(16777215, 16777215))
        font = QFont()
        font.setPointSize(14)
        Dialog.setFont(font)
        self.horizontalLayout = QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.image_label = QLabel(Dialog)
        self.image_label.setObjectName(u"image_label")
        self.image_label.setMinimumSize(QSize(128, 128))
        self.image_label.setMaximumSize(QSize(128, 128))

        self.horizontalLayout.addWidget(self.image_label)

        self.version_label = QLabel(Dialog)
        self.version_label.setObjectName(u"version_label")
        self.version_label.setEnabled(True)
        self.version_label.setTextFormat(Qt.AutoText)
        self.version_label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.version_label)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"\u5173\u4e8e", None))
        self.image_label.setText(QCoreApplication.translate("Dialog", u"image", None))
        self.version_label.setText(QCoreApplication.translate("Dialog", u"Version", None))
    # retranslateUi

