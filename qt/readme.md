# 语音翻译器图形界面应用程序

## 概述

这是一个具有图形用户界面的桌面应用程序，用于实时语音翻译和校正。它允许用户录制音频、上传音频文件，并使用 Whisper 模型和 Qwen API 进行语音转文本与文本校正。程序经过更新，现在支持用户自定义校正模型。

## 功能特点

- 实时音频录制（支持暂停/继续）
- 音频文件上传
- 语音转文本功能（使用 Whisper）
- 文本校正功能（使用 Qwen API）
- 支持用户自定义校正模型
- 简单易用的图形界面

## 系统要求

- Python 3.10 或更高版本
- PyQt5
- Whisper 库
- PyAudio 库
- OpenAI Python SDK
- Wave 库

## 安装步骤

1. 克隆本项目仓库
2. 安装所需依赖：
python=3.10.17
```
pip install -r requirements.txt
```

3. 下载 Whisper 模型（您可以在 GUI 中指定要使用的模型）：

```
python -m whisper --model base --download_dir ./models
```

## 使用方法

1. 启动应用程序
2. 在参数字段中输入您的 Qwen API 密钥和基础 URL
3. 从下拉菜单中选择您偏好的校正模型和语音转文本模型，或者在"Correction Model"字段中输入自定义模型名称
4. 点击“开始录制”按钮开始录制音频
5. 点击“暂停录制”暂停录制，“停止录制”停止录制
6. 录制的音频将保存为“output.wav”
7. 您也可以使用“上传音频”按钮上传音频文件
8. 点击“翻译 & 纠错”按钮处理音频并获取校正后的文本
9. 使用“清空文本”按钮清空显示区域

## API 配置

您需要获取 Qwen API 密钥并设置相应的基础 URL。API 参数可以在 GUI 中输入：

- **API 密钥**：您的 Qwen API 密钥
- **基础 URL**：Qwen API 的基础访问地址
- **校正模型**：从可用的 Qwen 模型中选择或输入自定义模型名称
- **语音转文本模型**：从 Whisper 模型大小中选择（tiny、base、small、medium、large）

## 模型说明

本应用使用 Whisper 进行语音转文本，使用 Qwen API 进行文本校正。您可以选择不同的模型大小以获得不同的准确性/性能平衡。

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

- 确保您已下载所需的 Whisper 模型
- 为获得最佳效果，请在安静的环境中录制
- 应用程序需要互联网连接才能调用 Qwen API
- 音频文件必须为 WAV 格式才能获得最佳处理效果
- 如出现`FileNotFoundError: [WinError 2] 系统找不到指定的文件。`错误请下载`ffmpeg-2025-04-21-git-9e1162bdf1-essentials_build.7z`解压并加入环境变量中。



## 开源协议

本项目遵循 MIT 开源协议。有关详细信息，请参阅 LICENSE 文件。