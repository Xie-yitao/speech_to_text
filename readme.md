# 语音翻译器应用程序

## 概述

本项目包含两个版本的语音翻译器应用程序，分别为基于 PyQt5 的桌面端实现和基于 Flask 的 Web 端实现。两个版本均支持实时语音录制、音频文件上传、语音转文本以及文本校正功能。

## 目录结构

```
speech_to_text/
├── qt/          # 桌面端实现
│   ├── speech_translator.py
│   ├── README.md
│   └── LICENSE
|── web/             # Web端实现
    ├── app.py
    ├── static/
    └── templates/
        └── index.html
|── requirements.txt
|── ffmpeg-2025-04-21-git-9e1162bdf1-essentials_build.7z
└── readme.md
```

## 功能特点

- 实时音频录制（支持暂停/继续）
- 音频文件上传
- 语音转文本功能（使用 Whisper）
- 文本校正功能（使用 Qwen API）
- 支持用户自定义校正模型
- 简单易用的用户界面

## 桌面端实现

### 系统要求

- Python 3.10 或更高版本
- PyQt5
- Whisper 库
- PyAudio 库
- OpenAI Python SDK
- Wave 库

### 安装步骤

1. 克隆本项目仓库
2. 安装所需依赖：

```
pip install -r requirements.txt
```

3. 下载 Whisper 模型（您可以在 GUI 中指定要使用的模型），可以在界面中选择，如果没有会自动下载对应模型：

```
python -m whisper --model base --download_dir ./models
```

## 

### 使用方法

1. 进入对应文件目录`cd qt`，启动应用程序：`python speech_translator.py`
2. 在参数字段中输入您的 Qwen API 密钥和基础 URL，建议使用硅基流动，可以免费调用一些基础模型。基础 URL为：https://api.siliconflow.cn/v1
3. 从下拉菜单中选择您偏好的校正模型和语音转文本模型，或者在"Correction Model"字段中输入自定义模型名称
4. 点击“开始录制”按钮开始录制音频
5. 点击“暂停录制”暂停录制，“停止录制”停止录制
6. 录制的音频将保存为“output.wav”
7. 您也可以使用“上传音频”按钮上传音频文件
8. 点击“翻译 & 纠错”按钮处理音频并获取校正后的文本
9. 使用“清空文本”按钮清空显示区域

## Web 端实现

### 系统要求

- Python 3.10 或更高版本
- Flask
- Whisper 库
- OpenAI Python SDK
- PyAudio 库
- Wave 库

### 安装步骤

​	**同桌面端**

### 使用方法

1. 启动 Flask 应用：`python app.py`
2. 在浏览器中访问 `http://127.0.0.1:5000`
3. 在页面中输入您的 Qwen API 密钥和基础 URL
4. 设置参数（可选）：
   - 语音转文本模型（如：tiny, base, small, medium, large）
   - 校正模型（如：Qwen/Qwen2.5-7B-Instruct）
5. 点击“开始录制”按钮开始录制音频
6. 点击“暂停录制”暂停录制，“停止录制”停止录制
7. 点击“上传音频”上传音频文件
8. 点击“翻译 & 纠错”按钮处理音频并获取校正后的文本
9. 点击“清空文本”按钮清空显示区域

## API 配置

您需要获取 Qwen API 密钥并设置相应的基础 URL。API 参数可以在应用程序中输入：

- **API 密钥**：您的 Qwen API 密钥
- **基础 URL**：Qwen API 的基础访问地址
- **校正模型**：从可用的 Qwen 模型中选择或输入自定义模型名称
- **语音转文本模型**：从 Whisper 模型大小中选择（tiny、base、small、medium、large）

## 模型说明

本项目使用 Whisper 进行语音转文本，使用 Qwen API 进行文本校正。您可以选择不同的模型大小以获得不同的准确性/性能平衡。

对于 Whisper 模型：
- `tiny`：最小的模型，速度最快但准确性最低
- `base`：速度和准确性之间的良好平衡
- `small`：比 base 模型更准确
- `medium`：比 small 模型更准确
- `large`：最准确但速度最慢

对于 Qwen 校正模型：
- `Qwen/Qwen2.5-7B-Instruct`：针对指令优化的模型
- `Qwen/Qwen2.5-7B-Chat`：针对对话优化的模型
- **自定义模型**：您可以输入任意有效的模型名称

## 注意事项

- 为获得最佳效果，请在安静的环境中录制
- 应用程序需要互联网连接才能调用 Qwen API
- 如果出现 `FileNotFoundError: [WinError 2] 系统找不到指定的文件。` 错误，请下载 [FFmpeg Essentials Build](https://ffmpeg.org/download.html) 并将其目录添加到环境变量中。

## 开源协议

本项目遵循 MIT 开源协议。有关详细信息，请参阅 LICENSE 文件。