import numpy as np
import random
import sys
from collections import deque
import time
from enum import Enum
import pyvisa

import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import (QApplication, QMainWindow,
                             QDialog, QTableWidget, QTableWidgetItem,
                             QLabel, QPushButton)
from PyQt5.QtCore import QTimer, QSize


class Mode(Enum):
    '''
    Enum class specifying a data acquisition mode: dormant and waiting
    to be woken up (IDLE), live streaming data to display (MONITOR),
    and collecting/saving data to a file (RECORD).
    '''
    IDLE = 0
    MONITOR = 1
    RECORD = 2

class Parameters(Enum):
    '''Enum class for parameters used throughout the code.'''
    FPS = 30                # frames/second of the plot display
    DAQ_SPEED = 50            # data acquisition rate in milliseconds
    BUFFER_LEN = 1000       # number of data points in the live buffer

##print(Mode.__members__)
##print(Mode.IDLE.name)
##print(Mode.IDLE.value)


class EquipmentManager(QMainWindow):
    '''
    Main GUI thread using uic.loadUI(), grabbing the
    QtDesigner widgets. Widgets control the state of the data
    acquisition class called 'DAQThread', simulating experimental
    data monitoring in real time.
    '''
    connect_equipment = QtCore.pyqtSignal(object)
    def __init__(self):
        QMainWindow.__init__(self)
        uic.loadUi("equipment_manager.ui", self)

        self.lockin_button = QPushButton("Connect")
        self.oscilloscope_button = QPushButton("Connect")
        self.equipment_list = [("Lockin", "USB0::0xB506::0x2000::003051::INSTR", "Disconnected", self.lockin_button),
                          ("Oscilloscope", "USB::EQUIPMENT::TAG2", "Disconnected", self.oscilloscope_button)]

        self.lockin = None
        self.oscilloscope = None

        self.mutex = QtCore.QMutex()

        self.rm = pyvisa.ResourceManager()

        self.listWidget.addItems(self.rm.list_resources())
        
        table = self.tableWidget
        table.setRowCount(len(self.equipment_list))
        table.setColumnCount(len(self.equipment_list[0]))
        table.setHorizontalHeaderLabels(["Name", "Visa tag", "Status",""])

        for i, (name, tag, status, button) in enumerate(self.equipment_list):
            _name = QTableWidgetItem(name)
            _tag = QTableWidgetItem(tag)
            _status = QTableWidgetItem(status)
            table.setItem(i, 0, _name)
            table.setItem(i, 1, _tag)
            table.setItem(i, 2, _status)
            table.setCellWidget(i, 3, button)
            button.clicked.connect(lambda checked, x=_tag: self.connect_equipment.emit(x))

        table.resizeRowsToContents()
        table.resizeColumnsToContents()
        table.show()

        self.connect_equipment.connect(self._test)

        self.resource_list_thread = AvailableResourceList(self)
        self.resource_list_thread.start()

    @QtCore.pyqtSlot(object)
    def _test(self, name) -> None:
        print(name.text())

    def closeEvent(self, event):
        print("Closing application...")
        self.resource_list_thread.stop()
        event.accept()

class AvailableResourceList(QtCore.QThread):
    def __init__(self, parent):
        super().__init__()
        self.running = True
        self.parent = parent

    def run(self) -> None:
        '''
        Runs once the thread is started with the
        thread.start() method. This function is not
        explicitly called.
        '''
        while self.running:
            self.parent.mutex.lock()
            resource_list = self.parent.rm.list_resources()
            self.parent.mutex.unlock()
            old_resource_list = []
            for i in range(self.parent.listWidget.count()):
                old_resource_list.append(self.parent.listWidget.item(i).text())
            for i in resource_list:
                if i not in old_resource_list:
                    self.parent.listWidget.addItem(i)
                else:
                    pass
            for i in range(len(old_resource_list)):
                if old_resource_list[i] not in resource_list:
                    old_item = self.parent.listWidget.takeItem(i)
                    del old_item
                else:
                    pass

            self.sleep(2)

    def stop(self) -> None:
        self.running = False

        # wake thread if sleeping in IDLE state
        #self.wait_condition.wakeAll()

        self.quit()
        self.wait()

        # close VISA connection safely
##        try:
##            self.lockin.close()
##            self.rm.close()
##        except:
##            pass



if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = EquipmentManager()
    win.show()
    sys.exit(app.exec_())











