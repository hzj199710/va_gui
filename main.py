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

CORRECT_F = 0
ERROR_F = 1
LOST_F = 2
REPEAT_F = 3
UNEXPECT_F = 4
UNCHECKED_F = 5


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
def mysql_get_snap(conn, apron=None, nodename=None, data_start=None, data_end=None, checked=None):
    sql_where = ''
    if apron != None:
        sql_where += 'apron="%s" ' % apron

    if nodename != None:
        if sql_where != '':
            sql_where += 'AND '
        sql_where += 'node_chinese="%s" ' % nodename

    if data_start != None:
        if sql_where != '':
            sql_where += 'AND '
        sql_where += 'date >= "%s" ' % (data_start.strftime("%Y-%m-%d"))

    if data_end != None:
        if sql_where != '':
            sql_where += 'AND '
        sql_where += 'date <= "%s" ' % (data_end.strftime("%Y-%m-%d"))

    if checked != 0:
        if sql_where != '':
            sql_where += 'AND '
        if checked == 6:
            sql_where += ' (checked is null or checked = 5) '
        else:
            sql_where += ' checked = %s'%(checked-1)
    if sql_where != '':
        sql_where = 'where ' + sql_where

    sql = 'SELECT * FROM node_view %s ORDER BY `datetime` ASC, `id` ASC;' % (sql_where)
    result = pd.read_sql(sql, conn)
    return result


def get_chineseNode(conn):
    sql = 'SELECT chinese FROM node_name;'
    result = pd.read_sql(sql, conn)
    return result

def get_position(conn):
    sql = 'SELECT distinct apron FROM node_event;'
    result = pd.read_sql(sql, conn)
    return result


# 更新数据
def mysql_update_data(conn, data_list):
    cursor = conn.cursor()
    for data in data_list:
        sql = 'UPDATE node_event SET checked=%s WHERE id=%s' % (data[1], data[0])
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
    def __init__(self, parent=None, conn=None):
        QDialog.__init__(self, parent=parent)
        self.result = None
        self.conn = conn
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
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowCloseButtonHint)

        self.btnVerifyQuery.clicked.connect(self.on_query)
        self.btnOut.clicked.connect(self.save_data)

        # 设置table只能行选择，且不能编辑，设置列宽
        self.verifytableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.verifytableWidget.setEditTriggers(QTableView.NoEditTriggers)
        self.verifytableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verifytableWidget.verticalHeader().setVisible(False)
        self.verifytableWidget.setColumnWidth(0, 60)
        self.verifytableWidget.setColumnWidth(1, 40)
        self.verifytableWidget.setColumnWidth(2, 150)
        self.verifytableWidget.setColumnWidth(3, 80)
        self.verifytableWidget.setColumnWidth(4, 160)
        self.verifytableWidget.setColumnWidth(5, 100)
        self.verifytableWidget.clicked.connect(self.table_change)

        # 设置节点选择器
        item = self.verifyNodeCombox
        _translate = QtCore.QCoreApplication.translate
        node_name = np.array(get_chineseNode(self.conn)).tolist()
        item.addItem("")
        item.setItemText(0, _translate("verify", '全部'))
        for index in range(len(node_name)):
            item.addItem("")
            item.setItemText(index+1, _translate("verify", node_name[index][0]))

        # 设置机位选择器
        item = self.verifyPlaneNoCombox
        _translate = QtCore.QCoreApplication.translate
        node_name = np.array(get_position(self.conn)).tolist()
        item.addItem("")
        item.setItemText(0, _translate("verify", '全部'))
        for index in range(len(node_name)):
            item.addItem("")
            item.setItemText(index + 1, _translate("verify", node_name[index][0]))


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


        # 生成统计报告
        self.btnStatistics.clicked.connect(self.createStatistics)

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
                comboBox = self.verifytableWidget.cellWidget(row, 5)
                currentIndex = comboBox.currentIndex()

                comboBox.setCurrentIndex((currentIndex+1)%6)

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
        temp = self.result.iloc[self.pageIndex * 20 + row, :]
        node = np.array(temp).tolist()
        node[4] = node[8].date()
        res1 = resultnode.Ui_nodeGifResWidget(node)
        wgt = QtWidgets.QWidget()
        res1.setupUi(wgt)
        self.verticalLayout_4.addWidget(wgt)

    # 实时更新
    def on_save(self):
        row = self.verifytableWidget.selectedItems()[0].row()
        self.result.iloc[row + self.pageIndex*20, 7] = self.verifytableWidget.cellWidget(row, 5).currentIndex()
        data_list_n = [[self.result.iloc[row + self.pageIndex*20, 0], self.result.iloc[row + self.pageIndex*20, 7]]]
        mysql_update_data(self.conn, data_list_n)

    def on_query(self):
        apron = self.verifyPlaneNoCombox.itemText(self.verifyPlaneNoCombox.currentIndex())
        if apron == "全部":
            apron = None
        node = self.verifyNodeCombox.itemText(self.verifyNodeCombox.currentIndex())
        if node == "全部":
            node = None
        data_start = self.verifyBegindateEdit.date().toPyDate()
        data_end = self.verifyEnddateEdit.date().toPyDate()
        checked = self.verifyStatusCombox.currentIndex()
        self.result = mysql_get_snap(self.conn, apron=apron, nodename=node, checked=checked, data_start=data_start, data_end=data_end)
        if self.result.shape[0] != 0:
            self.result['checked'] = self.result['checked'].fillna(UNCHECKED_F).astype('int')
            self.result['date'] = self.result.apply(lambda x: x['datetime'].strftime('%Y-%m-%d %H:%M:%S'), axis=1)
            self.result['date_day'] = self.result.apply(lambda x: x['datetime'].strftime('%Y-%m-%d'), axis=1)
            self.pageIndex = 0
            self.pageIndexLast = int((self.result.shape[0]-1) / 20)
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
        for i in range(20):
            if self.pageIndex * 20 + i > self.result.shape[0] - 1:
                break
            node = self.result.iloc[self.pageIndex * 20 + i, :]
            ID = str(node["id"])
            apron = node["apron"]
            date = node["date"]
            node_chinese = node["node_chinese"]
            snap_addr = node["snap_addr"]
            checked = node["checked"]
            if np.isnan(checked):
                checked = UNCHECKED_F
            row = table.rowCount()
            table.insertRow(row)
            item = QTableWidgetItem(ID)
            table.setItem(row, 0, item)
            item = QTableWidgetItem(apron)
            table.setItem(row, 1, item)
            item = QTableWidgetItem(date)
            table.setItem(row, 2, item)
            item = QTableWidgetItem(node_chinese)
            table.setItem(row, 3, item)
            item = QTableWidgetItem(snap_addr)
            table.setItem(row, 4, item)

            item = QComboBox()
            _translate = QtCore.QCoreApplication.translate
            item.setObjectName(ID)
            item.addItem("")
            item.addItem("")
            item.addItem("")
            item.addItem("")
            item.addItem("")
            item.addItem("")
            item.setItemText(CORRECT_F, _translate("verify", "正确"))
            item.setItemText(ERROR_F, _translate("verify", "错误"))
            item.setItemText(LOST_F, _translate("verify", "遗漏"))
            item.setItemText(REPEAT_F, _translate("verify", "重复上报"))
            item.setItemText(UNEXPECT_F, _translate("verify", "无计划航班"))
            item.setItemText(UNCHECKED_F, _translate("verify", "未审核"))
            item.setCurrentIndex(checked)
            item.currentIndexChanged.connect(self.on_save)
            table.setCellWidget(row, 5, item)
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
            sql_cfg = config["mysql"]
            try:
                self.conn = pymysql.connect(host=sql_cfg['ip'], port=sql_cfg["port"], user=sql_cfg["user"],
                                   passwd=sql_cfg["passwd"], db=sql_cfg["db"])
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
        self.main_ui = MyVerify(conn=self.conn)
        with open('./static/setting/style.qss', 'r', encoding='utf-8') as f:
            tmp = f.read()
            self.main_ui.setStyleSheet(tmp)
        self.login.destroy()
        self.main_ui.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mgr = Manager()
    sys.exit(app.exec_())
