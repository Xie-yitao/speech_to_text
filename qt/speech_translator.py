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

# Ensure dependencies are installed
try:
    import whisper
except ImportError as e:
    print("Missing module detected. Please ensure 'whisper' and its dependencies are installed.")
    sys.exit(1)

# Worker signals
class WorkerSignals(QObject):
    transcription_ready = pyqtSignal(str)
    correction_ready = pyqtSignal(str)

# Audio Recorder Worker
class AudioRecorder(threading.Thread):
    def __init__(self, signals, api_params):
        super().__init__()
        self.signals = signals
        self.api_params = api_params
        self._running = False
        self._paused = False
        self.frames = []
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.OUTPUT_FILENAME = "output.wav"
        self.p = pyaudio.PyAudio()

    def run(self):
        stream = self.p.open(format=self.FORMAT,
                             channels=self.CHANNELS,
                             rate=self.RATE,
                             input=True,
                             frames_per_buffer=self.CHUNK)
        self._running = True
        while self._running:
            if self._paused:
                continue
            data = stream.read(self.CHUNK, exception_on_overflow=False)
            self.frames.append(data)
        stream.stop_stream()
        stream.close()
        self.p.terminate()
        # save
        wf = wave.open(self.OUTPUT_FILENAME, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        # trigger transcription
        self.transcribe_and_correct(self.OUTPUT_FILENAME)

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._running = False

    def transcribe_and_correct(self, filepath):
        # load whisper model
        stt_model_name = self.api_params['stt_model']
        model = whisper.load_model(stt_model_name, download_root=self.api_params['cache_dir'])
        result = model.transcribe(filepath)
        text = result['text']
        self.signals.transcription_ready.emit(text)
        # correct via Qwen
        client = OpenAI(api_key=self.api_params['api_key'], base_url=self.api_params['base_url'])
        messages = [
            {'role':'system','content':'你是一个专业的文本纠错助手。'},
            {'role':'user','content':f"需要纠正的文本是：{text}"}
        ]
        response = client.chat.completions.create(
            model=self.api_params['correction_model'], messages=messages
        )
        corrected = response.choices[0].message.content
        self.signals.correction_ready.emit(corrected)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speech Translator")
        self.signals = WorkerSignals()
        self.signals.transcription_ready.connect(self.on_transcription)
        self.signals.correction_ready.connect(self.on_correction)
        self.recorder = None
        self.api_params = {'api_key':'', 'base_url':'', 'correction_model':'Qwen/Qwen2.5-7B-Instruct', 'stt_model':'base', 'cache_dir':'./models'}
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        # parameter inputs
        param_layout = QHBoxLayout()
        self.api_input = QLineEdit(); self.api_input.setPlaceholderText("API Key")
        self.base_url_input = QLineEdit(); self.base_url_input.setPlaceholderText("Base URL")
        self.corr_combo = QComboBox(); self.corr_combo.addItems(["Qwen/Qwen2.5-7B-Instruct", "Qwen/Qwen2.5-7B-Chat"])
        self.stt_combo = QComboBox(); self.stt_combo.addItems(["tiny","base","small","medium","large"])
        param_layout.addWidget(QLabel("API Key:")); param_layout.addWidget(self.api_input)
        param_layout.addWidget(QLabel("Base URL:")); param_layout.addWidget(self.base_url_input)
        param_layout.addWidget(QLabel("Correction Model:")); param_layout.addWidget(self.corr_combo)
        param_layout.addWidget(QLabel("STT Model:")); param_layout.addWidget(self.stt_combo)
        layout.addLayout(param_layout)
        # buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始录制")
        self.pause_btn = QPushButton("暂停录制")
        self.stop_btn = QPushButton("停止录制")
        self.upload_btn = QPushButton("上传音频")
        self.translate_btn = QPushButton("翻译 & 纠错")
        self.clear_btn = QPushButton("清空文本")  # 添加清空文本按钮
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.upload_btn)
        btn_layout.addWidget(self.translate_btn)
        btn_layout.addWidget(self.clear_btn)  # 将清空按钮添加到按钮布局
        layout.addLayout(btn_layout)
        # text display
        self.text_display = QTextEdit(); self.text_display.setReadOnly(True)
        layout.addWidget(self.text_display)
        central.setLayout(layout)
        # connect
        self.start_btn.clicked.connect(self.start_record)
        self.pause_btn.clicked.connect(self.pause_record)
        self.stop_btn.clicked.connect(self.stop_record)
        self.upload_btn.clicked.connect(self.upload_file)
        self.translate_btn.clicked.connect(self.translate)
        self.clear_btn.clicked.connect(self.clear_text)  # 连接清空文本按钮到清空方法

    def start_record(self):
        if self.recorder and self.recorder.is_alive():
            self.recorder.resume()
        else:
            self.update_params()
            self.recorder = AudioRecorder(self.signals, self.api_params)
            self.recorder.start()
        self.text_display.append("录制中...")

    def pause_record(self):
        if self.recorder:
            self.recorder.pause()
            self.text_display.append("已暂停录制")

    def stop_record(self):
        if self.recorder:
            self.recorder.stop()
            self.text_display.append("录制停止，文件保存至 output.wav")

    def upload_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择音频文件", "", "Audio Files (*.wav *.mp3 *.m4a)")
        if path:
            self.uploaded = path
            self.text_display.append(f"已上传文件: {path}")

    def translate(self):
        self.update_params()
        target = getattr(self, 'uploaded', 'output.wav')

        if not hasattr(self, 'recorder') or self.recorder is None or not self.recorder.is_alive():
            # 创建一个临时的 Recorder 仅用于调用 transcribe_and_correct
            self.recorder = AudioRecorder(self.signals, self.api_params)

        # 启动线程执行转录和纠错
        threading.Thread(target=self.recorder.transcribe_and_correct, args=(target,)).start()
        self.text_display.append("翻译 & 纠错处理中...")

    def update_params(self):
        self.api_params['api_key'] = self.api_input.text()
        self.api_params['base_url'] = self.base_url_input.text()
        self.api_params['correction_model'] = self.corr_combo.currentText()
        self.api_params['stt_model'] = self.stt_combo.currentText()

    def on_transcription(self, text):
        self.text_display.append("原文: \n" + text)

    def on_correction(self, text):
        self.text_display.append("纠错后: \n" + text)

    def clear_text(self):
        """清空文本显示区域"""
        self.text_display.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())