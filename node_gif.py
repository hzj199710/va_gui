# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'node_gif.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QMovie
import my_gif

class Ui_Form(object):
    def __init__(self,path):
        self.gif_path=path

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(377, 213)
        self.horizontalLayoutWidget = QtWidgets.QWidget(Form)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(0, 0, 376, 211))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_apron = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_apron.setMinimumSize(QtCore.QSize(72, 0))
        self.label_apron.setMaximumSize(QtCore.QSize(72, 20))
        self.label_apron.setObjectName("label_apron")
        self.verticalLayout.addWidget(self.label_apron)
        self.label_timestamp = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_timestamp.setMinimumSize(QtCore.QSize(72, 0))
        self.label_timestamp.setMaximumSize(QtCore.QSize(72, 20))
        self.label_timestamp.setObjectName("label_timestamp")
        self.verticalLayout.addWidget(self.label_timestamp)
        self.label_node_name = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_node_name.setMinimumSize(QtCore.QSize(72, 0))
        self.label_node_name.setMaximumSize(QtCore.QSize(72, 20))
        self.label_node_name.setObjectName("label_node_name")
        self.verticalLayout.addWidget(self.label_node_name)
        spacerItem = QtWidgets.QSpacerItem(2, 2, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.label_week_day = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_week_day.setMinimumSize(QtCore.QSize(72, 0))
        self.label_week_day.setMaximumSize(QtCore.QSize(72, 20))
        self.label_week_day.setObjectName("label_week_day")
        self.verticalLayout.addWidget(self.label_week_day)
        self.label_date = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_date.setMinimumSize(QtCore.QSize(72, 0))
        self.label_date.setMaximumSize(QtCore.QSize(72, 20))
        self.label_date.setObjectName("label_date")
        self.verticalLayout.addWidget(self.label_date)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.label_gif = my_gif.MyLabel(self.gif_path,self.horizontalLayoutWidget)
        self.label_gif.setMinimumSize(QtCore.QSize(300, 200))
        self.label_gif.setMaximumSize(QtCore.QSize(300, 200))
        self.label_gif.setObjectName("label_gif")
        self.horizontalLayout.addWidget(self.label_gif)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

        self.label_gif.setupUi()

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_apron.setText(_translate("Form", "302"))
        self.label_timestamp.setText(_translate("Form", "12:13"))
        self.label_node_name.setText(_translate("Form", "飞机到达"))
        self.label_week_day.setText(_translate("Form", "星期三"))
        self.label_date.setText(_translate("Form", "2020/07/15"))
        self.label_gif.setText(_translate("Form", "gif"))

