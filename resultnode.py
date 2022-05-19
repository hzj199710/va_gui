# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'resultnode.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets
import my_gif
import json
import datetime

class Ui_nodeGifResWidget(object):
    def __init__(self,node_info):
        self.snap_info=node_info
        self.apron=node_info[1]
        self.node=node_info[2]
        self.node_chinese=node_info[3]
        date0=datetime.datetime.combine(node_info[4],datetime.time.min)
        date0+=node_info[5]
        self.date=date0.strftime('%Y/%m/%d')
        str_tmp="日一二三四五六"
        self.week = "星期"+str_tmp[int(date0.strftime('%w'))]
        self.time=date0.strftime('%H:%M:%S')
        fp  = open('./static/setting/config.json', 'r', encoding='utf8')
        config = json.load(fp)
        self.gif_path = config["snap_root_path"]+node_info[6]

    def setupUi(self, nodeGifResWidget):
        nodeGifResWidget.setObjectName("nodeGifResWidget")
        nodeGifResWidget.resize(845, 604)
        nodeGifResWidget.setMinimumSize(QtCore.QSize(0, 0))
        nodeGifResWidget.setMaximumSize(QtCore.QSize(16777215, 16777215))
        nodeGifResWidget.setStyleSheet("")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(nodeGifResWidget)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.nodeGifCardWidget = QtWidgets.QWidget(nodeGifResWidget)
        self.nodeGifCardWidget.setStyleSheet("")
        self.nodeGifCardWidget.setObjectName("nodeGifCardWidget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.nodeGifCardWidget)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.nodeGifLeftSide = QtWidgets.QLabel(self.nodeGifCardWidget)
        self.nodeGifLeftSide.setMinimumSize(QtCore.QSize(0, 0))
        self.nodeGifLeftSide.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.nodeGifLeftSide.setText("")
        self.nodeGifLeftSide.setObjectName("nodeGifLeftSide")
        self.horizontalLayout_2.addWidget(self.nodeGifLeftSide)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setContentsMargins(6, 6, -1, 6)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.nodeGifPlaneNo = QtWidgets.QLabel(self.nodeGifCardWidget)
        self.nodeGifPlaneNo.setMinimumSize(QtCore.QSize(0, 0))
        self.nodeGifPlaneNo.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.nodeGifPlaneNo.setObjectName("nodeGifPlaneNo")
        self.horizontalLayout.addWidget(self.nodeGifPlaneNo)
        self.nodeGifStatusIco = QtWidgets.QLabel(self.nodeGifCardWidget)
        self.nodeGifStatusIco.setMinimumSize(QtCore.QSize(0, 0))
        self.nodeGifStatusIco.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.nodeGifStatusIco.setText("")
        self.nodeGifStatusIco.setObjectName("nodeGifStatusIco")
        self.horizontalLayout.addWidget(self.nodeGifStatusIco)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.nodeGifTime = QtWidgets.QLabel(self.nodeGifCardWidget)
        self.nodeGifTime.setMinimumSize(QtCore.QSize(0, 0))
        self.nodeGifTime.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.nodeGifTime.setObjectName("nodeGifTime")
        self.verticalLayout.addWidget(self.nodeGifTime)
        self.nodeGifName = QtWidgets.QLabel(self.nodeGifCardWidget)
        self.nodeGifName.setMinimumSize(QtCore.QSize(0, 0))
        self.nodeGifName.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.nodeGifName.setObjectName("nodeGifName")
        self.verticalLayout.addWidget(self.nodeGifName)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.nodeGifWeek = QtWidgets.QLabel(self.nodeGifCardWidget)
        self.nodeGifWeek.setMinimumSize(QtCore.QSize(0, 0))
        self.nodeGifWeek.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.nodeGifWeek.setObjectName("nodeGifWeek")
        self.verticalLayout.addWidget(self.nodeGifWeek)
        self.nodeGifDate = QtWidgets.QLabel(self.nodeGifCardWidget)
        self.nodeGifDate.setMinimumSize(QtCore.QSize(0, 0))
        self.nodeGifDate.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.nodeGifDate.setObjectName("nodeGifDate")
        self.verticalLayout.addWidget(self.nodeGifDate)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        # self.nodeGifPic = QtWidgets.QLabel(self.nodeGifCardWidget)
        # mylabel=my_gif.MyLabel(self.gif_path)
        # mylabel.setupUi(self.nodeGifPic)
        self.nodeGifPic = my_gif.MyLabel(self.gif_path,self.nodeGifCardWidget)
        self.nodeGifPic.setMinimumSize(QtCore.QSize(0, 0))
        self.nodeGifPic.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.nodeGifPic.setText("")
        self.nodeGifPic.setObjectName("nodeGifPic")
        self.horizontalLayout_2.addWidget(self.nodeGifPic)
        self.verticalLayout_3.addWidget(self.nodeGifCardWidget)

        self.retranslateUi(nodeGifResWidget)
        QtCore.QMetaObject.connectSlotsByName(nodeGifResWidget)

    def retranslateUi(self, nodeGifResWidget):
        _translate = QtCore.QCoreApplication.translate
        nodeGifResWidget.setWindowTitle(_translate("nodeGifResWidget", "resultNode"))
        self.nodeGifPlaneNo.setText(_translate("nodeGifResWidget", self.apron))
        self.nodeGifTime.setText(_translate("nodeGifResWidget", self.time))
        self.nodeGifName.setText(_translate("nodeGifResWidget", self.node_chinese))
        self.nodeGifWeek.setText(_translate("nodeGifResWidget", self.week))
        self.nodeGifDate.setText(_translate("nodeGifResWidget", self.date))
