# -*- coding: utf-8 -*-
"""
Python3 + PySide
"""

ORDERED = False
from collections import OrderedDict
import sys
import operator
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import *

class MyTableView(QTableView):
    def __init__(self, parent=None, *args):
        QTableView.__init__(self, parent, *args)

class MyTableModel(QAbstractTableModel):
    def __init__(self, data, headerdata, columns, parent=None, *args):
        QAbstractTableModel.__init__(self, parent, *args)

        rowlist = []
        for i in range(data.size[0]):
            row = [i, ]
            for c in columns:
                row.append(data[c.lower()][i])
            rowlist.append(row)
        headerdata.insert(0, 'id')
        #columns.insert(0, 'id')

        self.header = headerdata
        self.columns = columns
        self.dbdata = rowlist

    def getColumnData(self, column):
        return [x[column].toPyObject() for x in self.data if isinstance(x[column], QVariant)]

    def rowCount(self, parent):
        return len(self.dbdata)

    def columnCount(self, parent):
        if len(self.dbdata) < 1:
            return 0
        else:
            return len(self.dbdata[0])
   
    def get_value(self, index):
        i = index.row()
        j = index.column()
        try:
            return self.dbdata[i][j]
        except AttributeError:
            return self.dbdata[i][j]

    def data(self, index, role):
        if not index.isValid():
            return None
        value = self.get_value(index)

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return value
        elif role == Qt.TextAlignmentRole:
                return Qt.AlignCenter
        return None

        if isinstance(self.dbdata[index.row()][index.column()], str):
            return self.data[index.row()][index.column()].decode("utf-8")
        else:
            return QtCore.QVariant(self.data[index.row()][index.column()])

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            
            try:
                return self.header[col]
            except IndexError:
                return self.header[col-1]

    def sort(self, Ncol, order):
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.dbdata = sorted(self.dbdata, key=operator.itemgetter(Ncol))
        if order == Qt.DescendingOrder:
            self.dbdata.reverse()
        self.emit(SIGNAL("layoutChanged()"))


    def setData(self, index, value, role):
        if index.isValid() and role == Qt.EditRole:
            self.data[index.row()][index.column()] = value
            self.model.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
            return True
        else:
            return False

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable


class Table(object):
    """ Fast table for PySide """

    def __init__(self, **kwargs):
        __slots__ = [
            'data', 'type_dict', 'type_list', 'type_ordereddict',
            'default_value'
        ]
        if ORDERED:
            self.data = OrderedDict()
        else:
            self.data = {}
        self.default_value = ''  # None?
        self.type_dict = type({})
        self.type_list = type([])
        self.type_ordereddict = type(OrderedDict())
        self.convert_numeric = False  # True? Then mind it!!!

        if 'data' in kwargs:  # Fill on creation?
            values = kwargs['data']
            if type(values) == self.type_dict:
                self.add_dict(values)
            elif type(values) == self.type_list:
                self.merge(values)

    def clear(self):
        self.data = OrderedDict()

    def __call__(self):
        return self.to_dict()

    def __getitem__(self, somekey):
        return self.to_dict().get(somekey, [])

    @property
    def size(self):
        """
        (# of records, # of columns)
        """
        return (self.len, len(self.keys))

    @property
    def len(self):
        return self.__data_len__()

    @property
    def keys(self):
        return sorted(self.data.keys())

    @property
    def reverse_keys(self):
        return [key for key in self.keys][::-1]

    def __data_len__(self):
        """ Length of data[first key] list. """
        _ = 0
        for key in self.keys:
            if self.data[key]:
                _ = len(self.data[key])
                break
        return _

    def to_dict(self):
        """ Legacy code """
        return self.data

    def subtract_lists(self, x, y):
        return [item for item in x if item not in y]

    def add_dict(self, adict):
        """
        Cool, but not needed
        ====================
        """
        if self.convert_numeric:
            from fastnumbers import fast_float as ff
            to_add = {
                k: ff(adict[k]) if adict[k] else ''
                for k in adict.keys()
            }
        else:
            to_add = adict
        """ Add columns if not exist """
        if not set(to_add.keys()).issubset(
                self.data.keys()):  # New key means adding
            new_keys = \
                sorted(self.subtract_lists(to_add.keys(), \
                                        self.data.keys()))          # it to our dict
            newdict = {key: [self.default_value] \
                    * self.__data_len__() for key in new_keys}
            self.data.update(newdict)

        [self.data[key].append(to_add.get(key, \
                                self.default_value)) \
                                    for key in self.keys]

    def merge(self, somedata):
        if type(somedata) == self.type_dict \
                or type(somedata) == self.type_ordereddict:
            self.add_dict(somedata)
            return
        if type(somedata) == self.type_list:
            for data in somedata:
                self.add_dict(data)
                return
        print('Table: merge: Unsupported: %s' % type(somedata))
        return

    def get_recno(self, n):
        """
        Get dict of a last record
        """
        _ = {key: self.data[key][n] for key in self.data.keys()}
        return _

    def get_last(self):
        _ = self.__data_len__() - 1
        return self.get_recno(_)

    def __iter__(self):
        for _ in range(0, self.len):
            yield self.get_recno(_)

    def find(self, search_dict):  # Not tested
        _res = []
        for row in self:
            for key in search_dict:
                """
                Important on searching for empty values
                """
                if getattr(row, key, '') != search_dict[key]:
                    break
            _res.append(row)
        return _res

    def find_one(self, search_dict):
        _res = []
        for row in self:  # <-- self iterator
            for key in search_dict:
                if row[key] != search_dict[key]:
                    break
                else:
                    _res = (row)
        return _res

    def __repr__(self):
        return '%s' % self.data

    def replace(self, key, somedata):
        value = somedata.get(key, None)
        """
        if not value:
            self.add_dict(somedata)
            return
        """
        if value not in self.data.get(key, []):  # we don't need to replace?
            self.add_dict(somedata)
            return
        else:
            for n in range(0, self.len):  # duplicate, we need to!
                if self.data[key][n] == somedata[key]:
                    for key in somedata:
                        self.data[key][n] = somedata[key]
                    break  # Replace only one
                else:
                    pass
                    #print('Dict replace error')                    # Not always error.


##############################
# Now, tests...              #
##############################
if __name__ == '__main__':

    def set_table_widget(table_object, data):
        ######################################################
        #  QTableWidget from dict-like table, 'easy' way     #
        ######################################################
        num_rows = data.len
        table_object.setRowCount(num_rows)
        keys = data.reverse_keys
        table_object.setColumnCount(len(keys))
        qkeys = [str(k).upper()[:20] for k in keys]
        table_object.setHorizontalHeaderLabels(qkeys)

        for n, key in enumerate(keys):
            for m, item in enumerate(data()[key]):
                newitem = QTableWidgetItem(str(item))
                newitem.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                table_object.setItem(m, n, newitem)
        return num_rows

    table = Table()
    for n in range(100000):
        table.add_dict({'one':1, 'two':2, 'three': 3})
        table.add_dict({'one':11, 'two':22, 'three': 33})
        table.add_dict({'one':111, 'two':222,
                    'three': 333, 'four': 4444})

    app = QApplication(sys.argv)
    window = QWidget()
    layout = QGridLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    window.setLayout(layout)
    tv = MyTableView()
    keys = [str(k).upper()[:20] for k in table.reverse_keys]
    tm = MyTableModel(table, keys, keys)
    tv.setModel(tm)
    tv.setAlternatingRowColors(True)
    tv.setSortingEnabled(True)
    tv.setColumnHidden(0, True)
    layout.addWidget(tv)
    tv.show()
    window.show()
    window.showMaximized()
    sys.exit(app.exec_())
