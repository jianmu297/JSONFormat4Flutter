#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Filename :   formater.py
# @Date     :   18-1-26 下午5:48
# @Author   :   DebuggerX
from functools import partial

from mainwindow import *
import json

# 定义显示的json格式化字符串的缩进量为4个空格
indent = '    '

# 临时存储
last_list_com_box = None


# 验证json字符串是否合法
def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True


# 传入未格式化的单行json字符串，返回指定缩进的多行json字符串
def jformat(inp):
    obj = json.loads(inp)
    outp = json.dumps(obj, skipkeys=False, ensure_ascii=False, check_circular=True, allow_nan=True, cls=None, indent='  ', separators=None,
                      default=None, sort_keys=True)
    return outp


def analyse_json_obj(json_obj, level=0, res=None, json_key=None):
    if res is None:
        res = []

    # 对字典对象的属性按照基本数据类型->list类型->dict类型的次序排序
    if isinstance(json_obj, dict):
        json_obj = sorted(
            json_obj.items(), key=lambda x:
            (
                isinstance(x[1], dict),
                isinstance(x[1], list),
                isinstance(x[1], str),
                isinstance(x[1], bool),
                isinstance(x[1], float),
                isinstance(x[1], int),
                x[0]
            )
        )

        # 插入父层级数据为dict类型，类型序号为8，层级深度+1，遍历解析所有子属性
        if json_key is None:
            res.append('%s<[dict]>8' % (indent * level))
        else:
            res.append('%s<%s> : <[dict]>8' % (indent * level, json_key))
        level += 1
        for key, value in json_obj:
            analyse_json_obj(value, level, res, key)

    elif isinstance(json_obj, list):
        # 插入父层级数据为list类型，类型序号为9，层级深度+1，并取其第一个元素继续解析
        if json_key is None:
            res.append('%s<[list]>9' % (indent * level))
        else:
            res.append('%s <%s> : <[list]>9' % (indent * level, json_key))
        if len(json_obj) > 0:
            analyse_json_obj(json_obj[0], level + 1, res)

    else:
        # 针对基本数据类型，在插入的键值对数据后再加入类型序号标志位
        obj_type = type(json_obj)
        if obj_type is int:
            obj_type = 1
        elif obj_type is float:
            obj_type = 2
        elif obj_type is bool:
            obj_type = 3
        elif obj_type is str:
            obj_type = 4
        else:
            obj_type = 0
        res.append('%s<%s> : <%s>%d' % (indent * level, json_key, json_obj, obj_type))

    return res


def change_text(com_box, current_text):
    com_box.setCurrentText('List<%s>' % current_text)


# 生成字段类型下拉框
def get_type_combobox(line):
    com_box = QtWidgets.QComboBox()
    com_box.setEditable(True)
    obj_type = int(line[-1]) if line[-1].isdigit() else 0

    if last_list_com_box is not None:
        com_box.currentTextChanged.connect(partial(change_text, last_list_com_box))
    last_list_com_box = None

    # 根据字段数据的最后一位数字标记指定下拉框默认类型
    if obj_type < 8:
        com_box.addItem('Object')
        com_box.addItem('int')
        com_box.addItem('double')
        com_box.addItem('bool')
        com_box.addItem('String')

        com_box.setCurrentIndex(obj_type)
    elif obj_type == 8:
        com_box.setCurrentText('')
    elif obj_type == 9:
        com_box.setCurrentText('List<>')
        # 将该list字段的编辑框临时保存，用于与下一个字段的类型绑定
        global last_list_com_box
        last_list_com_box = com_box

    return com_box


def get_name_text_edit(line):
    te = QtWidgets.QTextEdit(line[line.find('<') + 1:line.find('>')])

    return te


def update_list(json_str):
    json_obj = json.loads(json_str)
    # 传入json对象，返回所需要的格式化协议数据数组
    res = analyse_json_obj(json_obj)

    ui.tv_fields.setRowCount(len(res))

    for i in range(len(res)):
        line = res[i]
        assert isinstance(line, str)
        index = line.find('<')

        ui.tv_fields.setCellWidget(i, 1, get_type_combobox(line))
        if line.strip() == '<[dict]>8':
            label = QtWidgets.QLabel("")
            label.setStyleSheet("background-color: rgb(200,200,200);")
            ui.tv_fields.setCellWidget(i, 2, label)
        else:
            ui.tv_fields.setCellWidget(i, 2, get_name_text_edit(line))

        if index == 0:
            field = line.replace('<', '').replace('>', '')
        else:
            field = ("%s※==》%s" % (' ' * (index - 4), line[index:])).replace('<', '').replace('>', '')

        label = QtWidgets.QLabel()
        label.setText(field[0:60] + '...' if len(field) > 60 else field[0:-1])
        label.setToolTip(field[0:-1])

        ui.tv_fields.setCellWidget(i, 0, label)

    ui.tv_fields.resizeColumnToContents(0)


def json_format():
    # 从文本编辑框获取json字符串
    json_str = ui.te_json.toPlainText()
    if is_json(json_str):
        # 将格式化后的json字符串覆盖到文本编辑框中
        ui.te_json.setText(jformat(json_str.replace('\n', '')))

        # 根据json更新表格条目
        update_list(json_str)

    else:
        msg = QtWidgets.QMessageBox()
        msg.information(ui.te_json, "警告", "JSON不合法", QtWidgets.QMessageBox.Ok)


def generate_bean():
    ui.te_json.setText("OK")


def init_event():
    # 绑定json解析按钮事件
    ui.btn_format.clicked.connect(json_format)
    ui.btn_generate.clicked.connect(generate_bean)


# 设置表格基础样式
def init_table():
    # 设置表头，表头文字居中
    ui.tv_fields.setHorizontalHeaderLabels(['Fields', 'Types', 'Name'])
    ui.tv_fields.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignHCenter)
    # 表头自动平分宽度
    ui.tv_fields.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    # 设置第一列为固定宽度，不参与平分
    ui.tv_fields.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
    ui.tv_fields.resizeColumnToContents(0)
    # 隐藏左侧垂直表头
    ui.tv_fields.verticalHeader().setVisible(False)


def init_view():
    init_table()


def customUI():
    init_view()
    init_event()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    widget = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(widget)
    # 在生成代码的基础上再修改UI以及添加逻辑
    customUI()
    widget.show()
    sys.exit(app.exec_())