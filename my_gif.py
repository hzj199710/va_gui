# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QMovie
import os

class MyLabel(QtWidgets.QLabel):
    def __init__(self,path, parent=None):
        # super.__init__(self, parent)
        QtWidgets.QLabel.__init__(self, parent)
        self.gif_path=path
        self.setMouseTracking(True)
        self.setupUi()

    def setupUi(self,parent=None):
        self.gif = QMovie(self.gif_path)
        self.gif.setScaledSize(QSize(600, 400))
        self.setMovie(self.gif)
        self.gif.start()
        # self.gif.jumpToFrame(self.gif.frameCount()-1)
        # self.gif.setPaused(True)


    def enterEvent(self, mE):
        self.gif.start()


    def mouseDoubleClickEvent(self, e):

        ll = self.gif_path.split('/')
        self.gif_path = '\\'.join(ll)
        os.system(self.gif_path)
        print("double clicked")

    # def leaveEvent(self, mE):
        # # self.gif.stop()
        # self.gif.setPaused(True)
        # self.gif.jumpToFrame(self.gif.frameCount()-1)
