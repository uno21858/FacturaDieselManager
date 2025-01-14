# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'principal_window.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDateEdit, QDateTimeEdit,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QSpacerItem, QStatusBar,
    QTextEdit, QTreeView, QVBoxLayout, QWidget)
import Icons_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(774, 587)
        MainWindow.setMaximumSize(QSize(780, 600))
        font = QFont()
        font.setPointSize(13)
        MainWindow.setFont(font)
        icon = QIcon()
        icon.addFile(u":/Main/icon.ico", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.lb_facdes = QLabel(self.centralwidget)
        self.lb_facdes.setObjectName(u"lb_facdes")

        self.verticalLayout_2.addWidget(self.lb_facdes, 0, Qt.AlignmentFlag.AlignHCenter)

        self.treeView = QTreeView(self.centralwidget)
        self.treeView.setObjectName(u"treeView")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeView.sizePolicy().hasHeightForWidth())
        self.treeView.setSizePolicy(sizePolicy)
        self.treeView.viewport().setProperty(u"cursor", QCursor(Qt.CursorShape.PointingHandCursor))

        self.verticalLayout_2.addWidget(self.treeView, 0, Qt.AlignmentFlag.AlignLeft)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.btn_download = QPushButton(self.centralwidget)
        self.btn_download.setObjectName(u"btn_download")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btn_download.sizePolicy().hasHeightForWidth())
        self.btn_download.setSizePolicy(sizePolicy1)
        font1 = QFont()
        font1.setPointSize(14)
        self.btn_download.setFont(font1)

        self.verticalLayout_2.addWidget(self.btn_download, 0, Qt.AlignmentFlag.AlignHCenter)

        self.cB_months = QComboBox(self.centralwidget)
        self.cB_months.addItem("")
        self.cB_months.addItem("")
        self.cB_months.addItem("")
        self.cB_months.addItem("")
        self.cB_months.addItem("")
        self.cB_months.addItem("")
        self.cB_months.addItem("")
        self.cB_months.addItem("")
        self.cB_months.addItem("")
        self.cB_months.addItem("")
        self.cB_months.addItem("")
        self.cB_months.addItem("")
        self.cB_months.setObjectName(u"cB_months")

        self.verticalLayout_2.addWidget(self.cB_months)

        self.Dte_year = QDateEdit(self.centralwidget)
        self.Dte_year.setObjectName(u"Dte_year")
        self.Dte_year.setMinimumDate(QDate(2023, 9, 14))
        self.Dte_year.setCurrentSection(QDateTimeEdit.Section.YearSection)

        self.verticalLayout_2.addWidget(self.Dte_year)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.gb_SumadCom = QGroupBox(self.centralwidget)
        self.gb_SumadCom.setObjectName(u"gb_SumadCom")
        self.gb_SumadCom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gridLayout = QGridLayout(self.gb_SumadCom)
        self.gridLayout.setObjectName(u"gridLayout")
        self.line_2 = QFrame(self.gb_SumadCom)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line_2, 7, 0, 1, 2)

        self.line_5 = QFrame(self.gb_SumadCom)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.Shape.HLine)
        self.line_5.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line_5, 9, 0, 1, 2)

        self.lb_fecha = QLabel(self.gb_SumadCom)
        self.lb_fecha.setObjectName(u"lb_fecha")

        self.gridLayout.addWidget(self.lb_fecha, 0, 0, 1, 1)

        self.line_4 = QFrame(self.gb_SumadCom)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.Shape.HLine)
        self.line_4.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line_4, 1, 0, 1, 2)

        self.lb_folio = QLabel(self.gb_SumadCom)
        self.lb_folio.setObjectName(u"lb_folio")

        self.gridLayout.addWidget(self.lb_folio, 2, 0, 1, 1)

        self.line_3 = QFrame(self.gb_SumadCom)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line_3, 3, 0, 1, 2)

        self.lbtxt_sumaPG = QLabel(self.gb_SumadCom)
        self.lbtxt_sumaPG.setObjectName(u"lbtxt_sumaPG")

        self.gridLayout.addWidget(self.lbtxt_sumaPG, 8, 0, 1, 1)

        self.lbtxt_sumaLD = QLabel(self.gb_SumadCom)
        self.lbtxt_sumaLD.setObjectName(u"lbtxt_sumaLD")

        self.gridLayout.addWidget(self.lbtxt_sumaLD, 6, 0, 1, 1)

        self.lbtxt_sumaprecioD = QLabel(self.gb_SumadCom)
        self.lbtxt_sumaprecioD.setObjectName(u"lbtxt_sumaprecioD")

        self.gridLayout.addWidget(self.lbtxt_sumaprecioD, 4, 0, 1, 1)

        self.lb_PriceGas = QLabel(self.gb_SumadCom)
        self.lb_PriceGas.setObjectName(u"lb_PriceGas")

        self.gridLayout.addWidget(self.lb_PriceGas, 8, 1, 1, 1)

        self.lb_PriceDiesel = QLabel(self.gb_SumadCom)
        self.lb_PriceDiesel.setObjectName(u"lb_PriceDiesel")

        self.gridLayout.addWidget(self.lb_PriceDiesel, 4, 1, 1, 1)

        self.lb_LitersDiesel = QLabel(self.gb_SumadCom)
        self.lb_LitersDiesel.setObjectName(u"lb_LitersDiesel")

        self.gridLayout.addWidget(self.lb_LitersDiesel, 6, 1, 1, 1)

        self.lb_fechaEmision = QLabel(self.gb_SumadCom)
        self.lb_fechaEmision.setObjectName(u"lb_fechaEmision")

        self.gridLayout.addWidget(self.lb_fechaEmision, 0, 1, 1, 1)

        self.lb_FolioFactura = QLabel(self.gb_SumadCom)
        self.lb_FolioFactura.setObjectName(u"lb_FolioFactura")

        self.gridLayout.addWidget(self.lb_FolioFactura, 2, 1, 1, 1)

        self.line = QFrame(self.gb_SumadCom)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 5, 0, 1, 2)


        self.verticalLayout_3.addWidget(self.gb_SumadCom)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_2)

        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")

        self.verticalLayout_3.addWidget(self.label)

        self.DispLogs = QTextEdit(self.centralwidget)
        self.DispLogs.setObjectName(u"DispLogs")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.DispLogs.sizePolicy().hasHeightForWidth())
        self.DispLogs.setSizePolicy(sizePolicy2)
        self.DispLogs.viewport().setProperty(u"cursor", QCursor(Qt.CursorShape.WhatsThisCursor))
        self.DispLogs.setReadOnly(True)

        self.verticalLayout_3.addWidget(self.DispLogs)


        self.horizontalLayout.addLayout(self.verticalLayout_3)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 774, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.lb_facdes.setText(QCoreApplication.translate("MainWindow", u"Facturas Descargadas", None))
        self.btn_download.setText(QCoreApplication.translate("MainWindow", u"Descargar Facturas", None))
        self.cB_months.setItemText(0, QCoreApplication.translate("MainWindow", u"Enero", None))
        self.cB_months.setItemText(1, QCoreApplication.translate("MainWindow", u"Febrero", None))
        self.cB_months.setItemText(2, QCoreApplication.translate("MainWindow", u"Marzo", None))
        self.cB_months.setItemText(3, QCoreApplication.translate("MainWindow", u"Abril", None))
        self.cB_months.setItemText(4, QCoreApplication.translate("MainWindow", u"Mayo", None))
        self.cB_months.setItemText(5, QCoreApplication.translate("MainWindow", u"Junio", None))
        self.cB_months.setItemText(6, QCoreApplication.translate("MainWindow", u"Julio", None))
        self.cB_months.setItemText(7, QCoreApplication.translate("MainWindow", u"Agosto", None))
        self.cB_months.setItemText(8, QCoreApplication.translate("MainWindow", u"Septiembre", None))
        self.cB_months.setItemText(9, QCoreApplication.translate("MainWindow", u"Octubre", None))
        self.cB_months.setItemText(10, QCoreApplication.translate("MainWindow", u"Noviembre", None))
        self.cB_months.setItemText(11, QCoreApplication.translate("MainWindow", u"Diciembre", None))

        self.Dte_year.setDisplayFormat(QCoreApplication.translate("MainWindow", u"yyyy", None))
        self.gb_SumadCom.setTitle(QCoreApplication.translate("MainWindow", u"Suma de Combustibles", None))
        self.lb_fecha.setText(QCoreApplication.translate("MainWindow", u"Fecha de la Factura", None))
        self.lb_folio.setText(QCoreApplication.translate("MainWindow", u"Folio: ", None))
        self.lbtxt_sumaPG.setText(QCoreApplication.translate("MainWindow", u"Suma $ Gasolina: ", None))
        self.lbtxt_sumaLD.setText(QCoreApplication.translate("MainWindow", u"Suma L (Litros) Diesel:", None))
        self.lbtxt_sumaprecioD.setText(QCoreApplication.translate("MainWindow", u"Suma $ Diesel: ", None))
        self.lb_PriceGas.setText(QCoreApplication.translate("MainWindow", u"$0.00", None))
        self.lb_PriceDiesel.setText(QCoreApplication.translate("MainWindow", u"$0.00", None))
        self.lb_LitersDiesel.setText(QCoreApplication.translate("MainWindow", u"0.000", None))
        self.lb_fechaEmision.setText(QCoreApplication.translate("MainWindow", u"d/M/AAAA", None))
        self.lb_FolioFactura.setText(QCoreApplication.translate("MainWindow", u"D00000", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Logs:", None))
    # retranslateUi

