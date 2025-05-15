import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, \
    QDoubleSpinBox, QMessageBox, QComboBox, QSpinBox
from PyQt5.QtGui import QPixmap, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backend_bases import MouseButton, KeyEvent
import matplotlib.font_manager as fm
import threading


class DrawingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_fonts()
        self.selected_points = []  # 存储用户选择的点
        self.all_intersect_points = []  # 存储所有交点
        self.midpoints = []  # 存储所有中点
        self.ray_intersect_points = {}  # 按等分线存储交点
        self.zoom_factor = 1.2  # 缩放因子
        self.initUI()

    def setup_fonts(self):
        chinese_fonts = [
            "SimHei", "WenQuanYi Micro Hei", "Heiti TC",
            "Microsoft YaHei", "SimSun", "Arial Unicode MS"
        ]
        available_fonts = [f.name for f in fm.fontManager.ttflist]
        self.chinese_font = next((font for font in chinese_fonts if font in available_fonts),
                                 plt.rcParams["font.family"][0])
        plt.rcParams["font.family"] = self.chinese_font
        plt.rcParams['axes.unicode_minus'] = False

    def initUI(self):
        main_layout = QHBoxLayout()
        self.figure = plt.figure(figsize=(18, 15))
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas, 7)

        param_layout = QVBoxLayout()

        # 参数输入
        self.a_input = QLineEdit('0.5')
        self.b_input = QLineEdit('0.15')
        self.div_spinbox = QDoubleSpinBox()
        self.div_spinbox.setRange(1, 180)
        self.div_spinbox.setValue(15)  # 默认值设小一些，以便显示更多等分线
        self.div_spinbox.setSingleStep(1)

        # 螺旋线起始角度参数
        self.start_angle_spinbox = QDoubleSpinBox()
        self.start_angle_spinbox.setRange(0, 2 * np.pi)
        self.start_angle_spinbox.setValue(0.5)  # 默认从0.5弧度开始
        self.start_angle_spinbox.setSingleStep(0.1)
        self.start_angle_spinbox.setDecimals(1)

        param_layout.addWidget(QLabel('参数 a:'))
        param_layout.addWidget(self.a_input)
        param_layout.addWidget(QLabel('参数 b:'))
        param_layout.addWidget(self.b_input)
        param_layout.addWidget(QLabel('等分角度 (度):'))
        param_layout.addWidget(self.div_spinbox)
        param_layout.addWidget(QLabel('螺旋线起始角度 (弧度):'))
        param_layout.addWidget(self.start_angle_spinbox)

        # 勾选框
        self.show_guide_checkbox = QCheckBox('显示辅助线')
        self.show_div_checkbox = QCheckBox('显示等分线')
        self.show_intersect_checkbox = QCheckBox('显示所有交点')
        self.show_midpoints_checkbox = QCheckBox('显示中点')
        for checkbox in [self.show_guide_checkbox, self.show_div_checkbox,
                         self.show_intersect_checkbox, self.show_midpoints_checkbox]:
            checkbox.setChecked(True)
            param_layout.addWidget(checkbox)

        self.distance_label = QLabel('选择两个点测量距离')
        param_layout.addWidget(self.distance_label)

        draw_button = QPushButton('绘制')
        draw_button.clicked.connect(self.start_drawing)
        clear_button = QPushButton('清除选择')
        clear_button.clicked.connect(self.clear_selected_points)
        reset_view_button = QPushButton('重置视图')
        reset_view_button.clicked.connect(self.reset_view)
        param_layout.addWidget(draw_button)
        param_layout.addWidget(clear_button)
        param_layout.addWidget(reset_view_button)

        main_layout.addLayout(param_layout, 3)
        self.setFont(QFont(self.chinese_font, 10))
        self.setLayout(main_layout)
        self.setWindowTitle('对数螺旋线分析工具')
        self.resize(1800, 1350)
        self.show()

        # 连接鼠标滚轮事件
        self.canvas.mpl_connect('scroll_event', self.zoom_handler)
        # 连接鼠标点击事件
        self.canvas.mpl_connect('button_press_event', self.on_click)
        # 存储初始视图限制，用于重置
        self.initial_xlim = None
        self.initial_ylim = None

    def start_drawing(self):
        # 在单独线程中执行绘图操作
        draw_thread = threading.Thread(target=self.draw_logarithmic_spiral)
        draw_thread.start()

    def draw_logarithmic_spiral(self):
        try:
            a = float(self.a_input.text())
            b = float(self.b_input.text())
            div_angle = self.div_spinbox.value()
            start_angle = self.start_angle_spinbox.value()

            theta = np.linspace(start_angle, 10 * np.pi, 10000)
            r = a * np.exp(b * theta)
            x = r * np.cos(theta)
            y = r * np.sin(theta)

            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.plot(x, y, color='r', label='对数螺旋线')

            # 计算等分线与螺旋线的交点
            self.all_intersect_points = []
            self.ray_intersect_points = {}  # 按角度存储交点
            if self.show_div_checkbox.isChecked():
                for i in range(len(theta)):
                    angle = np.arctan2(y[i], x[i])
                    angle_deg = np.degrees(angle) % 360
                    # 找到最接近的等分角度
                    closest_div = round(angle_deg / div_angle) * div_angle % 360

                    if np.abs(angle_deg - closest_div) < (div_angle / 100):
                        point = (x[i], y[i])
                        self.all_intersect_points.append(point)
                        # 存储到对应角度的列表中
                        if closest_div not in self.ray_intersect_points:
                            self.ray_intersect_points[closest_div] = []
                        self.ray_intersect_points[closest_div].append(point)

            # 按距离排序每个角度的交点
            for angle in self.ray_intersect_points:
                self.ray_intersect_points[angle].sort(key=lambda p: np.hypot(p[0], p[1]))

            # 计算每条等分线上相邻交点的中点
            self.midpoints = []
            if self.show_midpoints_checkbox.isChecked():
                for angle in self.ray_intersect_points:
                    points = self.ray_intersect_points[angle]
                    for i in range(len(points) - 1):
                        p1 = points[i]
                        p2 = points[i + 1]
                        mid_x = (p1[0] + p2[0]) / 2
                        mid_y = (p1[1] + p2[1]) / 2
                        self.midpoints.append((mid_x, mid_y))

            # 绘制其他元素（如辅助线、等分线、交点等）
            if self.show_guide_checkbox.isChecked():
                for i in range(0, len(theta), 50):
                    ax.plot([0, x[i]], [0, y[i]], color='g', alpha=0.3)

            if self.show_div_checkbox.isChecked():
                max_r = np.max(r) * 1.1
                div_angle_rad = np.radians(div_angle)
                num_lines = int(np.ceil(360 / div_angle))
                for i in range(num_lines):
                    angle = i * div_angle_rad
                    end_x = max_r * np.cos(angle)
                    end_y = max_r * np.sin(angle)
                    ax.plot([0, end_x], [0, end_y], color='purple', alpha=0.6)

            if self.show_intersect_checkbox.isChecked() and self.all_intersect_points:
                ix, iy = zip(*self.all_intersect_points)
                ax.scatter(ix, iy, color='black', s=10, zorder=5, label='交点')

            if self.show_midpoints_checkbox.isChecked() and self.midpoints:
                mx, my = zip(*self.midpoints)
                ax.scatter(mx, my, color='blue', s=10, zorder=6, label='中点')

            if self.selected_points:
                sx, sy = zip(*self.selected_points)
                ax.scatter(sx, sy, color='orange', s=30, zorder=7, label='已选择')
                if len(self.selected_points) == 2:
                    p1, p2 = self.selected_points
                    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='orange', linestyle='--', zorder=4)
                    dist = np.hypot(p2[0] - p1[0], p2[1] - p1[1])
                    self.distance_label.setText(f'距离: {dist:.4f}')

            # 调整视图范围
            max_r = np.max(r)
            view_factor = 0.8
            ax.set_xlim([-max_r * view_factor, max_r * view_factor])
            ax.set_ylim([-max_r * view_factor, max_r * view_factor])

            # 保存初始视图限制
            self.initial_xlim = ax.get_xlim()
            self.initial_ylim = ax.get_ylim()

            ax.set_aspect('equal')
            ax.set_title('对数螺旋线分析工具')
            ax.legend()
            self.canvas.draw()

        except ValueError as e:
            QMessageBox.critical(self, "输入错误", f"请输入有效的数值: {str(e)}")

    def zoom_handler(self, event):
        """处理鼠标滚轮缩放事件"""
        if event.inaxes is None:
            return

        ax = event.inaxes
        xdata, ydata = event.xdata, event.ydata

        # 计算缩放比例
        if event.button == 'up':
            scale_factor = 1 / self.zoom_factor
        else:  # event.button == 'down'
            scale_factor = self.zoom_factor

        # 获取当前视图限制
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        # 计算新的视图限制，以鼠标位置为中心
        x_center = xdata
        y_center = ydata

        new_x_width = (xlim[1] - xlim[0]) * scale_factor
        new_y_width = (ylim[1] - ylim[0]) * scale_factor

        new_xlim = [x_center - new_x_width / 2, x_center + new_x_width / 2]
        new_ylim = [y_center - new_y_width / 2, y_center + new_y_width / 2]

        # 设置新的视图限制
        ax.set_xlim(new_xlim)
        ax.set_ylim(new_ylim)

        self.canvas.draw()

    def on_click(self, event):
        """处理鼠标点击事件，用于选择点"""
        if event.button == MouseButton.LEFT and event.inaxes:
            if not self.all_intersect_points and not self.midpoints:
                return
            click_x, click_y = event.xdata, event.ydata
            distances = []

            # 检查是否点击了交点或中点
            for px, py in self.all_intersect_points + self.midpoints:
                distances.append(np.hypot(px - click_x, py - click_y))

            min_idx = np.argmin(distances)
            max_r = max(np.hypot(px, py) for px, py in self.all_intersect_points + self.midpoints)

            if distances[min_idx] < max_r * 0.05:  # 只在距离很近时才认为是点击了交点
                # 修正索引错误
                points = self.all_intersect_points + self.midpoints
                if min_idx < len(points):
                    point = points[min_idx]

                    if point in self.selected_points:
                        self.selected_points.remove(point)
                    else:
                        if len(self.selected_points) >= 2:
                            self.selected_points.pop(0)
                        self.selected_points.append(point)

                    self.draw_logarithmic_spiral()

    def clear_selected_points(self):
        """清除已选择的点"""
        self.selected_points = []
        self.distance_label.setText('选择两个点测量距离')
        self.draw_logarithmic_spiral()

    def reset_view(self):
        """重置视图到初始状态"""
        if self.initial_xlim and self.initial_ylim:
            ax = self.figure.gca()
            ax.set_xlim(self.initial_xlim)
            ax.set_ylim(self.initial_ylim)
            self.canvas.draw()

    def show_error_message(self, message):
        QMessageBox.critical(self, "输入错误", message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DrawingApp()
    sys.exit(app.exec_())