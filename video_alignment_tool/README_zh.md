# 视频场景标注工具

这是一个基于 Streamlit 的视频场景标注工具，支持本地视频和云存储视频的场景标注。

## 系统要求

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

1. 首次运行时，选择视频访问模式：
   - 本地视频模式：从本地磁盘加载视频文件
   - 云存储模式：从云存储（如 Google Drive）加载视频

2. 本地视频模式配置：
   - 设置视频目录路径
   - 设置脚本目录路径

3. 云存储模式配置：
   - 设置远程视频文件夹 URL
   - 支持 Google Drive 和其他云存储服务

4. 标注功能：
   - 场景描述验证
   - 交互内容标注
   - 说话人映射确认
   - 添加笔记和反馈

## 快捷键

- 空格键：播放/暂停视频
- D 键：下一个场景

## 常见问题

1. 如果遇到 "No module named 'streamlit'"：
   ```bash
   pip install streamlit
   ```

2. 如果视频无法播放：
   - 检查视频文件路径是否正确
   - 确保视频格式为 MP4
   - 云存储模式下确保有正确的访问权限

3. 如果页面加载缓慢：
   - 检查网络连接
   - 考虑使用本地视频模式
   - 减小视频文件大小

## 项目结构

```
video_scene_verifier/
├── src/
│   └── app.py          # 主应用程序
├── config/             # 配置文件目录
└── requirements.txt    # 依赖包列表
```

## 反馈和支持

如果遇到问题或需要帮助，请：
1. 检查是否正确安装了所有依赖
2. 确认 Python 版本是否符合要求
3. 查看控制台输出的错误信息

## 发布说明

- 版本：1.0.0
- 最后更新：[当前日期]
- 支持平台：Windows、macOS、Linux 