# 视频场景标注工具

这是一个基于 Streamlit 的视频场景标注工具，支持本地视频和云存储视频的场景标注。

## 环境要求

- Python 3.10 或更高版本
- pip 或 conda 包管理器

## 安装步骤

1. 创建并激活虚拟环境（推荐）：

```bash
# 使用 conda
conda create -n video_scene python=3.10
conda activate video_scene

# 或使用 venv
python -m venv video_scene
# Windows
.\video_scene\Scripts\activate
# Linux/Mac
source video_scene/bin/activate
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
cd src
streamlit run app.py
```

应用将在浏览器中自动打开，默认地址为：http://localhost:8501

## 使用说明

### 基本配置

1. 首次运行时，选择视频访问模式：
   - 本地视频模式：从本地磁盘加载视频文件
   - 云存储模式：从云存储（如 Google Drive）加载视频

2. 本地视频模式配置：
   - 设置视频目录路径
   - 设置脚本目录路径

3. 云存储模式配置：
   - 设置远程视频文件夹 URL
   - 支持 Google Drive 和其他云存储服务

### 标注功能

1. 场景描述验证
   - 检查并确认每个场景的描述准确性
   - 标注场景的开始和结束时间

2. 交互内容标注
   - 记录场景中的对话内容
   - 标注重要的视觉线索

3. 说话人映射确认
   - 识别并记录场景中的说话人
   - 确认说话人与对话的对应关系

4. 笔记和反馈
   - 添加场景相关的备注
   - 记录标注过程中的问题或建议

### 快捷键

- 空格键：播放/暂停视频
- D 键：下一个场景

## 目录结构

```
video_scene_verifier/
├── src/
│   └── app.py          # 主应用程序
├── config/             # 配置文件目录
└── requirements.txt    # 依赖包列表
```

## 工具界面预览

![视频场景标注工具截图](video_verifier.png) 