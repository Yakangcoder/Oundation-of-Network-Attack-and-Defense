# -*- coding = utf-8 -*-

import os
import sys
import time
import logging
import threading
import scapy.all

from logger import logger
from queue import Queue, Empty
from typing import Dict, Union, Optional

from scapy.all import *
from scapy.all import sniff, Padding, Raw
from scapy.layers.inet import IP, TCP, UDP
from scapy.utils import hexdump, PcapWriter
from scapy.arch.common import compile_filter

from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QMainWindow, QTabWidget
from PySide6.QtWidgets import QListWidgetItem as QLItem
from PySide6.QtWidgets import QTreeWidgetItem as QRItem
from PySide6.QtWidgets import QTableWidgetItem as QTItem

from UI.ui_Sniffer import Ui_MainWindow as main_ui
from UI.ui_About import Ui_Dialog as about_ui

DIRNAME = os.path.dirname(os.path.abspath(__file__))
MAXSIZE = 1024
LOGO = os.path.join(DIRNAME, 'logo.png')


class Signal(QtCore.QObject):
    packet_received = QtCore.Signal(None)


class Packet:
    """ 表示一个数据包的类 """

    def __init__(self, packet):
        if not packet or not isinstance(packet, scapy.packet.Packet):
            raise ValueError("Invalid packet")

        if not packet.haslayer(IP):
            raise ValueError("Packet has no IP layer")

        self.packet = packet
        self.src_ip = packet[IP].src
        self.dst_ip = packet[IP].dst
        self.proto = packet[IP].proto
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.length = len(packet)
        self.sport, self.dport = None, None

        if packet.haslayer(TCP):
            self.sport = packet[TCP].sport
            self.dport = packet[TCP].dport
        elif packet.haslayer(UDP):
            self.sport = packet[UDP].sport
            self.dport = packet[UDP].dport

    def __repr__(self):
        return f"<Packet {self.src_ip} -> {self.dst_ip} ({self.length} bytes)>"

    @classmethod
    def parse_packet(cls, packet):
        return cls(packet)


class Sniffer(QtCore.QThread):
    """ 表示一个网络嗅探器的类 """

    def __init__(self, signal, iface: str, filter_exp: str, queue: Queue, packet: Optional[Packet] = None):
        super().__init__()
        self.signal = signal
        self.iface = iface
        self.filter_exp = filter_exp
        self.queue = queue
        self.packet_obj = packet
        self.logger = logging.getLogger(f"Sniffer({iface})")
        self.timeout = None
        self.sniffer = None

        # 实例化信号
        # self.signal.packet_received.connect(self.queue.put(packet))

        try:
            compile_filter(filter_exp=self.filter_exp)
        except Exception as e:
            self.logger.error(e)
            raise

    def start_sniffer(self, timeout=None):
        self.logger.info("Sniffer started")

        self.sniffer = AsyncSniffer(
            iface=self.iface,
            prn=self.packet_callback,
            filter=self.filter_exp,
        )
        self.sniffer.start()

    def packet_callback(self, packet):
 #       packet_obj = self.packet_obj.parse_packet(packet)
 #       packet_info: Dict[str, Union[str, int, float]] = {
 #           'src_ip': packet_obj.src_ip,
 #           'dst_ip': packet_obj.dst_ip,
 #           'proto': packet_obj.proto,
 #           'timestamp': packet_obj.timestamp,
 #           'length': packet_obj.length,
 #           'sport': packet_obj.sport,
 #           'dport': packet_obj.dport
 #       }
        self.queue.put(packet)
        self.signal.packet_received.emit()

    def stop_sniffer(self):
        if self.sniffer:
            self.sniffer.stop()
            self.logger.info("Sniffer stopped")
            self.sniffer = None
        self.quit()


class MainWindow(QMainWindow):
    """ 网络嗅探器主窗口类 """

    def __init__(self, parent=None) -> None:
        # 初始化代码
        super().__init__(parent)
        self.ui = main_ui()
        self.ui.setupUi(self)

        self.sniffer = None
        self.counter = 0
        self.start_time = 0
        self.queue = Queue()
        self.signal = Signal()  # 新增自定义信号
        self.pcap_writer = None
        self.about = None

        self.setWindowTitle(f"网络嗅探器")
        self.setWindowIcon(QtGui.QIcon(LOGO))
        self.init_interfaces()

        # 创建Packet类实例
        # self.packet = Packet(scapy.all.IP())

        # 创建Sniffer类实例并将Packet类实例传递给它
        # self.sniffer = Sniffer(self.get_iface(), "", self.queue, self.packet)

    # 初始化界面
    def init_interfaces(self):
        """ 初始化界面 """

        # 添加可用的网卡
        for face in get_working_ifaces():
            self.ui.interfaceBox.addItem(face.name)

        # 绑定开始抓包按钮
        self.ui.startButton.clicked.connect(self.start_click)

        # 绑定过滤器编辑框
        self.ui.filterEdit.editingFinished.connect(self.validate_filter)

        # 绑定数据包列表
        self.ui.packetTable.horizontalHeader().setStretchLastSection(True)
        self.ui.packetTable.cellPressed.connect(self.update_content)

        self.ui.treeWidget.itemPressed.connect(self.update_layer_content)

        self.signal.packet_received.connect(self.update_packet)

        self.ui.actionAbout.triggered.connect(self.show_about)

        # 创建Packet类实例
        # self.packet = Packet(IP())

        # 创建Sniffer类实例并将Packet类实例传递给它
        # self.sniffer = Sniffer(self.get_iface(), "", self.queue, self.packet)

    # 显示关于对话框
    def show_about(self):
        """ 显示关于对话框 """

        if not self.about:
            self.about = QtWidgets.QDialog(self)
            self.about.ui = about_ui()
            self.about.ui.setupUi(self.about)
            self.about.ui.version_label.setText("一个网络嗅探器程序\n\nPython  &  Scapy  &  PySide6\n\n\n@Author  Qianran Suen")
            self.about.ui.image_label.setPixmap(QtGui.QPixmap(LOGO))
            self.about.ui.image_label.setScaledContents(True)
        self.about.show()

    # 获取当前选中的网卡名称
    def get_iface(self):
        """ 获取当前网卡 """

        idx = self.ui.interfaceBox.currentIndex()
        iface_name = get_working_ifaces()[idx]
        logger.debug(f"Selected interface: {iface_name}")
        return iface_name

    # 验证过滤器表达式是否有效
    def validate_filter(self):
        exp = self.ui.filterEdit.text().strip()
        if not exp:
            self.ui.filterEdit.setStyleSheet('')
            self.ui.startButton.setEnabled(True)
            return

        try:
            compile_filter(filter_exp=exp)
            # 输入框背景变绿
            self.ui.filterEdit.setStyleSheet('QLineEdit { background-color: rgb(33, 186, 69);}')
            self.ui.startButton.setEnabled(True)

        except Exception:
            # 将输入框背景变红
            self.ui.startButton.setEnabled(False)
            self.ui.filterEdit.setStyleSheet('QLineEdit { background-color: rgb(219, 40, 40);}')
            return

    def get_packet_layers(self, packet):
        counter = 0
        while True:
            layer = packet.getlayer(counter)
            if layer is None:
                break
            yield layer
            counter += 1

    def update_layer_content(self, item, column):
        if not hasattr(item, 'layer'):
            return
        layer = item.layer
        self.ui.contentEdit.setText(hexdump(layer, dump=True))

    def update_content(self, row, column):
        """ 更新数据包信息 """

        logger.debug("%s, %s clicked", row, column)
        item = self.ui.packetTable.item(row, 6)
        if not hasattr(item, 'packet'):
            return
        logger.debug(item)
        logger.debug(item.text())
        packet = item.packet
        self.ui.contentEdit.setText(hexdump(packet, dump=True))
        self.ui.treeWidget.clear()
        for layer in self.get_packet_layers(packet):
            item = QRItem(self.ui.treeWidget)
            item.layer = layer
            item.setText(0, layer.name)

            for name, value in layer.fields.items():
                child = QRItem(item)
                child.setText(0, f"{name}: {value}")

    def update_packet(self):
        packet = self.queue.get(False)
        if not packet:
            return

        if self.ui.packetTable.rowCount() >= MAXSIZE:
            self.ui.packetTable.removeRow(0)

        row = self.ui.packetTable.rowCount()
        self.ui.packetTable.insertRow(row)

        # No.
        self.counter += 1
        self.ui.packetTable.setItem(row, 0, QTItem(str(self.counter)))

        # Time
        elapse = time.time() - self.start_time
        self.ui.packetTable.setItem(row, 1, QTItem(f"{elapse:2f}"))

        # source
        if isinstance(packet.getlayer("IP"), IP):
            src = packet[IP].src
            dst = packet[IP].dst
        else:
            src = packet.src
            dst = packet.dst

        self.ui.packetTable.setItem(row, 2, QTItem(src))

        # destination
        self.ui.packetTable.setItem(row, 3, QTItem(dst))

        # protocol
        layer = None
        for var in self.get_packet_layers(packet):
            if not isinstance(var, (Padding, Raw)):
                layer = var

        protocol = layer.name
        self.ui.packetTable.setItem(row, 4, QTItem(str(protocol)))

        # length
        length = f"{len(packet)}"
        self.ui.packetTable.setItem(row, 5, QTItem(length))

        # info
        info = str(packet.summary())
        item = QTItem(info)
        item.packet = packet
        self.ui.packetTable.setItem(row, 6, item)

    def sniff_action(self, packet):
        if not self.sniffer:
            return

        self.queue.put(packet)
        self.signal.packet_received.emit()

    # 启动嗅探器
    def start_click(self):
        """ 启动嗅探器 """

        logger.debug("start button was clicked")
        if self.sniffer:
            self.sniffer.stop_sniffer()
            self.sniffer = None
            self.ui.startButton.setText("开始")
            self.ui.interfaceBox.setEnabled(True)
            self.ui.filterEdit.setEnabled(True)
            return

        exp = self.ui.filterEdit.text()
        logger.debug("filter expression %s", exp)

        iface = self.get_iface()
        logger.debug("sniffing interface %s", iface)

        self.sniffer = Sniffer(self.signal, iface, exp, self.queue)
        self.sniffer.start_sniffer()
        self.counter = 0
        self.start_time = time.time()

        self.ui.startButton.setText("停止")
        self.ui.interfaceBox.setEnabled(False)
        self.ui.filterEdit.setEnabled(False)
        self.ui.packetTable.clearContents()
        self.ui.packetTable.setRowCount(0)
        self.ui.treeWidget.clear()
        self.ui.contentEdit.clear()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
