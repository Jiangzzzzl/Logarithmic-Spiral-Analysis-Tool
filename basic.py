import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtGui import QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class DrawingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 创建主布局
        main_layout = QHBoxLayout()

        # 左边的绘图区域
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        # 右边的参数输入区域
        param_layout = QVBoxLayout()

        # 参数 a 输入
        a_label = QLabel('参数 a:')
        self.a_input = QLineEdit()
        param_layout.addWidget(a_label)
        param_layout.addWidget(self.a_input)

        # 参数 b 输入
        b_label = QLabel('参数 b:')
        self.b_input = QLineEdit()
        param_layout.addWidget(b_label)
        param_layout.addWidget(self.b_input)

        # 绘制按钮
        draw_button = QPushButton('绘制')
        draw_button.clicked.connect(self.draw_logarithmic_spiral)
        param_layout.addWidget(draw_button)

        main_layout.addLayout(param_layout)

        self.setLayout(main_layout)
        self.setWindowTitle('参数化绘图')
        self.show()

    def draw_logarithmic_spiral(self):
        try:
            a = float(self.a_input.text())
            b = float(self.b_input.text())
            theta = np.linspace(0, 10 * np.pi, 1000)
            r = a * np.exp(b * theta)
            x = r * np.cos(theta)
            y = r * np.sin(theta)

            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.plot(x, y, color='r')
            ax.set_xlim([-np.max(r) - 1, np.max(r) + 1])
            ax.set_ylim([-np.max(r) - 1, np.max(r) + 1])
            ax.set_aspect('equal', adjustable='box')
            self.canvas.draw()
        except ValueError:
            print("请输入有效的数值")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DrawingApp()
    sys.exit(app.exec_())
