from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import whisper
from openai import OpenAI
import pyaudio
import wave
import keyboard
import threading
import time

app = Flask(__name__)

# 全局变量
recording_flag = False
stream = None
frames = []
chunk = 1024
format = pyaudio.paInt16
channels = 1
rate = 44100
WAVE_OUTPUT_FILENAME = "temp_audio.wav"

# Whisper模型加载
model = None
current_s2t_model = "whisper-base"

# 默认API配置
current_api_key = ''
current_api_base_url = ''
current_model = "Qwen/Qwen2.5-7B-Instruct"

# 初始化PyAudio
p = pyaudio.PyAudio()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_recording', methods=['POST'])
def start_recording():
    global recording_flag, stream, frames
    if not recording_flag:
        recording_flag = True
        frames = []
        def record():
            global recording_flag, stream, frames, chunk
            try:
                if stream is not None:
                    stream.stop_stream()
                    stream.close()
                stream = p.open(format=format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
                while recording_flag:
                    data = stream.read(chunk, exception_on_overflow=False)
                    frames.append(data)
            except Exception as e:
                print("Recording error:", e)
                recording_flag = False
        threading.Thread(target=record).start()
    return jsonify({"status": "recording started"})

@app.route('/pause_recording', methods=['POST'])
def pause_recording():
    global recording_flag
    recording_flag = False
    return jsonify({"status": "recording paused"})

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global recording_flag, stream, frames
    if stream is not None:
        stream.stop_stream()
        stream.close()
        stream = None

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    frames = []
    return jsonify({"status": "recording stopped and saved"})

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if 'audio_file' not in request.files:
        return jsonify({"error": "No file part"})
    file = request.files['audio_file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    if file:
        file.save(WAVE_OUTPUT_FILENAME)
        return jsonify({"status": "file uploaded", "path": WAVE_OUTPUT_FILENAME})

@app.route('/translate', methods=['POST'])
def translate():
    global current_api_key, current_api_base_url, current_model, current_s2t_model
    result = model.transcribe(WAVE_OUTPUT_FILENAME)
    original_text = result["text"]

    client = OpenAI(api_key=current_api_key, base_url=current_api_base_url)
    response = client.chat.completions.create(
        model=current_model,
        messages=[
            {'role': 'system', 'content': '你是一个专业的文本纠错助手，擅长纠正错别字和语法错误。'},
            {'role': 'user', 'content': '我有一段文本需要纠正错别字和语法错误。'},
            {'role': 'assistant', 'content': '好的，请提供需要纠正的文本。'},
            {'role': 'user', 'content': f"需要纠正的文本是：{original_text}"}
        ],
        stream=True
    )

    corrected_text = ""
    for chunk in response:
        if not chunk.choices:
            continue
        if chunk.choices[0].delta.content:
            corrected_text += chunk.choices[0].delta.content

    return jsonify({
        "original_text": original_text,
        "corrected_text": corrected_text
    })

@app.route('/set_parameters', methods=['POST'])
def set_parameters():
    global current_api_key, current_api_base_url, current_model, current_s2t_model
    data = request.get_json()
    current_api_key = data.get('api_key', current_api_key)
    current_api_base_url = data.get('api_base_url', current_api_base_url)
    current_model = data.get('model', current_model)
    current_s2t_model = data.get('s2t_model', current_s2t_model)
    
    # 加载语音转文字模型
    global model
    model = whisper.load_model(current_s2t_model.split('-')[-1], download_root='./models')
    return jsonify({"status": "parameters set"})

@app.route('/clear_text', methods=['POST'])
def clear_text():
    return jsonify({"status": "text cleared", "original_text": "", "corrected_text": ""})

if __name__ == '__main__':
    app.run(debug=True)