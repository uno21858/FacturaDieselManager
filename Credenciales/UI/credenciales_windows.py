# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'credenciales_windows.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFormLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QWidget)
import Icons_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(300, 220)
        Form.setMaximumSize(QSize(400, 300))
        font = QFont()
        font.setPointSize(16)
        Form.setFont(font)
        icon = QIcon()
        icon.addFile(u":/Main/credential.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        Form.setWindowIcon(icon)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.pb_Ok = QPushButton(Form)
        self.pb_Ok.setObjectName(u"pb_Ok")
        icon1 = QIcon()
        icon1.addFile(u":/Buttons/flechita.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pb_Ok.setIcon(icon1)

        self.gridLayout.addWidget(self.pb_Ok, 2, 0, 1, 1)

        self.groupBox = QGroupBox(Form)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout = QFormLayout(self.groupBox)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.le_RFC = QLineEdit(self.groupBox)
        self.le_RFC.setObjectName(u"le_RFC")
        font1 = QFont()
        font1.setPointSize(16)
        font1.setStyleStrategy(QFont.PreferDefault)
        self.le_RFC.setFont(font1)
        self.le_RFC.setInputMethodHints(Qt.InputMethodHint.ImhPreferUppercase)
        self.le_RFC.setMaxLength(555)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.le_RFC)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.le_passwd = QLineEdit(self.groupBox)
        self.le_passwd.setObjectName(u"le_passwd")
        self.le_passwd.setEchoMode(QLineEdit.EchoMode.Password)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.le_passwd)


        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 2)

        self.lb_message = QLabel(Form)
        self.lb_message.setObjectName(u"lb_message")

        self.gridLayout.addWidget(self.lb_message, 3, 0, 1, 1)

        self.pb_Cancel = QPushButton(Form)
        self.pb_Cancel.setObjectName(u"pb_Cancel")
        icon2 = QIcon()
        icon2.addFile(u":/Buttons/boton-x.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pb_Cancel.setIcon(icon2)

        self.gridLayout.addWidget(self.pb_Cancel, 2, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 1, 0, 1, 1)

        QWidget.setTabOrder(self.le_RFC, self.le_passwd)
        QWidget.setTabOrder(self.le_passwd, self.pb_Ok)
        QWidget.setTabOrder(self.pb_Ok, self.pb_Cancel)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Credenciales", None))
        self.pb_Ok.setText(QCoreApplication.translate("Form", u"Ok", None))
        self.groupBox.setTitle(QCoreApplication.translate("Form", u"Ingrese RFC y Contrase\u00f1a", None))
        self.label.setText(QCoreApplication.translate("Form", u"RFC:", None))
        self.le_RFC.setText("")
        self.label_2.setText(QCoreApplication.translate("Form", u"Contrase\u00f1a:", None))
        self.lb_message.setText(QCoreApplication.translate("Form", u"Mensaje:", None))
        self.pb_Cancel.setText(QCoreApplication.translate("Form", u"Cancelar", None))
    # retranslateUi

