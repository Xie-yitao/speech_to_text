import sys
import os
import wave
import threading
import pyaudio
import whisper
from openai import OpenAI
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QFileDialog, QComboBox, QLabel, QLineEdit
)
from PyQt5.QtCore import pyqtSignal, QObject


# 信号类，用于线程间通信
class WorkerSignals(QObject):
    # 定义两个信号，分别用于通知转录完成和校正完成
    transcription_ready = pyqtSignal(str)
    correction_ready = pyqtSignal(str)


# 音频录制工作线程
class AudioRecorder(threading.Thread):
    def __init__(self, signals, api_params):
        super().__init__()
        self.signals = signals  # 用于发送信号通知主线程
        self.api_params = api_params  # API 参数
        self._running = False  # 录制状态标志
        self._paused = False  # 暂停状态标志
        self.frames = []  # 存储音频数据帧
        # 音频录制参数
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.OUTPUT_FILENAME = "output.wav"
        self.p = pyaudio.PyAudio()  # 音频流对象

    def run(self):
        # 打开音频流
        stream = self.p.open(format=self.FORMAT,
                             channels=self.CHANNELS,
                             rate=self.RATE,
                             input=True,
                             frames_per_buffer=self.CHUNK)
        self._running = True
        while self._running:
            if self._paused:
                continue  # 如果处于暂停状态，则跳过录制
            data = stream.read(self.CHUNK, exception_on_overflow=False)
            self.frames.append(data)  # 将录制的数据帧添加到列表中
        # 录制结束，关闭音频流
        stream.stop_stream()
        stream.close()
        self.p.terminate()
        # 保存音频文件
        wf = wave.open(self.OUTPUT_FILENAME, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        # 触发转录和校正流程
        self.transcribe_and_correct(self.OUTPUT_FILENAME)

    def pause(self):
        self._paused = True  # 设置暂停标志

    def resume(self):
        self._paused = False  # 清除暂停标志

    def stop(self):
        self._running = False  # 设置停止标志

    def transcribe_and_correct(self, filepath):
        # 加载 Whisper 模型
        stt_model_name = self.api_params['stt_model']
        model = whisper.load_model(stt_model_name, download_root=self.api_params['cache_dir'])
        result = model.transcribe(filepath)
        text = result['text']
        self.signals.transcription_ready.emit(text)  # 发送转录完成信号
        # 使用 Qwen API 进行文本校正
        client = OpenAI(api_key=self.api_params['api_key'], base_url=self.api_params['base_url'])
        messages = [
            {'role':'system','content':'你是一个专业的文本纠错助手。'},
            {'role':'user','content':f"需要纠正的文本是：{text}"}
        ]
        response = client.chat.completions.create(
            model=self.api_params['correction_model'], messages=messages
        )
        corrected = response.choices[0].message.content
        self.signals.correction_ready.emit(corrected)  # 发送校正完成信号


# 主窗口类
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speech Translator")
        self.signals = WorkerSignals()  # 创建信号对象
        # 连接信号到槽函数
        self.signals.transcription_ready.connect(self.on_transcription)
        self.signals.correction_ready.connect(self.on_correction)
        self.recorder = None  # 音频录制线程对象
        # 初始化 API 参数
        self.api_params = {
            'api_key':'', 
            'base_url':'', 
            'correction_model':'Qwen/Qwen2.5-7B-Instruct', 
            'stt_model':'base', 
            'cache_dir':'./models'
        }
        self._init_ui()  # 初始化 UI

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        # 参数输入布局
        param_layout = QHBoxLayout()
        # API 密钥输入
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("API Key")
        # 基础 URL 输入
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("Base URL")
        # 校正模型选择
        self.corr_combo = QComboBox()
        self.corr_combo.setEditable(True)  # 设置为可编辑模式
        self.corr_combo.addItems(["Qwen/Qwen2.5-7B-Instruct", "Qwen/Qwen2.5-7B-Chat", "自定义..."])
        # 语音识别模型选择
        self.stt_combo = QComboBox()
        self.stt_combo.addItems(["tiny","base","small","medium","large"])
        
        # 添加标签和输入控件到参数布局
        param_layout.addWidget(QLabel("API Key:"))
        param_layout.addWidget(self.api_input)
        param_layout.addWidget(QLabel("Base URL:"))
        param_layout.addWidget(self.base_url_input)
        param_layout.addWidget(QLabel("Correction Model:"))
        param_layout.addWidget(self.corr_combo)
        param_layout.addWidget(QLabel("STT Model:"))
        param_layout.addWidget(self.stt_combo)
        layout.addLayout(param_layout)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始录制")
        self.pause_btn = QPushButton("暂停录制")
        self.stop_btn = QPushButton("停止录制")
        self.upload_btn = QPushButton("上传音频")
        self.translate_btn = QPushButton("翻译 & 纠错")
        self.clear_btn = QPushButton("清空文本")  # 清空文本按钮
        
        # 添加按钮到按钮布局
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.upload_btn)
        btn_layout.addWidget(self.translate_btn)
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)
        
        # 文本显示区域
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        layout.addWidget(self.text_display)
        
        central.setLayout(layout)
        
        # 连接按钮点击事件到槽函数
        self.start_btn.clicked.connect(self.start_record)
        self.pause_btn.clicked.connect(self.pause_record)
        self.stop_btn.clicked.connect(self.stop_record)
        self.upload_btn.clicked.connect(self.upload_file)
        self.translate_btn.clicked.connect(self.translate)
        self.clear_btn.clicked.connect(self.clear_text)

    def start_record(self):
        if self.recorder and self.recorder.is_alive():
            self.recorder.resume()  # 如果录制已暂停，则恢复录制
        else:
            self.update_params()  # 更新参数
            self.recorder = AudioRecorder(self.signals, self.api_params)
            self.recorder.start()  # 启动录制线程
        self.text_display.append("录制中...")

    def pause_record(self):
        if self.recorder:
            self.recorder.pause()  # 暂停录制
            self.text_display.append("已暂停录制")

    def stop_record(self):
        if self.recorder:
            self.recorder.stop()  # 停止录制
            self.text_display.append("录制停止，文件保存至 output.wav")

    def upload_file(self):
        # 打开文件对话框选择音频文件
        path, _ = QFileDialog.getOpenFileName(self, "选择音频文件", "", "Audio Files (*.wav *.mp3 *.m4a)")
        if path:
            self.uploaded = path  # 保存上传的文件路径
            self.text_display.append(f"已上传文件: {path}")

    def translate(self):
        self.update_params()  # 更新参数
        target = getattr(self, 'uploaded', 'output.wav')  # 获取目标音频文件
        
        if not hasattr(self, 'recorder') or self.recorder is None or not self.recorder.is_alive():
            # 创建一个临时的 Recorder 用于处理转录和校正
            self.recorder = AudioRecorder(self.signals, self.api_params)
        
        # 在单独的线程中执行转录和校正
        threading.Thread(target=self.recorder.transcribe_and_correct, args=(target,)).start()
        self.text_display.append("翻译 & 纠错处理中...")

    def update_params(self):
        # 更新 API 参数
        self.api_params['api_key'] = self.api_input.text()
        self.api_params['base_url'] = self.base_url_input.text()
        
        # 获取校正模型名称（支持用户自定义）
        correction_model = self.corr_combo.currentText()
        if correction_model == "自定义...":
            correction_model = self.corr_combo.lineEdit().text()  # 获取用户输入的自定义模型
        self.api_params['correction_model'] = correction_model
        
        self.api_params['stt_model'] = self.stt_combo.currentText()

    def on_transcription(self, text):
        # 显示转录结果
        self.text_display.append("原文: \n" + text)

    def on_correction(self, text):
        # 显示校正结果
        self.text_display.append("纠错后: \n" + text)

    def clear_text(self):
        """清空文本显示区域"""
        self.text_display.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())