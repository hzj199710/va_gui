import sys
from PyQt5.QtWidgets import QApplication, QDialog, \
    QTableWidgetItem, QComboBox, \
    QAbstractItemView, QTableView, QLabel, QFileDialog, QShortcut, QMessageBox, QWidget, QLayout

from PyQt5.Qt import pyqtSignal, QThread, QFont, QDate, QKeySequence
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from login import Ui_Login

from verify import Ui_verify
from statisticsTable import *
import json
import pymysql
import resultnode
import pandas as pd
import numpy as np
from astral import LocationInfo
import os

page_rows = 25

level_dir = {
    0: '低',
    1: '中',
    2: '高'
}

type_dir = {
    0: '反光背心',
    1: '人员密度',
    2: '区域入侵'
}

status_dir = {
    0: '未处理',
    1: '已处理',
    2: '误报',
    3: '重复上报'
}

# 判断(南宁)该时间（dateTime）下是否是白天
def isDay(dateTime):
    date = dateTime.date()
    time = dateTime.time()
    with open('./static/setting/placePosition.json', 'r', encoding='utf8') as fp:
        info = json.load(fp)['nanning']
        nanning = LocationInfo('Nanning', info['country'], info['timezone'], info['latitude'], info['longitude'])
        from astral.sun import sun
        s = sun(nanning.observer, date=date, tzinfo=nanning.timezone)
        sunrise = s['sunrise'].time()
        sunset = s['sunset'].time()
        if sunrise.__le__(time) and sunset.__ge__(time):
            return True
        else:
            return False

import time
# 查询数据
def mysql_get_snap(conn, view, source=None, type=None, level=None, data_start=None, data_end=None, status=None):
    sql_where = ''
    if source != None:
        sql_where += 'camera_name="%s" ' % source

    if type != None:
        if sql_where != '':
            sql_where += 'AND '
        sql_where += 'type="%s" ' % type

    if level != None:
        if sql_where != '':
            sql_where += 'AND '
        sql_where += 'level="%s" ' % level

    if data_start != None:
        if sql_where != '':
            sql_where += 'AND '
        sql_where += 'timestamp >= "%s" ' % (data_start.strftime("%Y-%m-%d"))

    if data_end != None:
        if sql_where != '':
            sql_where += 'AND '
        sql_where += 'timestamp <= "%s" ' % (data_end.strftime("%Y-%m-%d"))

    if status != None:
        if sql_where != '':
            sql_where += 'AND '
        if status == 0:
            sql_where += ' (status is null or status = 0) '
        else:
            sql_where += 'status="%s" ' % status

    if sql_where != '':
        sql_where = 'where ' + sql_where

    sql = 'SELECT * FROM %s %s ORDER BY `timestamp` ASC, `id` ASC;' % (view, sql_where)
    print(sql)
    result = pd.read_sql_query(sql, conn)
    return result


def get_source(conn):
    pass


def get_chineseNode(conn):
    sql = 'SELECT chinese FROM node_name;'
    result = pd.read_sql(sql, conn)
    return result

def get_position(conn, view):
    sql = 'SELECT distinct apron FROM %s;'%(view)
    result = pd.read_sql(sql, conn)
    return result


# 更新数据
def mysql_update_data(conn, view, data_list):
    cursor = conn.cursor()
    for data in data_list:
        sql = 'UPDATE %s SET status=%s WHERE id=%s' % (view, data[1], data[0])
        cursor.execute(sql)
    conn.commit()


class Thread_1(QThread):
    _signal = pyqtSignal()

    def __init__(self, data, staticstisTable):
        super().__init__()
        self.result = data
        self.staticstisTable = staticstisTable

    # 根据condition生成统计表
    def generate_dd(self, result, condition, decimal=3):
        result_total = result.groupby([condition, 'checked']).size().reset_index()
        result_error = result_total[result_total['checked'] == 1].loc[:, [condition, 0]]
        result_right = result_total[result_total['checked'] == 0].loc[:, [condition, 0]]
        result_error.columns = [condition, 'error_count']
        result_right.columns = [condition, 'right_count']

        print(1)
        dd = pd.merge(result_right, result_error, how='outer', on=condition)
        dd = dd[[condition, 'right_count', 'error_count']]
        dd = dd.fillna(0)
        dd['error_count'] = dd['error_count'].astype('int')
        dd['right_count'] = dd['right_count'].astype('int')
        print(dd)
        total_count, total_error = dd['right_count'].sum(), dd['error_count'].sum()
        dd.loc['new'] = ['综合', total_count, total_error]

        dd['accuracy'] = dd.apply(lambda x: round(x['right_count'] / (x['right_count'] + x['error_count']), decimal),
                                  axis=1)
        print(1)
        # 将准确数量改为总数量
        dd['right_count'] = dd.apply(lambda x: x['right_count'] + x['error_count'], axis=1)

        dd['error_count'] = dd['error_count'].astype('int')
        dd['right_count'] = dd['right_count'].astype('int')
        print(1)
        return dd

    def run(self):
        decimal = 3
        self.tablesContain = []
        with open('./static/setting/style.qss', 'r', encoding='utf-8') as f:
            tmp = f.read()
            self.staticstisTable.setStyleSheet(tmp)

        # 按节点统计
        result = self.result
        dd = self.generate_dd(result, 'node_chinese')
        dd.columns = ['节点名', '节点数', '错误数', '准确率']
        self.createTables(Mydate=dd, table=self.staticstisTable.tableByNode)
        self.staticstisTable.tableByNode.setEditTriggers(QTableView.NoEditTriggers)
        self.tablesContain.append(['按节点统计', dd])

        # 按天统计
        dd = self.generate_dd(result, 'date_day')
        dd.columns = ['时期', '节点数', '错误数', '准确率']
        self.createTables(Mydate=dd, table=self.staticstisTable.tableByDate)
        self.staticstisTable.tableByDate.setEditTriggers(QTableView.NoEditTriggers)
        self.tablesContain.append(['按天统计', dd])


        # 按机位统计
        dd = self.generate_dd(result, 'apron')
        dd.columns = ['机位', '节点数', '错误数', '准确率']
        self.createTables(Mydate=dd, table=self.staticstisTable.tableByPosition)
        self.staticstisTable.tableByPosition.setEditTriggers(QTableView.NoEditTriggers)
        self.tablesContain.append(['按机位统计', dd])

        # 按昼夜分类
        result['isDay'] = result.apply(lambda x: isDay(x['datetime']), axis=1)
        result_List = [result[result['isDay'] == True], result[result['isDay'] == False]]
        for i in range(2):
            if result_List[i].shape[0] != 0:
                dd = self.generate_dd(result_List[i], 'node_chinese')

                dd.columns = ['节点名', '节点数', '错误数', '准确率']
                self.createTables(Mydate=dd, table=self.staticstisTable.tableByTime, position=[2, i * 4])
                self.staticstisTable.tableByTime.setEditTriggers(QTableView.NoEditTriggers)
                if i == 0:
                    self.tablesContain.append(['白天统计', dd])
                else:
                    self.tablesContain.append(['晚上统计', dd])

        self.staticstisTable.signal.connect(self.slot_generateExcel)
        self._signal.emit()

    def createTables(self, Mydate, table, position=None):
        if position == None:
            position = [0, 0]
        if position[1] == 0:
            table.setRowCount(position[0])
        for row in range(Mydate.shape[0]):
            if position[1] == 0:
                table.insertRow(row + position[0])
            for col in range(Mydate.shape[1]):
                item = QTableWidgetItem(str(Mydate.iloc[row, col]))
                table.setItem(row + position[0], col + position[1], item)

    def slot_generateExcel(self):
        global save_path
        _translate = QtCore.QCoreApplication.translate
        save_path, fileType = QFileDialog.getSaveFileName(None, "文件保存", "./", 'Excel(*.xlsx)')

        if save_path != '':
            writer = pd.ExcelWriter(save_path, mode='w', engine="openpyxl")
            for item in self.tablesContain:
                item[1].to_excel(writer, sheet_name=item[0], index=False)
            writer.save()
            writer.close()


class MyVerify(QDialog, Ui_verify):
    def __init__(self, parent=None, conn=None, view=None):
        QDialog.__init__(self, parent=parent)
        self.result = None
        self.conn = conn
        self.view = view
        self.is_update = False
        self.update_id_flag = None
        self.setupUi(self)

        # 设置热键
        QShortcut(QKeySequence("space"), self, self.changeState)
        QShortcut(QKeySequence("up"), self, self.chooseUp)
        QShortcut(QKeySequence("down"), self, self.chooseDown)

    def setupUi(self, MainWindow):
        Ui_verify.setupUi(self, MainWindow)
        self.setWindowIcon(QIcon('./static/res/飞机.png'))

        # 界面设置
        self.setWindowTitle('机位分析核验程序')
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMaximizeButtonHint)


        # 设置table只能行选择，且不能编辑，设置列宽
        self.verifytableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.verifytableWidget.setEditTriggers(QTableView.NoEditTriggers)
        self.verifytableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verifytableWidget.verticalHeader().setVisible(False)
        self.verifytableWidget.setColumnWidth(0, 100)
        self.verifytableWidget.setColumnWidth(1, 140)
        self.verifytableWidget.setColumnWidth(2, 150)
        self.verifytableWidget.setColumnWidth(3, 140)
        self.verifytableWidget.setColumnWidth(4, 190)
        self.verifytableWidget.setColumnWidth(5, 140)
        self.verifytableWidget.setColumnWidth(6, 110)
        self.verifytableWidget.setColumnWidth(7, 130)
        self.verifytableWidget.clicked.connect(self.table_change)

        # 设置资源选择器
        item = self.verifySourceCombox
        _translate = QtCore.QCoreApplication.translate
        source_name = np.array(get_source(self.conn)).tolist()
        item.addItem("")
        item.setItemText(0, _translate("verify", '全部'))
        # for index in range(len(source_name)):
        #     item.addItem("")
        #     item.setItemText(index+1, _translate("verify", source_name[index][0]))

        # 设置时间编辑器
        self.verifyBegindateEdit.setDate(QDate.fromString("2020-08-03", 'yyyy-MM-dd'))
        self.verifyEnddateEdit.setDate(QDate.currentDate())

        # 翻页设置
        self.pageIndex = 0
        self.pageIndexLast = 0
        self.btnHomePage.clicked.connect(lambda: self.goToPage(0))
        self.btnLastPage.clicked.connect(lambda: self.goToPage(self.pageIndexLast))
        self.btnBeforePage.clicked.connect(lambda: self.goToPage(self.pageIndex - 1))
        self.btnBeforePage.setShortcut('left')
        self.btnAfterPage.clicked.connect(lambda: self.goToPage(self.pageIndex + 1))
        self.btnAfterPage.setShortcut('right')


        # 按钮连接功能
        self.btnQuery.clicked.connect(self.on_query)
        self.btnReset.clicked.connect(self.on_reset)
        self.btnUpdate.clicked.connect(self.on_update)

        self.timer_1 = QtCore.QTimer(self)
        self.timer_1.timeout.connect(self.update_timer)

    def closeEvent(self, event):
        sys.exit(app.exec_())

    def createStatistics(self):
        if self.result is None or self.result.shape[0] == 0:
            self.msg = QDialog()
            self.msg.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
            self.msg.setWindowTitle('错误')
            self.msg.setWindowIcon(QIcon('./static/res/错误.png'))
            self.msg.resize(300, 250)

            self.msg.lbl = QLabel(u'当前没有查询数据，请先获取数据！！！', self.msg)
            self.msg.lbl.move(25, 100)
            self.msg.lbl.setStyleSheet(
                "font-family: 微软雅黑;\n"
                "font-size: 14px;\n"
                "color: #B9DAFF;\n"
            )

            self.msg.setStyleSheet("background: #182B51;\n")
            self.msg.show()
        else:
            self.itdd = QDialog()
            self.itdd.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
            self.itdd.setWindowTitle('请等待')
            self.itdd.resize(300, 300)
            self.itdd.setStyleSheet("background: #182B51;")
            self.itdd.lbl = QLabel(u'请等待......', self.itdd)
            self.itdd.lbl.move(50, 100)
            self.itdd.lbl.setFont(QFont("Timers", 20))
            self.itdd.lbl.setStyleSheet('color: white;')
            self.itdd.show()

            self.btnStatistics.setEnabled(False)
            self.staticstisTable = MyStatisticsTable()

            self.thread_1 = Thread_1(self.result, self.staticstisTable)
            self.thread_1.start()
            self.thread_1._signal.connect(self.setBtn)

    def save_data(self):
        if self.result is not None and self.result.shape[0] > 0:
            global save_path
            temp = self.result.loc[:, ['id', 'apron', 'node_chinese', 'date', 'snap_addr', 'checked']]
            _translate = QtCore.QCoreApplication.translate
            save_path, fileType = QFileDialog.getSaveFileName(None, "文件保存", "./", 'Excel(*.xlsx)')

            if save_path != '':
                writer = pd.ExcelWriter(save_path, mode='w', engine="openpyxl")
                temp.to_excel(writer, sheet_name='result', index=False)
                writer.save()
                writer.close()
        else:
            self.msg = QDialog()
            self.msg.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
            self.msg.setWindowIcon(QIcon('./static/res/错误.png'))
            self.msg.setWindowTitle('错误')
            self.msg.resize(300, 250)

            self.msg.lbl = QLabel(u'无数据需要保存', self.msg)
            self.msg.lbl.move(100, 100)
            self.msg.lbl.setStyleSheet(
                "font-family: 微软雅黑;\n"
                "font-size: 14px;\n"
                "color: #B9DAFF;\n"
            )

            self.msg.setStyleSheet("background: #182B51;\n")
            self.msg.show()

    def changeState(self):
        if self.verifytableWidget.rowCount() != 0:
            item = self.verifytableWidget.selectedItems()
            if len(item) != 0:
                row = item[0].row()
                comboBox = self.verifytableWidget.cellWidget(row, 7)
                currentIndex = comboBox.currentIndex()

                comboBox.setCurrentIndex((currentIndex+1)%4)

    def chooseUp(self):
        if self.verifytableWidget.rowCount() != 0:
            item = self.verifytableWidget.selectedItems()
            if len(item) != 0:
                row = item[0].row() - 1
                if row >= 0:
                    self.verifytableWidget.selectRow(row)
                    self.showImg(row)

    def chooseDown(self):
        if self.verifytableWidget.rowCount() != 0:
            item = self.verifytableWidget.selectedItems()
            if len(item) != 0:
                if item[0].row() < self.verifytableWidget.rowCount() - 1:
                    row = item[0].row() + 1
                    self.verifytableWidget.selectRow(row)
                    self.showImg(row)

    def table_change(self):
        if self.verifytableWidget.rowCount() != 0:
            item = self.verifytableWidget.selectedItems()
            if len(item) != 0:
                if item[0].row() <= self.verifytableWidget.rowCount() - 1:
                    row = item[0].row()
                    self.showImg(row)

    def setBtn(self):
        self.btnStatistics.setEnabled(True)
        self.itdd.destroy()
        self.staticstisTable.show()

    def goToPage(self, num):
        if num >= 0 and num <= self.pageIndexLast:
            self.pageIndex = num
            self.createTable()

    def showImg(self, row):
        for i in range(self.verticalLayout_4.count()):
            self.verticalLayout_4.itemAt(i).widget().deleteLater()
        temp = self.result.iloc[self.pageIndex * page_rows + row, :]
        node_t = []
        node_t.append(temp['id'])
        node_t.append(temp['camera_name'])
        node_t.append(temp['location'])
        node_t.append(type_dir[temp['type']])
        node_t.append(temp['timestamp'])
        node_t.append(temp['snap'])

        res1 = resultnode.Ui_nodeGifResWidget(node_t)
        wgt = QtWidgets.QWidget()
        res1.setupUi(wgt)
        self.verticalLayout_4.addWidget(wgt)
        self.verticalLayout_4.setSizeConstraint(0)
        # pass

    def update_timer(self):
        if self.is_update:
            self.result = mysql_get_snap(self.conn, self.view)
            if self.result.shape[0] != 0:
                self.result['status'] = self.result['status'].fillna(0).astype('int')
                self.result['date'] = self.result.apply(lambda x: x['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), axis=1)
                self.result['date_day'] = self.result.apply(lambda x: x['timestamp'].strftime('%Y-%m-%d'), axis=1)
                self.result['date_time'] = self.result.apply(lambda x: x['timestamp'].strftime('%H:%M:%S'), axis=1)

                self.result = self.result.iloc[::-1]

                if self.result.shape[0] > page_rows:
                    self.result = self.result.iloc[:page_rows, :]

                if self.result.iloc[0, 0] != self.update_id_flag:
                    self.update_id_flag = self.result.iloc[0, 0]
                    self.pageIndex = 0
                    self.pageIndexLast = 0
                    self.lblTotalPage.setText('共1页')
                    print(self.result)
                    self.createTable()

    def on_reset(self):
        self.verifyHandleCombox.setCurrentIndex(0)
        self.verifyLevelCombox.setCurrentIndex(0)
        self.verifyTypeCombox.setCurrentIndex(0)
        self.verifySourceCombox.setCurrentIndex(0)
        self.verifyBegindateEdit.setDate(QDate.fromString("2020-08-03", 'yyyy-MM-dd'))
        self.verifyEnddateEdit.setDate(QDate.currentDate())

    def on_update(self):
        if not self.is_update:
            self.is_update = True
            self.on_reset()
            self.btnQuery.setEnabled(False)
            self.btnReset.setEnabled(False)
            self.btnBeforePage.setEnabled(False)
            self.btnLastPage.setEnabled(False)
            self.btnHomePage.setEnabled(False)
            self.btnAfterPage.setEnabled(False)
            self.verifySourceCombox.setEnabled(False)
            self.verifyTypeCombox.setEnabled(False)
            self.verifyLevelCombox.setEnabled(False)
            self.verifyHandleCombox.setEnabled(False)
            self.verifyBegindateEdit.setEnabled(False)
            self.verifyEnddateEdit.setEnabled(False)
            self.timer_1.start(1000)

        else:
            self.timer_1.stop()
            self.result = None
            self.createTable()
            self.is_update = False
            self.update_id_flag = None
            self.btnQuery.setEnabled(True)
            self.btnReset.setEnabled(True)
            self.btnBeforePage.setEnabled(True)
            self.btnLastPage.setEnabled(True)
            self.btnHomePage.setEnabled(True)
            self.btnAfterPage.setEnabled(True)
            self.verifySourceCombox.setEnabled(True)
            self.verifyTypeCombox.setEnabled(True)
            self.verifyLevelCombox.setEnabled(True)
            self.verifyHandleCombox.setEnabled(True)
            self.verifyBegindateEdit.setEnabled(True)
            self.verifyEnddateEdit.setEnabled(True)

    # 实时更新
    def on_save(self):
        row = self.verifytableWidget.selectedItems()[0].row()
        self.result.iloc[row + self.pageIndex*page_rows, 7] = self.verifytableWidget.cellWidget(row, 7).currentIndex()
        print(self.result.iloc[row + self.pageIndex*page_rows, :])
        data_list_n = [[self.result.iloc[row + self.pageIndex*page_rows, 0], self.result.iloc[row + self.pageIndex*page_rows, 7]]]
        mysql_update_data(self.conn, self.view, data_list_n)

    def on_query(self):
        source = self.verifySourceCombox.itemText(self.verifySourceCombox.currentIndex())
        if source == "全部":
            source = None
        type = self.verifyTypeCombox.currentIndex() - 1
        if type == -1:
            type = None
        level = self.verifyLevelCombox.currentIndex() - 1
        if level == -1:
            level = None
        status = self.verifyHandleCombox.currentIndex() - 1
        if status == -1:
            status = None

        data_start = self.verifyBegindateEdit.date().toPyDate()
        data_end = self.verifyEnddateEdit.date().toPyDate()

        # self.result = mysql_get_snap(self.conn, self.view, source=source, type=type, level=level, status=status)#, data_start=data_start, data_end=data_end)
        self.result = mysql_get_snap(self.conn, self.view, source=source, type=type, level=level, status=status,
                                     data_start=data_start, data_end=data_end)
        print(self.result)
        if self.result.shape[0] != 0:
            self.result['status'] = self.result['status'].fillna(0).astype('int')
            self.result['date'] = self.result.apply(lambda x: x['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), axis=1)
            self.result['date_day'] = self.result.apply(lambda x: x['timestamp'].strftime('%Y-%m-%d'), axis=1)
            self.result['date_time'] = self.result.apply(lambda x: x['timestamp'].strftime('%H:%M:%S'), axis=1)
            self.pageIndex = 0
            self.pageIndexLast = int((self.result.shape[0]-1) / page_rows)
            self.lblTotalPage.setText('共%d页' % (self.pageIndexLast+1))
            self.createTable()
        else:
            self.verifytableWidget.setRowCount(0)
            self.msg = QDialog()
            self.msg.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
            self.msg.setWindowTitle('错误')
            self.msg.setWindowIcon(QIcon('./static/res/错误.png'))
            self.msg.resize(300, 250)

            self.msg.lbl = QLabel(u'查询不到数据，请重新选择！！！', self.msg)
            self.msg.lbl.move(25, 100)
            self.msg.lbl.setStyleSheet(
                "font-family: 微软雅黑;\n"
                "font-size: 14px;\n"
                "color: #B9DAFF;\n"
            )

            self.msg.setStyleSheet("background: #182B51;\n")
            self.msg.show()

    def createTable(self):
        table = self.verifytableWidget
        table.setRowCount(0)
        self.lblPageNum.setText(str(self.pageIndex+1))
        if self.result is None:
            return
        for i in range(page_rows):
            if self.pageIndex * page_rows + i > self.result.shape[0] - 1:
                break
            node = self.result.iloc[self.pageIndex * page_rows + i, :]
            ID = str(node["id"])
            date_time = node['date_time']
            date_day = node['date_day']
            location = node['location']
            source = node['camera_name']
            type = type_dir[node['type']]
            level = level_dir[node['level']]
            status = node['status']

            row = table.rowCount()
            table.insertRow(row)
            item = QTableWidgetItem(ID)
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            table.setItem(row, 0, item)
            item = QTableWidgetItem(date_day)
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            table.setItem(row, 1, item)
            item = QTableWidgetItem(date_time)
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            table.setItem(row, 2, item)
            item = QTableWidgetItem(location)
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            table.setItem(row, 3, item)
            item = QTableWidgetItem(source)
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            table.setItem(row, 4, item)
            item = QTableWidgetItem(type)
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            table.setItem(row, 5, item)
            item = QTableWidgetItem(level)
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            table.setItem(row, 6, item)

            item = QComboBox()
            _translate = QtCore.QCoreApplication.translate
            item.setObjectName(ID)
            item.addItem("")
            item.addItem("")
            item.addItem("")
            item.addItem("")
            for ele in range(4):
                item.setItemText(ele, _translate("verify", status_dir[ele]))
            item.setCurrentIndex(status)
            item.currentIndexChanged.connect(self.on_save)
            table.setCellWidget(row, 7, item)
        self.verifytableWidget.selectRow(0)
        self.showImg(0)


class MyStatisticsTable(Ui_statisticsTable, QDialog):
    signal = pyqtSignal()

    def __init__(self):
        super(QDialog, self).__init__()
        self.setupUi(self)

    def setupUi(self, statisticsTable):
        Ui_statisticsTable.setupUi(self, statisticsTable)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle('核验结果')
        self.tableByTime.setSpan(0, 0, 1, 4)
        self.tableByTime.setSpan(0, 4, 1, 4)
        self.btnSave.clicked.connect(self.save)
        self.btnCancel.clicked.connect(self.cancel)

    def save(self):
        self.signal.emit()
        self.destroy()

    def cancel(self):
        self.destroy()


def mysql_get(conn, table, query=None):
    sql_where = ''
    if query != None:
        sql_where += " where "
        for key in query:
            sql_where += '%s="%s" AND ' %(key, query[key])
        sql_where = sql_where[:-4]

    sql = 'SELECT * FROM %s %s'%(table, sql_where)
    result = pd.read_sql(sql, conn)
    print('数据读取成功')
    return result


class Login(Ui_Login, QWidget):
    siginal_login = pyqtSignal(str)

    def __init__(self, parent=None, conn= None):
        QWidget.__init__(self, parent=parent)
        self.conn = conn
        self.setupUi(self)

    def setupUi(self, Login_t):
        Ui_Login.setupUi(self, Login_t)
        self.setWindowTitle('登录')
        self.setWindowIcon(QIcon('./static/res/飞机.png'))

        self.label_img.setPixmap(QtGui.QPixmap("./static/res/用户管理.png"))

        self.pushButton_login.setShortcut('return')
        self.pushButton_login.clicked.connect(self.login_in)


    def login_in(self):
        name = self.lineEdit_name.text()
        passwd = self.lineEdit_password.text()
        table = "user"
        query = {"user_name": name, "passwd": passwd}
        result = mysql_get(self.conn, table, query=query)
        if result.shape[0] >= 1:
            self.siginal_login.emit('dd')
        else:
            self.itdd = QDialog()
            self.itdd.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
            self.itdd.setWindowTitle('错误')
            self.itdd.setWindowIcon(QIcon('./static/res/错误.png'))
            self.itdd.resize(300, 250)

            self.itdd.lbl = QLabel(u'用户名或者密码错误，请重新输入！！！', self.itdd)
            self.itdd.lbl.move(25, 100)
            self.itdd.lbl.setStyleSheet(
                                        "font-family: 微软雅黑;\n"
                                        "font-size: 14px;\n"
                                        "color: #B9DAFF;\n"
            )

            self.itdd.setStyleSheet("background: #182B51;\n")
            self.itdd.show()


class Manager:
    def __init__(self):
        self.conn = None
        with open('./static/setting/config.json', 'r', encoding='utf8')as fp:
            config = json.load(fp)
            os.system('net use Z: %s %s /user:%s' % (config["snap_root_path"], config["remote_passwd"], config["remote_user"]))
            sql_cfg = config["mysql"]
            try:
                self.conn = pymysql.connect(host=sql_cfg['ip'], port=sql_cfg["port"], user=sql_cfg["user"],
                                   passwd=sql_cfg["passwd"], db=sql_cfg["db"], autocommit=True)
                self.view = sql_cfg["view"]
                self.login = Login(conn=self.conn)
                with open('./static/setting/style.qss', 'r', encoding='utf-8') as f:
                    tmp = f.read()
                    self.login.setStyleSheet(tmp)
                self.login.show()
                self.setIt()
            except:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText('无法连接数据库，请填好配置信息')
                msg.exec()
                sys.exit()

    def __del__(self):
        if self.conn is not None:
            self.conn.close()

    def setIt(self):
        self.login.siginal_login.connect(self.move2main)

    def move2main(self, msg):
        self.login.setWindowTitle('登录中...')
        self.main_ui = MyVerify(conn=self.conn, view=self.view)
        with open('./static/setting/style.qss', 'r', encoding='utf-8') as f:
            tmp = f.read()
            self.main_ui.setStyleSheet(tmp)
        self.login.destroy()
        self.main_ui.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mgr = Manager()
    sys.exit(app.exec_())
