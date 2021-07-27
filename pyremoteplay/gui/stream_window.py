"""Stream Window for GUI."""
import asyncio
import sys
import threading
import time
from enum import Enum

from pyremoteplay.av import ProcessReceiver, QueueReceiver
from pyremoteplay.ctrl import CTRLAsync
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

from .util import label, message


class CTRLWorker(QtCore.QObject):
    finished = QtCore.Signal()
    started = QtCore.Signal()

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.ctrl = None
        self.thread = None

    def run(self):
        if not self.ctrl:
            print("No CTRL")
            self.ctrl = None
            self.finished.emit()
            return
        self.thread = threading.Thread(
            target=self.worker,
        )
        self.thread.start()

    def stop(self):
        if self.ctrl:
            print(f"Stopping Session @ {self.ctrl.host}")
            self.ctrl.stop()
            self.ctrl.loop.stop()
            del self.ctrl
        self.ctrl = None
        self.finished.emit()

    def get_ctrl(self, host, profile, resolution, fps):
        self.ctrl = CTRLAsync(host, profile, resolution=resolution, fps=fps, av_receiver=QueueReceiver)
        # self.ctrl.av_receiver.add_audio_cb(self.handle_audio)

    def worker(self):
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        self.ctrl.loop = asyncio.new_event_loop()
        task = self.ctrl.loop.create_task(self.start())
        print("CTRL Start")
        self.ctrl.loop.run_until_complete(task)
        if self.ctrl:
            self.ctrl.loop.run_forever()
        print("CTRL Finished")
        task.cancel()
        self.stop()

    async def start(self):
        status = await self.ctrl.start()
        if not status:
            print("CTRL Failed to Start")
            message(None, "Error", self.ctrl.error)
            self.stop()
        else:
            self.started.emit()

    def send_standby(self):
        self.ctrl.standby()
        self.stop()

    def stick_state(self, stick: str, direction: str = None, value: float = None, point=None):
        if point is not None:
            self.ctrl.controller.stick(stick, point=point)
            return

        if direction in ("LEFT", "RIGHT"):
            axis = "X"
        else:
            axis = "Y"
        if direction in ("UP", "LEFT") and value != 0.0:
            value *= -1.0
        self.ctrl.controller.stick(stick, axis, value)

    def send_button(self, button, action):
        self.ctrl.controller.button(button, action)


class AVProcessor(QtCore.QObject):
    frame = QtCore.Signal()

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.pixmap = None

    def next_frame(self):
        frame = self.window.worker.ctrl.av_receiver.get_video_frame()
        if frame is None:
            return
        self.window.frame_mutex.lock()
        self.pixmap = QtGui.QPixmap.fromImage(
            QtGui.QImage(
                bytearray(frame.planes[0]),
                frame.width,
                frame.height,
                frame.width * 3,
                QtGui.QImage.Format_RGB888,
            )
        )
        self.window.frame_mutex.unlock()
        # Clear Queue if behind. Try to use latest frame.
        if self.window.worker.ctrl.av_receiver.queue_size > 3:
            self.window.worker.ctrl.av_receiver.v_queue.clear()
        self.frame.emit()


class JoystickWidget(QtWidgets.QFrame):
    def __init__(self, window, left=False, right=False):
        super().__init__(window)
        self.window = window
        self.left = Joystick(self, "left") if left else None
        self.right = Joystick(self, "right") if right else None
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background-color: rgba(255, 255, 255, 0.4); border-radius:25%;")
        for joystick in [self.left, self.right]:
            self.layout.addWidget(joystick)
            joystick.show()

    def hide_sticks(self):
        self.left.hide()
        self.right.hide()

    def show_sticks(self, left=False, right=False):
        width = 0
        should_show = False
        if left:
            width += Joystick.SIZE
            self.left.show()
            should_show = True
        if right:
            width += Joystick.SIZE
            self.right.show()
            should_show = True
        self.resize(width, Joystick.SIZE)
        self.show()

    def default_pos(self):
        if self.window.fullscreen:
            width = self.window.main_window.screen.virtualSize().width()
            height = self.window.main_window.screen.virtualSize().height()
        else:
            width = self.window.size().width()
            height = self.window.size().height()
        x_pos = width / 2 - self.size().width() / 2
        y_pos = height - self.size().height()
        new_pos = QtCore.QPoint(x_pos, y_pos)
        self.move(new_pos)

    def mousePressEvent(self, event):
        self.grab_outside = True
        self._last_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.grab_outside = False

    def mouseMoveEvent(self, event):
        if self.grab_outside:
            cur_pos = self.mapToGlobal(self.pos())
            global_pos = event.globalPos()
            diff = global_pos - self._last_pos
            new_pos = self.mapFromGlobal(cur_pos + diff)
            if self.window.fullscreen:
                max_x = self.window.main_window.screen.virtualSize().width()
                max_y = self.window.main_window.screen.virtualSize().height()
            else:
                max_x = self.window.size().width()
                max_y = self.window.size().height()
            x_pos = min(max(new_pos.x(), 0), max_x - self.size().width())
            y_pos = min(max(new_pos.y(), 0), max_y - self.size().height())
            new_pos = QtCore.QPoint(x_pos, y_pos)
            self.move(new_pos)
            self._last_pos = global_pos


class Joystick(QtWidgets.QLabel):

    SIZE = 180

    class Direction(Enum):
        LEFT = 0
        RIGHT = 1
        UP = 2
        DOWN = 3

    def __init__(self, parent, stick):
        super().__init__(parent)
        self.parent = parent
        self.stick = stick
        self.setMinimumSize(Joystick.SIZE, Joystick.SIZE)
        self.movingOffset = QtCore.QPointF(0, 0)
        self.grabCenter = False
        self.__maxDistance = 50
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.0)")

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        bounds = QtCore.QRectF(-self.__maxDistance, -self.__maxDistance, self.__maxDistance * 2, self.__maxDistance * 2).translated(self._center())
        painter.setBrush(QtGui.QColor(75, 75, 75, 150))
        painter.drawEllipse(bounds)
        painter.setBrush(Qt.black)
        painter.drawEllipse(self._centerEllipse())

    def _centerEllipse(self):
        if self.grabCenter:
            return QtCore.QRectF(-40, -40, 80, 80).translated(self.movingOffset)
        return QtCore.QRectF(-40, -40, 80, 80).translated(self._center())

    def _center(self):
        return QtCore.QPointF(self.width()/2, self.height()/2)

    def _boundJoystick(self, point):
        limitLine = QtCore.QLineF(self._center(), point)
        if (limitLine.length() > self.__maxDistance):
            limitLine.setLength(self.__maxDistance)
        return limitLine.p2()

    def joystickDirection(self):
        if not self.grabCenter:
            return (0.0, 0.0)
        vector = QtCore.QLineF(self._center(), self.movingOffset)
        point = vector.p2()
        point_x = (point.x() - self._center().x()) / self.__maxDistance
        point_y = (point.y() - self._center().y()) / self.__maxDistance
        return (point_x, point_y)

    def mousePressEvent(self, event):
        is_center = self._centerEllipse().contains(event.pos())
        if is_center:
            self.grabCenter = True
            self.movingOffset = self._boundJoystick(event.pos())
            self.update()
        if not self.grabCenter:
            self.parent.mousePressEvent(event)
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if not self.grabCenter:
            self.parent.mouseMoveEvent(event)
        self.grabCenter = False
        self.movingOffset = QtCore.QPointF(0, 0)
        self.update()
        point = self.joystickDirection()
        self.parent.window.worker.stick_state(self.stick, point=point)

    def mouseMoveEvent(self, event):
        if self.grabCenter:
            self.movingOffset = self._boundJoystick(event.pos())
            self.update()
            point = self.joystickDirection()
            self.parent.window.worker.stick_state(self.stick, point=point)
        else:
            self.parent.mouseMoveEvent(event)


class StreamWindow(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.hide()
        print(self.main_window.screen.virtualSize().width(), self.main_window.screen.virtualSize().height())
        self.setMaximumWidth(self.main_window.screen.virtualSize().width())
        self.setMaximumHeight(self.main_window.screen.virtualSize().height())
        self.setStyleSheet("background-color: black")
        self.video_output = QtWidgets.QLabel(self, alignment=Qt.AlignCenter)
        #self.video_output.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        self.audio_output = None
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.video_output)
        self.joystick = JoystickWidget(self, left=True, right=True)
        self.joystick.hide()
        self.input_options = None
        self.fps_label = label(self, "FPS: ")
        self.worker = CTRLWorker(self)
        self.av_worker = AVProcessor(self)
        self.timer = QtCore.QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.av_worker.next_frame)
        self.ms_refresh = 0

        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.cleanup)
        self.worker.started.connect(self.show_video)

        self.av_thread = QtCore.QThread()
        self.av_worker.moveToThread(self.av_thread)
        self.av_thread.started.connect(self.start_timer)
        self.av_worker.frame.connect(self.new_frame)

    def start(self, host, name, profile, resolution='720p', fps=60, show_fps=False, fullscreen=False, input_map=None, input_options=None):
        self.input_options = input_options
        self.frame_mutex = QtCore.QMutex()
        self.video_output.hide()
        self.mapping = ControlsWidget.DEFAULT_MAPPING if input_map is None else input_map
        self.fps = fps
        self.fullscreen = fullscreen
        self.ms_refresh = 1000.0/self.fps
        self.setWindowTitle(f"Session {name} @ {host}")
        self.worker.get_ctrl(host, profile, resolution, fps)

        if show_fps:
            self.init_fps()
            self.fps_label.show()
        else:
            self.fps_label.hide()
        self.thread.start()
        self.av_thread.start()

    def show_video(self):
        self.resize(self.worker.ctrl.resolution['width'], self.worker.ctrl.resolution['height'])
        if self.fullscreen:
            self.showFullScreen()
        else:
            self.show()
        self.video_output.show()
        joysticks = self.input_options.get("joysticks")
        if joysticks:
            self.joystick.hide_sticks()
            self.joystick.show_sticks(joysticks['left'], joysticks['right'])
            self.joystick.default_pos()

# Waiting on pyside6.2
#    def init_audio(self):
#        config = self._a_stream._audio_config
#        format = QtMultimedia.QAudioFormat()
#        format.setChannels(config['channels'])
#        format.setFrequency(config['rate'])
#        format.setSampleSize(config['bits'])
#        format.setCodec("audio/pcm")
#        format.setByteOrder(QtMultimedia.QAudioFormat.LittleEndian)
#        format.setSampleType(QtMultimedia.QAudioFormat.SignedInt)
#        output = QtMultimedia.QAudioOutput(format)
#        self.audio_output = output.start()

    def new_frame(self):
        self.frame_mutex.lock()
        if self.av_worker.pixmap is not None:
            self.video_output.setPixmap(self.av_worker.pixmap)
        self.frame_mutex.unlock()
        self.set_fps()

    def init_fps(self):
        self.fps_label.move(20, 20)
        self.fps_label.setStyleSheet("background-color:#33333333;color:white;padding-left:5px;")
        self.fps_sample = 0
        self.last_time = time.time()

    def set_fps(self):
        if self.fps_label is not None:
            self.fps_sample += 1
            if self.fps_sample < self.fps:
                return
            now = time.time()
            delta = now - self.last_time
            self.last_time = now
            self.fps_label.setText(f"FPS: {int(self.fps/delta)}")
            self.fps_sample = 0

    def handle_audio(self, data):
        if self.audio_output is None:
            self.init_audio()
        self.audio_output.write()

    # def resizeEvent(self, event):
    #     self.worker.ctrl.max_width = self.geometry().width()
    #     self.worker.ctrl.max_height = self.geometry().height()
    #     self.video_output.resize(self.geometry().width(), self.geometry().height())
    #     event.accept()

    def keyPressEvent(self, event):
        key = Qt.Key(event.key()).name.decode()
        button = self.mapping.get(key)
        if button is None:
            print(f"Button Invalid: {key}")
            return
        if button == "QUIT":
            self.close()
            return
        if button == "STANDBY":
            message(self, "Standby", "Set host to standby?", level="info", cb=self.send_standby, escape=True)
            return
        if event.isAutoRepeat():
            return
        if "STICK" in button:
            button = button.split("_")
            stick = button[1]
            direction = button[2]
            self.worker.stick_state(stick, direction, 1.0)
        else:
            self.worker.send_button(button, "press")
        event.accept()

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        key = Qt.Key(event.key()).name.decode()
        button = self.mapping.get(key)
        if button is None:
            print(f"Button Invalid: {key}")
            return
        if button in ["QUIT", "STANDBY"]:
            return
        if "STICK" in button:
            button = button.split("_")
            stick = button[1]
            direction = button[2]
            self.worker.stick_state(stick, direction, 0.0)
        else:
            self.worker.send_button(button, "release")
        event.accept()

    def send_standby(self):
        if self.worker.ctrl is not None:
            self.worker.ctrl.standby()

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()

    def cleanup(self):
        print("Cleaning up window")
        self.timer.stop()
        self.thread.quit()
        self.av_thread.quit()
        self.main_window.session_stop()

    def start_timer(self):
        print("AV Processor Started")
        self.timer.start(self.ms_refresh)