# SpeechSynthSubs

SpeechSynthSubs is a Python application that converts text into spoken audio and synchronizes it with subtitles. It utilizes Google's Text-to-Speech API for audio synthesis and the `pysubs2` library to create subtitle files in the `.srt` format.

## Prerequisites

Before you can use SpeechSynthSubs, make sure you have:

- Python 3.x installed
- A Google Cloud Platform account with billing enabled, to use the Google Text-to-Speech API.

## Installation
   ```bash
git clone https://github.com/hesic73/SpeechSynthSubs.git
cd SpeechSynthSubs
pip install -r requirements.txt
   ```

### Set up the Google Cloud Text-to-Speech API

- Follow Google's guide to set up an API key or service account.

- Ensure the API key is accessible as an environment variable:

```bash
export GOOGLE_TTS_API_KEY='your_api_key_here'
```

## Usage

The tool supports input either via a text file or directly as a string:

```bash
python main.py -f path/to/your/file.txt
python main.py -t "Your text string here."
```

This will generate an audio file (`output.mp3`) and a subtitle file (`subtitles.srt`) in a directory under `runs/` labeled with the current timestamp.

## Example

### Input Text

```
Python是一种广泛使用的解释型、高级和通用的编程语言。Python支持多种编程范型，包括结构化、过程式、反射式、面向对象和函数式编程。它拥有动态类型系统和垃圾回收功能，能够自动管理内存使用，并且其本身拥有一个巨大而广泛的标准库。它的语言结构以及面向对象的方法，旨在帮助程序员为小型的和大型的项目编写逻辑清晰的代码。
```

### Generated SSML

```
<speak>Python是一种广泛使用的解释型、高级和通用的编程语言<mark name="mark_0"/>。Python支持多种编程范型<mark name="mark_1"/>，包括结构化、过程式、反射式、面向对象和函数式编程<mark name="mark_2"/>。它拥有动态类型系统和垃圾回收功能<mark name="mark_3"/>，能够自动管理内存使用<mark name="mark_4"/>，并且其本身拥有一个巨大而广泛的标准库<mark name="mark_5"/>。它的语言结构以及面向对象的方法<mark name="mark_6"/>，旨在帮助程序员为小型的和大型的项目编写逻辑清晰的代码<mark name="mark_7"/>。</speak>
```

### Subtitles (.srt)

```
1
00:00:00,000 --> 00:00:04,500
Python是一种广泛使用的解释型、高级和通用的编程语言

2
00:00:04,500 --> 00:00:07,287
Python支持多种编程范型

3
00:00:07,287 --> 00:00:12,017
包括结构化、过程式、反射式、面向对象和函数式编程

4
00:00:12,017 --> 00:00:15,849
它拥有动态类型系统和垃圾回收功能

5
00:00:15,849 --> 00:00:17,929
能够自动管理内存使用

6
00:00:17,929 --> 00:00:21,485
并且其本身拥有一个巨大而广泛的标准库

7
00:00:21,485 --> 00:00:24,891
它的语言结构以及面向对象的方法

8
00:00:24,891 --> 00:00:29,810
旨在帮助程序员为小型的和大型的项目编写逻辑清晰的代码
```

### Audio Output



## Limitations

- The tool may incorrectly segment sentences when converting text to SSML, either breaking where it shouldn't or failing to break where necessary.

## Appendix

- Supported Chinese Voices:https://cloud.google.com/text-to-speech/docs/voices

| Language         | Voice type | Language code | Voice name        | SSML gender |
| ---------------- | ---------- | ------------- | ----------------- | ----------- |
| Mandarin Chinese | Standard   | cmn-CN        | cmn-CN-Standard-A | FEMALE      |
| Mandarin Chinese | Standard   | cmn-CN        | cmn-CN-Standard-B | MALE        |
| Mandarin Chinese | Standard   | cmn-CN        | cmn-CN-Standard-C | MALE        |
| Mandarin Chinese | Standard   | cmn-CN        | cmn-CN-Standard-D | FEMALE      |
| Mandarin Chinese | Premium    | cmn-CN        | cmn-CN-Wavenet-A  | FEMALE      |
| Mandarin Chinese | Premium    | cmn-CN        | cmn-CN-Wavenet-B  | MALE        |
| Mandarin Chinese | Premium    | cmn-CN        | cmn-CN-Wavenet-C  | MALE        |
| Mandarin Chinese | Premium    | cmn-CN        | cmn-CN-Wavenet-D  | FEMALE      |