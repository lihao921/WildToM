import streamlit as st
import streamlit.components.v1 as components
import json
import os
from pathlib import Path
import time
import re
import pandas as pd
import cv2
# from gdrive_utils import list_videos_in_folder, get_gdrive_service

# 添加模式选择和视频处理功能
VIDEO_MODE_LOCAL = "本地视频模式"
VIDEO_MODE_CLOUD = "云存储模式"

# 定义默认路径
DEFAULT_VIDEO_DIR = r"G:\Phd\datasets\videoQA\social-IQ2.0\Social-IQ-2.0-Challenge-main\siq2\siq2\siq_full\video\videos_trainval_tom"
DEFAULT_QA_DIR = r"J:\Code\paper3\data\5_agent_emody\Multi-Agents-Debate-main\multimodal_agent_omni_mc\5.1_auto_filtering\filtering_results_with_speaker_mapping\feedback_1"
DEFAULT_CAPTION_DIR = r"J:\Code\paper3\data\4_global_speaker_alignment\output\gpt_captions_nano"



# 在文件开头的全局变量区域添加状态常量
QUESTION_STATUS_PENDING = "pending"
QUESTION_STATUS_KEPT = "kept"
QUESTION_STATUS_DELETED = "deleted"

def load_video_mapping():
    """加载视频ID到URL的映射"""
    mapping_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'video_mapping.json')
    if os.path.exists(mapping_file):
        # 尝试不同的编码方式
        encodings = ['utf-8', 'utf-8-sig', 'utf-16', 'latin1']
        for encoding in encodings:
            try:
                with open(mapping_file, 'r', encoding=encoding) as f:
                    data = json.load(f)
                    
                    # 检查映射文件的有效性和过期时间
                    if 'metadata' in data:
                        # 检查文件夹URL是否匹配
                        if 'folder_url' in data['metadata']:
                            current_folder = st.session_state.get('remote_folder', '')
                            if current_folder and current_folder != data['metadata']['folder_url']:
                                # 如果文件夹URL不匹配，返回空映射
                                return {}
                        
                        # 检查映射是否过期（默认30天）
                        if 'created_at' in data['metadata']:
                            created_at = time.strptime(data['metadata']['created_at'], "%Y-%m-%d")
                            current_time = time.localtime()
                            # 计算天数差
                            days_diff = (time.mktime(current_time) - time.mktime(created_at)) / (24 * 60 * 60)
                            if days_diff > 30:  # 如果映射超过30天
                                return {}
                    
                    # 成功读取后，重新以utf-8保存
                    with open(mapping_file, 'w', encoding='utf-8') as fw:
                        json.dump(data, fw, indent=2, ensure_ascii=False)
                    return data.get('video_mappings', {})
            except Exception as e:
                continue
        
        # 如果所有编码都失败了，创建新文件
        try:
            default_data = {
                "metadata": {
                    "version": "1.0",
                    "created_at": time.strftime("%Y-%m-%d"),
                    "folder_url": st.session_state.get('remote_folder', ''),
                    "file_count": 0
                },
                "video_mappings": {}
            }
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
            return {}
        except Exception as e:
            st.error(f"创建新的映射文件失败: {str(e)}")
            return {}
    
    return {}

def save_video_mapping(mapping, mode=VIDEO_MODE_CLOUD):
    """
    保存视频ID到URL的映射
    Args:
        mapping: 视频ID到URL的映射字典
        mode: 视频访问模式 (VIDEO_MODE_CLOUD 或 VIDEO_MODE_LOCAL)
    """
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    os.makedirs(config_dir, exist_ok=True)
    mapping_file = os.path.join(config_dir, 'video_mapping.json')
    try:
        # 清理和标准化映射
        cleaned_mapping = {}
        for video_id, url in mapping.items():
            if 'drive.google.com' in url:
                try:
                    # 提取文件ID
                    if 'file/d/' in url:
                        file_id = url.split('file/d/')[1].split('/')[0]
                    elif 'id=' in url:
                        file_id = url.split('id=')[1].split('&')[0]
                    else:
                        continue
                    
                    # 根据模式生成不同的URL格式
                    if mode == VIDEO_MODE_CLOUD:
                        cleaned_mapping[video_id] = f"https://drive.google.com/file/d/{file_id}/preview"
                    else:
                        cleaned_mapping[video_id] = f"https://drive.google.com/uc?id={file_id}&export=download"
                except Exception:
                    continue
            else:
                cleaned_mapping[video_id] = url
        
        data = {
            "metadata": {
                "version": "1.0",
                "created_at": time.strftime("%Y-%m-%d"),
                "folder_url": st.session_state.get('remote_folder', ''),
                "file_count": len(cleaned_mapping),
                "is_complete": len(cleaned_mapping) >= 588  # 标记是否为完整映射
            },
            "video_mappings": cleaned_mapping
        }
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"保存视频映射失败: {str(e)}")
        return False

def convert_gdrive_link_to_direct(url: str) -> str:
    """将Google Drive链接转换为直接下载链接"""
    # 从文件夹链接中提取ID
    if 'folders' in url:
        folder_id = url.split('folders/')[1].split('?')[0].split('/')[0]
        return f"https://drive.google.com/uc?id={folder_id}"
    # 从文件链接中提取ID
    elif 'file/d/' in url:
        file_id = url.split('file/d/')[1].split('/')[0]
        return f"https://drive.google.com/uc?id={file_id}&export=download"
    return url

def get_video_path(video_id, mode):
    """根据所选模式获取视频路径"""
    if mode == VIDEO_MODE_LOCAL:
        # 本地模式
        video_dir = st.session_state.get('video_dir', DEFAULT_VIDEO_DIR)
        return os.path.join(video_dir, f"{video_id}.mp4")
    else:
        # 云存储模式
        # 首先检查是否有远程文件夹URL
        if 'remote_folder' not in st.session_state:
            st.session_state.remote_folder = ""
            
        remote_folder = st.session_state.remote_folder
        
        if not remote_folder:
            st.error("未设置远程文件夹URL")
            st.error("请点击'云存储设置'按钮设置远程文件夹URL")
            return ""
            
        # 加载视频映射
        video_mapping = load_video_mapping()
        
        # 如果视频ID在映射中，直接使用映射的URL
        if video_id in video_mapping:
            url = video_mapping[video_id]
            # 如果是Google Drive链接，确保格式正确
            if 'drive.google.com' in url:
                try:
                    # 提取文件ID
                    file_id = None
                    if '/file/d/' in url:
                        file_id = url.split('/file/d/')[1].split('/')[0]
                    elif 'id=' in url:
                        file_id = url.split('id=')[1].split('&')[0]
                    elif 'export=download' in url:
                        file_id = url.split('id=')[1].split('&')[0]
                    
                    if not file_id:
                        st.error(f"无效的Google Drive URL格式: {url}")
                        return ""
                    
                    # 使用直接下载链接，因为Streamlit视频播放器需要直接的视频URL
                    final_url = f"https://drive.google.com/uc?id={file_id}&export=download"
                    return final_url
                except Exception as e:
                    st.error(f"转换视频URL时出错: {str(e)}")
                    return url
            return url
            
        # 如果视频ID不在映射中，且映射为空，尝试从Google Drive获取
        if not video_mapping and 'drive.google.com' in remote_folder:
            try:
                # 从文件夹URL中提取文件夹ID
                folder_id = remote_folder.split('folders/')[1].split('?')[0].split('/')[0]
                # 获取文件夹中的所有视频
                new_mapping = list_videos_in_folder(folder_id, 'cloud' if mode == VIDEO_MODE_CLOUD else 'local')
                
                # 检查是否获取到了预期的文件数量（588个文件）
                if new_mapping and len(new_mapping) > 0:
                    # 更新并保存映射
                    video_mapping.update(new_mapping)
                    save_video_mapping(video_mapping, mode=mode)
                    st.success("已自动更新视频映射")
                    st.rerun()
            except Exception as e:
                st.error(f"自动获取视频映射时出错: {str(e)}")
        
        # 如果是其他云存储服务，或者视频ID不在映射中
        if 'drive.google.com' in remote_folder:
            st.error(f"视频 {video_id} 未在Google Drive映射中找到。")
            return ""
        else:
            # 其他云存储服务，构建直接URL
            if not remote_folder.endswith('/'):
                remote_folder += '/'
            video_url = f"{remote_folder}{video_id}.mp4"
            
            # 保存新的映射
            video_mapping[video_id] = video_url
            save_video_mapping(video_mapping, mode=mode)
            
            return video_url

def test_gdrive_connection(folder_id):
    """测试Google Drive文件夹连接"""
    try:
        service = get_gdrive_service()
        # 尝试列出文件夹内容
        query = f"'{folder_id}' in parents"
        results = service.files().list(q=query, pageSize=1, fields="files(id, name)").execute()
        files = results.get('files', [])
        if files:
            return True, f"连接成功！找到 {len(files)} 个文件。"
        else:
            return True, "连接成功，但文件夹为空。"
    except Exception as e:
        return False, f"连接失败: {str(e)}"

def show_cloud_storage_settings():
    """显示云存储设置界面"""
    st.subheader("云存储设置")
    
    # 显示返回按钮
    if st.button("← 返回主界面"):
        st.session_state.show_settings = False
        st.rerun()
        
    # 显示远程文件夹设置
    st.markdown("### 远程视频文件夹设置")
    st.markdown("""
    请输入存放视频文件的远程文件夹URL。例如：
    - Google Drive文件夹分享链接 (https://drive.google.com/drive/folders/...)
    - 其他云存储服务的文件夹URL
    
    **注意：**
    1. 对于Google Drive：
       - 确保文件夹已设置为"任何人都可以查看"
       - 直接粘贴文件夹的分享链接即可
    2. 对于其他云存储：
       - 确保URL可以直接访问视频文件
       - URL应该以斜杠(/)结尾
    3. 视频文件名应该为"视频ID.mp4"格式
    """)
    
    # 使用form来确保设置被正确保存
    with st.form("cloud_storage_settings"):
        new_folder = st.text_input(
            "远程文件夹URL",
            value=st.session_state.get('remote_folder', ''),
            help="输入存放所有视频文件的远程文件夹URL"
        )
        
        submitted = st.form_submit_button("保存文件夹设置", type="primary")
        if submitted and new_folder:
            if new_folder != st.session_state.get('remote_folder', ''):
                st.session_state.remote_folder = new_folder
                # 清除现有映射，强制重新获取
                save_video_mapping({}, mode=st.session_state.video_mode)
                st.success("设置已保存！将重新获取视频映射。")
            else:
                st.success("设置已保存！")
            # 不要立即返回主界面，让用户可以看到保存成功的消息
    
    # 显示当前设置
    if st.session_state.get('remote_folder'):
        st.info(f"当前远程文件夹: {st.session_state.remote_folder}")
        if 'drive.google.com' in st.session_state.remote_folder:
            st.info("已检测到Google Drive链接，将根据当前模式处理视频访问")
    
    # 显示当前的视频映射
    video_mapping = load_video_mapping()
    if video_mapping:
        st.markdown("### 当前视频映射")
        st.markdown("以下是已保存的视频ID到URL的映射：")
        for video_id, url in video_mapping.items():
            st.code(f"{video_id}: {url}")
        
        if st.button("清除所有视频映射"):
            save_video_mapping({}, mode=st.session_state.video_mode)
            st.success("已清除所有视频映射！")
            st.rerun()
    
    # 添加单个视频映射的功能
    st.markdown("### 添加/更新单个视频映射")
    with st.form("add_video_mapping"):
        col1, col2 = st.columns(2)
        with col1:
            video_id = st.text_input("视频ID")
        with col2:
            video_url = st.text_input("视频URL")
            
        submitted = st.form_submit_button("添加/更新映射")
        if submitted and video_id and video_url:
            # 如果是Google Drive链接，根据当前模式处理
            if 'drive.google.com' in video_url:
                video_mapping[video_id] = video_url
                if save_video_mapping(video_mapping, mode=st.session_state.video_mode):
                    st.success(f"已添加/更新视频 {video_id} 的映射！")
                    st.rerun()
    
    # 自动生成Google Drive视频映射按钮
    if st.session_state.get('remote_folder') and 'drive.google.com' in st.session_state['remote_folder']:
        if st.button("自动生成Google Drive视频映射"):
            match = re.search(r'folders/([a-zA-Z0-9_-]+)', st.session_state['remote_folder'])
            if match:
                folder_id = match.group(1)
                # 根据当前模式获取视频映射
                mapping = list_videos_in_folder(folder_id, 'cloud' if st.session_state.video_mode == VIDEO_MODE_CLOUD else 'local')
                if save_video_mapping(mapping, mode=st.session_state.video_mode):
                    st.success("已自动生成所有视频映射！")
                    st.rerun()
            else:
                st.error("无法识别Google Drive文件夹ID")

# Custom HTML and JavaScript for keyboard shortcuts and video control
CUSTOM_JS = """
<script>
// Google Drive Player API
let player = null;

function onYouTubeIframeAPIReady() {
    // This function will be called when the API is ready
    setupGDrivePlayer();
}

function setupGDrivePlayer() {
    const iframe = document.querySelector('iframe');
    if (iframe && iframe.src.includes('drive.google.com')) {
        // Add necessary event listener for iframe load
        iframe.addEventListener('load', function() {
            // Initialize player once iframe is loaded
            player = new YT.Player(iframe, {
                events: {
                    'onReady': onPlayerReady,
                    'onStateChange': onPlayerStateChange
                }
            });
        });
    }
}

function onPlayerReady(event) {
    // Player is ready
    console.log('Player ready');
    // If we have a start time, seek to it
    if (window.startTime) {
        seekToTime(window.startTime);
    }
}

function onPlayerStateChange(event) {
    // Monitor player state changes
    if (event.data == YT.PlayerState.PLAYING) {
        // Video is playing
        if (window.endTime) {
            // Check time periodically
            setInterval(function() {
                if (player && player.getCurrentTime() >= window.endTime) {
                    player.pauseVideo();
                }
            }, 1000);
        }
    }
}

function seekToTime(seconds) {
    if (player && player.seekTo) {
        player.seekTo(seconds);
        player.playVideo();
    }
}

function setupKeyboardControls() {
    // Wait for video element to be available
    const videoCheck = setInterval(() => {
        const video = document.querySelector('.stVideo video');
        const iframe = document.querySelector('iframe');
        
        if (video || (iframe && iframe.src.includes('drive.google.com'))) {
            clearInterval(videoCheck);
            
            // Add keyboard event listener
            document.addEventListener('keydown', function(e) {
                // 'd' key for next scene
                if (e.key === 'd' || e.key === 'D') {
                    const nextButton = document.querySelector('button[data-testid="next-button"]');
                    if (nextButton && !nextButton.disabled) {
                        nextButton.click();
                    }
                }
                
                // Space bar for play/pause
                if (e.key === ' ' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
                    e.preventDefault();
                    if (video) {
                        if (video.paused) {
                            video.play();
                        } else {
                            video.pause();
                        }
                    } else if (player) {
                        const state = player.getPlayerState();
                        if (state === YT.PlayerState.PLAYING) {
                            player.pauseVideo();
                        } else {
                            player.playVideo();
                        }
                    }
                }
            });

            // Add video end time control
            if (video) {
                video.addEventListener('timeupdate', function() {
                    if (this.currentTime >= window.sceneEndTime) {
                        this.pause();
                    }
                });
            }
        }
    }, 100);
}

// Call setup when the page loads and after Streamlit re-runs
document.addEventListener('DOMContentLoaded', setupKeyboardControls);
if (window.Streamlit) {
    window.Streamlit.addEventListener('streamlit:render', setupKeyboardControls);
}
</script>

<!-- Load Google Drive Player API -->
<script src="https://www.youtube.com/iframe_api"></script>
"""

def load_script(script_path):
    """Load the JSON script file."""
    with open(script_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def convert_timestamp_to_seconds(timestamp):
    """Convert HH:MM:SS timestamp to seconds."""
    try:
        # Split into hours, minutes, and seconds (which may contain decimals)
        parts = timestamp.strip().split(':')
        if len(parts) != 3:
            return 0
        h, m, s = parts
        # Convert hours and minutes to integers, seconds to float
        return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception as e:
        st.error(f"Error converting timestamp {timestamp}: {str(e)}")
        return 0

def create_timeline_visualization(scenes, current_scene):
    """Create a visual timeline of scenes using HTML/CSS."""
    total_duration = max([convert_timestamp_to_seconds(scene['timestamp'].split(' - ')[1]) for scene in scenes])
    timeline_html = f"""
    <style>
        .timeline-container {{
            position: relative;
            padding-top: 25px;  /* 增加顶部padding，为标签腾出空间 */
            margin-bottom: 20px;
        }}
        .timeline {{
            width: 100%;
            height: 40px;
            background: #f0f0f0;
            position: relative;
            border-radius: 4px;
        }}
        .scene-marker {{
            position: absolute;
            height: 100%;
            background: #e0e0e0;
            border-right: 1px solid #ccc;
            transition: background-color 0.3s;
        }}
        .scene-marker.current {{
            background: #2196F3;
        }}
        .scene-label {{
            position: absolute;
            top: -25px;  /* 调整标签位置 */
            left: 50%;
            transform: translateX(-50%);
            font-size: 12px;
            background: white;  /* 添加背景色 */
            padding: 2px 4px;   /* 添加内边距 */
            border-radius: 2px;  /* 圆角 */
            white-space: nowrap; /* 防止文字换行 */
            z-index: 1;         /* 确保标签在最上层 */
        }}
    </style>
    <div class="timeline-container">
        <div class="timeline">
    """
    
    for scene in scenes:
        start_time = convert_timestamp_to_seconds(scene['timestamp'].split(' - ')[0])
        end_time = convert_timestamp_to_seconds(scene['timestamp'].split(' - ')[1])
        start_percent = (start_time / total_duration) * 100
        width_percent = ((end_time - start_time) / total_duration) * 100
        is_current = scene['scene_number'] == current_scene
        
        timeline_html += f"""
        <div class="scene-marker{' current' if is_current else ''}"
             style="left: {start_percent}%; width: {width_percent}%;">
            <div class="scene-label">{scene['scene_number']}</div>
        </div>
        """
    
    timeline_html += """
        </div>
    </div>
    """
    return timeline_html

def load_feedback(video_id):
    """Load existing feedback for a video."""
    # 使用绝对路径
    feedback_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'feedback'))
    feedback_file = os.path.join(feedback_dir, f"{video_id}_feedback_script.json")
    
    try:
        if os.path.exists(feedback_file):
            with open(feedback_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:  # 如果文件不为空
                    data = json.loads(content)
                    if isinstance(data, dict) and 'scenes' in data:
                        # 将新格式转换为兼容格式
                        feedback_data = {video_id: {}}
                        for scene in data['scenes']:
                            scene_number = scene['scene_number']
                            scene_key = str(scene_number)
                            feedback_data[video_id][scene_key] = {}
                            
                            # 处理场景笔记
                            if 'notes' in scene:
                                feedback_data[video_id][scene_key]['notes'] = scene['notes']
                            
                            # 处理交互反馈
                            if 'interactions_feedback' in scene:
                                for feedback in scene['interactions_feedback']:
                                    feedback_key = f"interaction_{feedback['index']}"
                                    feedback_data[video_id][scene_key][feedback_key] = {
                                        'index': feedback['index'],
                                        'content': feedback['content'],
                                        'speaker_feedback': feedback.get('speaker_feedback', ''),
                                        'target_feedback': feedback.get('target_feedback', ''),
                                        'action_emotion_feedback': feedback.get('action_emotion_feedback', ''),
                                        'mental_feedback': feedback.get('mental_feedback', '')
                                    }
                        return feedback_data
        return {video_id: {}}
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON in feedback file: {str(e)}")
        # 如果JSON无效，备份原文件并创建新的
        if os.path.exists(feedback_file):
            backup_file = f"{feedback_file}.backup"
            try:
                os.rename(feedback_file, backup_file)
                st.warning(f"Backed up invalid feedback file to {backup_file}")
            except Exception as be:
                st.error(f"Failed to backup feedback file: {str(be)}")
    except Exception as e:
        st.error(f"Error loading feedback file: {str(e)}")
    return {video_id: {}}

def save_feedback(video_id, scene_id, question_type, question_data, status, feedback_text):
    """保存反馈到文件"""
    feedback_dir = os.path.join(os.path.dirname(__file__), '..', 'feedback')
    os.makedirs(feedback_dir, exist_ok=True)
    
    feedback_file = os.path.join(feedback_dir, f"{video_id}_feedback.json")
    
    # 读取现有数据或创建新的数据结构
    if os.path.exists(feedback_file):
        with open(feedback_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            "video_id": video_id,
            "scenes": {}
        }
    
    # 确保场景数据存在
    if scene_id not in data["scenes"]:
        data["scenes"][scene_id] = {}
    
    # 确保问题类型数据存在
    if question_type not in data["scenes"][scene_id]:
        data["scenes"][scene_id][question_type] = []
    
    # 更新或添加问题数据
    question_entry = {
        "question": question_data["question"],
        "character": question_data["character"],
        "target_character": question_data["target_character"],
        "moment": question_data["moment"],
        "correct_answer": question_data["correct_answer"],
        "modality_evidence": question_data["modality_evidence"],
        "mental_state_evidence": question_data["mental_state_evidence"],
        "status": status,
        "feedback": feedback_text,
        "processed_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 检查是否已存在该问题的反馈
    found = False
    for i, q in enumerate(data["scenes"][scene_id][question_type]):
        if q["question"] == question_data["question"]:
            data["scenes"][scene_id][question_type][i] = question_entry
            found = True
            break
    
    if not found:
        data["scenes"][scene_id][question_type].append(question_entry)
    
    # 保存到文件
    with open(feedback_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # 返回保存状态
    return True

def mark_question_processed(video_id, scene, q_type, question_id, status, question_data=None, feedback_text=""):
    """标记问题为已处理，并保存反馈"""
    if video_id not in st.session_state.processed_items:
        st.session_state.processed_items[video_id] = {}
    if scene not in st.session_state.processed_items[video_id]:
        st.session_state.processed_items[video_id][scene] = {}
    if q_type not in st.session_state.processed_items[video_id][scene]:
        st.session_state.processed_items[video_id][scene][q_type] = {}
    
    st.session_state.processed_items[video_id][scene][q_type][question_id] = status
    
    # 如果提供了问题数据，保存到文件
    if question_data:
        save_success = save_feedback(video_id, scene, q_type, question_data, status, feedback_text)
        if save_success:
            st.success(f"✅ 已保存问题 {question_id + 1} 的处理结果")
        else:
            st.error(f"❌ 保存问题 {question_id + 1} 的处理结果失败")
        time.sleep(0.5)  # 显示提示信息的时间

    # 显示最后保存时间
    if is_question_processed(video_id, scene, q_type, question_id):
        try:
            with open(os.path.join(os.path.dirname(__file__), '..', 'feedback', f"{video_id}_feedback.json"), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for q_data in data["scenes"].get(scene, {}).get(q_type, []):
                    if q_data["question"] == question_data["question"]:
                        st.caption(f"最后保存时间: {q_data['processed_time']}")
                        break
        except:
            pass

def load_character_analysis(video_id, caption_folder):
    """加载角色分析文件"""
    char_file = os.path.join(caption_folder, f"{video_id}_characters.json")
    if os.path.exists(char_file):
        with open(char_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("character_analysis", {}).get("description", "No character analysis available.")
    return "Character analysis file not found."

def load_tom_qa(folder_path, scene_file):
    """加载特定场景的 ToM QA 数据"""
    file_path = os.path.join(folder_path, scene_file)
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def get_question_type_data(qa_data, question_type):
    """从QA数据中提取特定类型的问题"""
    questions = []
    for character in qa_data["tom_qa_pairs"]:
        char_data = qa_data["tom_qa_pairs"][character]
        if question_type in char_data:
            for q in char_data[question_type]:
                q_info = {
                    "character": character,
                    "question": q["question"],
                    "correct_answer": q["options"][q["correct_answer"]],
                    "moment": q["moment"],
                    "target_character": q["target_character"],
                    "order": q["order"],
                    "modality_evidence": q["modality_evidence"],
                    "mental_state_evidence": q.get("mental_state_evidence", ""),
                    "difficulty": q.get("difficulty", 0),
                    "suggestions": q.get("suggestions", [])
                }
                questions.append(q_info)
    return questions

def get_video_qa_files(qa_dir):
    """获取所有视频的QA文件
    返回格式: {
        "video_id": {
            "folder_path": "完整的文件夹路径",
            "scene_files": ["scene_1.json", "scene_2.json", ...]
        }
    }
    """
    video_qa_files = {}
    
    # 遍历所有子文件夹
    for root, dirs, files in os.walk(qa_dir):
        # 查找包含 "_feedback_script_realigned" 的文件夹
        if "_feedback_script_realigned" in root:
            # 从路径中提取视频ID
            video_id = os.path.basename(root).split("_feedback_script_realigned")[0]
            
            # 获取场景文件
            scene_files = sorted([f for f in files if f.startswith("scene_") and f.endswith(".json")],
                               key=lambda x: int(x.split("_")[1].split(".")[0]))
            
            if scene_files:  # 只添加有场景文件的视频
                video_qa_files[video_id] = {
                    "folder_path": root,
                    "scene_files": scene_files
                }
    
    return video_qa_files

def init_session_state():
    """初始化会话状态"""
    if 'current_video_index' not in st.session_state:
        st.session_state.current_video_index = 0
    if 'current_scene_index' not in st.session_state:
        st.session_state.current_scene_index = 0
    if 'current_type_index' not in st.session_state:
        st.session_state.current_type_index = 0
    if 'processed_items' not in st.session_state:
        st.session_state.processed_items = {}
    if 'feedback_history' not in st.session_state:
        st.session_state.feedback_history = {}
    if 'paths_configured' not in st.session_state:
        st.session_state.paths_configured = False
    if 'show_path_settings' not in st.session_state:
        st.session_state.show_path_settings = not st.session_state.paths_configured

def load_feedback_history():
    """加载所有反馈历史"""
    feedback_dir = Path("feedback")
    if not feedback_dir.exists():
        return {}
    
    history = {}
    for file in feedback_dir.glob("*_feedback.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                video_id = data.get('video_id')
                if video_id:
                    history[video_id] = data
        except:
            continue
    return history

def get_progress_info(video_qa_files):
    """获取当前进度信息"""
    total_videos = len(video_qa_files)
    current_video = list(video_qa_files.keys())[st.session_state.current_video_index]
    total_scenes = len(video_qa_files[current_video]["scene_files"])
    question_types = ["intention_questions", "desire_questions", "emotion_questions", 
                     "knowledge_questions", "belief_questions"]
    
    # 计算已处理的项目数量
    processed_count = 0
    total_count = 0
    for v in st.session_state.processed_items.values():
        for s in v.values():
            for t in s.values():
                processed_count += len(t)
                
    return {
        "current_video": current_video,
        "current_scene": video_qa_files[current_video]["scene_files"][st.session_state.current_scene_index],
        "current_type": question_types[st.session_state.current_type_index],
        "video_progress": f"{st.session_state.current_video_index + 1}/{total_videos}",
        "scene_progress": f"{st.session_state.current_scene_index + 1}/{total_scenes}",
        "type_progress": f"{st.session_state.current_type_index + 1}/5",
        "processed_count": processed_count
    }

def get_question_status(video_id, scene, q_type, question_id):
    """获取问题的处理状态"""
    try:
        return st.session_state.processed_items[video_id][scene][q_type][question_id]
    except KeyError:
        return QUESTION_STATUS_PENDING

def is_question_processed(video_id, scene, q_type, question_id):
    """检查问题是否已处理"""
    status = get_question_status(video_id, scene, q_type, question_id)
    return status != QUESTION_STATUS_PENDING

def navigate_next(video_qa_files):
    """导航到下一个项目"""
    question_types = ["intention_questions", "desire_questions", "emotion_questions", 
                     "knowledge_questions", "belief_questions"]
    current_video = list(video_qa_files.keys())[st.session_state.current_video_index]
    total_scenes = len(video_qa_files[current_video]["scene_files"])
    
    # 先尝试切换问题类型
    if st.session_state.current_type_index < len(question_types) - 1:
        st.session_state.current_type_index += 1
    # 如果问题类型已到末尾，切换场景
    elif st.session_state.current_scene_index < total_scenes - 1:
        st.session_state.current_scene_index += 1
        st.session_state.current_type_index = 0
    # 如果场景已到末尾，切换视频
    elif st.session_state.current_video_index < len(video_qa_files) - 1:
        st.session_state.current_video_index += 1
        st.session_state.current_scene_index = 0
        st.session_state.current_type_index = 0
    else:
        st.success("已完成所有内容的验证！")
        return False
    return True

def navigate_previous(video_qa_files):
    """导航到上一组问题"""
    question_types = ["intention_questions", "desire_questions", "emotion_questions", 
                     "knowledge_questions", "belief_questions"]
    current_video = list(video_qa_files.keys())[st.session_state.current_video_index]
    
    # 先尝试切换问题类型
    if st.session_state.current_type_index > 0:
        st.session_state.current_type_index -= 1
    # 如果问题类型已到开头，切换到上一个场景
    elif st.session_state.current_scene_index > 0:
        st.session_state.current_scene_index -= 1
        st.session_state.current_type_index = len(question_types) - 1
    # 如果场景已到开头，切换到上一个视频
    elif st.session_state.current_video_index > 0:
        st.session_state.current_video_index -= 1
        current_video = list(video_qa_files.keys())[st.session_state.current_video_index]
        st.session_state.current_scene_index = len(video_qa_files[current_video]["scene_files"]) - 1
        st.session_state.current_type_index = len(question_types) - 1
    return True

def get_character_with_description(character_name, qa_data):
    """获取角色名称及其视觉描述"""
    if "speaker_mapping" in qa_data:
        for speaker in qa_data["speaker_mapping"]:
            if speaker["character_name"] == character_name:
                return f"{character_name}（{speaker['visual_description']}）"
    return character_name

def get_all_questions(qa_data):
    """从QA数据中提取所有类型的问题"""
    questions = []
    question_types = ["intention_questions", "desire_questions", "emotion_questions", 
                     "knowledge_questions", "belief_questions"]
    
    for character in qa_data["tom_qa_pairs"]:
        char_data = qa_data["tom_qa_pairs"][character]
        for q_type in question_types:
            if q_type in char_data:
                for q in char_data[q_type]:
                    q_info = {
                        "character": character,
                        "question": q["question"],
                        "correct_answer": q["options"][q["correct_answer"]],
                        "moment": q["moment"],
                        "target_character": q["target_character"],
                        "order": q["order"],
                        "modality_evidence": q["modality_evidence"],
                        "mental_state_evidence": q.get("mental_state_evidence", ""),
                        "question_type": q_type
                    }
                    questions.append(q_info)
    return questions

def load_processed_questions(video_id, scene_id):
    """加载已处理的问题状态"""
    feedback_file = os.path.join(os.path.dirname(__file__), '..', 'feedback', f"{video_id}_feedback.json")
    try:
        if os.path.exists(feedback_file):
            with open(feedback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "scenes" in data and scene_id in data["scenes"]:
                    scene_data = data["scenes"][scene_id]
                    processed_items = {}
                    for q_type in scene_data:
                        if isinstance(scene_data[q_type], list):  # 确保是问题列表
                            for q in scene_data[q_type]:
                                if "status" in q:
                                    if q_type not in processed_items:
                                        processed_items[q_type] = {}
                                    # 使用问题内容作为键来匹配
                                    processed_items[q_type][q["question"]] = q["status"]
                    return processed_items
    except Exception as e:
        st.error(f"加载反馈文件时出错: {str(e)}")
    return {}

def find_next_unprocessed(video_qa_files):
    question_types = ["intention_questions", "desire_questions", "emotion_questions", "knowledge_questions", "belief_questions"]
    for v_idx, (video_id, video_data) in enumerate(video_qa_files.items()):
        for s_idx, scene_file in enumerate(video_data["scene_files"]):
            qa_data = load_tom_qa(video_data["folder_path"], scene_file)
            for t_idx, q_type in enumerate(question_types):
                questions = get_question_type_data(qa_data, q_type)
                processed_items = load_processed_questions(video_id, scene_file)
                for q in questions:
                    status = processed_items.get(q_type, {}).get(q["question"], "pending")
                    if status == "pending":
                        return v_idx, s_idx, t_idx
    return 0, 0, 0  # 全部完成时

def create_video_player(video_path, start_time=0):
    """创建自定义视频播放器"""
    # 读取视频文件
    with open(video_path, 'rb') as f:
        video_bytes = f.read()
    
    # 使用base64编码视频数据
    import base64
    video_b64 = base64.b64encode(video_bytes).decode()
    
    return f"""
        <div style="width:100%;">
            <video id="custom_video" width="100%" controls>
                <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
        <script>
            // 获取视频元素
            const video = document.getElementById('custom_video');
            
            // 设置初始时间
            video.addEventListener('loadedmetadata', function() {{
                video.currentTime = {start_time};
            }});
            
            // 添加跳转函数到window对象
            window.jumpToStart = function() {{
                if (video) {{
                    video.currentTime = {start_time};
                    video.play();
                }}
            }};
        </script>
    """

def show_path_settings_ui():
    """显示路径设置界面"""
    st.header("路径配置")
    with st.form("path_settings"):
        video_dir = st.text_input("视频目录路径", value=st.session_state.get('video_dir', DEFAULT_VIDEO_DIR))
        qa_dir = st.text_input("ToM QA JSON目录路径", value=st.session_state.get('qa_dir', DEFAULT_QA_DIR))
        caption_dir = st.text_input("Caption目录路径", value=st.session_state.get('caption_dir', DEFAULT_CAPTION_DIR))
        
        if st.form_submit_button("保存设置", type="primary"):
            if all([video_dir, qa_dir, caption_dir]):
                st.session_state.video_dir = video_dir
                st.session_state.qa_dir = qa_dir
                st.session_state.caption_dir = caption_dir
                st.session_state.paths_configured = True
                st.session_state.show_path_settings = False
                st.success("设置已保存！")
                st.rerun()
            else:
                st.error("请设置所有必要的目录路径")

def main():
    st.set_page_config(layout="wide")
    
    # 添加自动滚动到顶部的 JavaScript
    st.markdown("""
        <script>
            window.scrollTo(0, 0);
        </script>
    """, unsafe_allow_html=True)
    
    # 初始化会话状态
    init_session_state()
    st.session_state.feedback_history = load_feedback_history()

    st.title("ToM QA Verifier")

    # 路径设置处理
    if not st.session_state.paths_configured or st.session_state.show_path_settings:
        show_path_settings_ui()
        if not st.session_state.paths_configured:
            st.stop()
    else:
        # 显示当前路径设置和修改按钮
        with st.sidebar:
            st.caption("当前路径设置")
            st.caption(f"视频目录：{st.session_state.video_dir}")
            st.caption(f"QA目录：{st.session_state.qa_dir}")
            st.caption(f"Caption目录：{st.session_state.caption_dir}")
            if st.button("修改路径设置"):
                st.session_state.show_path_settings = True
                st.rerun()

    # 获取所有视频的QA文件
    video_qa_files = get_video_qa_files(st.session_state.qa_dir)
    if not video_qa_files:
        st.error("未找到QA文件")
        return

    # 只在首次加载时自动跳转到最新未标注样本
    if 'current_video_index' not in st.session_state:
        v_idx, s_idx, t_idx = find_next_unprocessed(video_qa_files)
        st.session_state.current_video_index = v_idx
        st.session_state.current_scene_index = s_idx
        st.session_state.current_type_index = t_idx

    # 侧边栏添加视频选择下拉框
    video_ids = list(video_qa_files.keys())
    selected_video = st.sidebar.selectbox("选择视频ID", video_ids, index=st.session_state.current_video_index)
    selected_video_index = video_ids.index(selected_video)
    if selected_video_index != st.session_state.current_video_index:
        st.session_state.current_video_index = selected_video_index
        st.session_state.current_scene_index = 0
        st.session_state.current_type_index = 0
        # st.experimental_rerun()
        st.rerun()

    # 获取当前进度信息
    progress = get_progress_info(video_qa_files)
    
    # 显示总体进度
    st.markdown("### 验证进度")
    cols = st.columns(3)
    with cols[0]:
        st.metric("当前视频", f"{progress['video_progress']}")
    with cols[1]:
        st.metric("当前场景", f"{progress['scene_progress']}")
    with cols[2]:
        st.metric("问题类型", f"{progress['type_progress']}")
    
    st.progress(progress['processed_count'] / (len(video_qa_files) * 5))  # 简单进度估算
    
    # 加载当前数据
    current_video = progress['current_video']
    current_scene = progress['current_scene']
    current_type = progress['current_type']
    
    qa_data = load_tom_qa(
        video_qa_files[current_video]["folder_path"],
        current_scene
    )
    char_analysis = load_character_analysis(current_video, st.session_state.caption_dir)

    # 显示当前位置
    timestamp = qa_data['raw_scene_data']['timestamp'] if 'raw_scene_data' in qa_data and 'timestamp' in qa_data['raw_scene_data'] else ""
    if timestamp:
        start_time = convert_timestamp_to_seconds(timestamp.split(' - ')[0])
        st.markdown(f"当前验证: **{current_video}** - {current_scene.replace('.json', '')} ({timestamp})", 
                   help="当前正在验证的视频和场景")
    else:
        st.markdown(f"当前验证: **{current_video}** - {current_scene.replace('.json', '')}", 
                   help="当前正在验证的视频和场景")

    # 主要内容区域
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        # 视频区域
        st.subheader("视频播放")
        video_path = os.path.join(st.session_state.video_dir, f"{current_video}.mp4")
        # 获取当前场景的start_time
        qa_data = load_tom_qa(video_qa_files[current_video]["folder_path"], current_scene)
        start_time = 0
        if 'raw_scene_data' in qa_data and 'timestamp' in qa_data['raw_scene_data']:
            start_time = convert_timestamp_to_seconds(qa_data['raw_scene_data']['timestamp'].split(' - ')[0])

        # 跳转按钮
        jump = st.button("⏱️ 跳转到场景开始", key=f"seek_button_{current_video}_{current_scene}")

        # 自定义 HTML5 视频播放器，支持 JS 跳转
        import base64
        if os.path.exists(video_path):
            with open(video_path, 'rb') as video_file:
                video_bytes = video_file.read()
                video_b64 = base64.b64encode(video_bytes).decode()
                st.components.v1.html(f'''
                    <video id="myvideo" width="100%" controls>
                        <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
                        您的浏览器不支持 video 标签。
                    </video>
                    <script>
                        const video = document.getElementById('myvideo');
                        window.jumpToStart = function() {{
                            video.currentTime = {start_time};
                            video.play();
                        }};
                        // 如果本次 Streamlit 运行点击了跳转按钮，则自动跳转
                        {'window.jumpToStart();' if jump else ''}
                    </script>
                ''', height=400)
        else:
            st.error("视频文件不存在")

        # 在视频切换时重置状态
        if 'previous_video' not in st.session_state:
            st.session_state.previous_video = current_video
        elif st.session_state.previous_video != current_video:
            st.session_state.force_jump = False
            st.session_state.last_jump_time = 0
            st.session_state.current_video_id = None
            st.session_state.current_scene_id = None
            st.session_state.previous_video = current_video

        # 问题处理状态显示
        st.markdown("---")
        st.markdown("**问题处理状态：**")
        questions = get_all_questions(qa_data)
        processed_items = load_processed_questions(current_video, current_scene)
        status_map = {"pending": "🟡", "kept": "🟢", "deleted": "🔴"}
        status_line = ""
        for i, q in enumerate(questions):
            saved_status = processed_items.get(q["question_type"], {}).get(q["question"], "pending")
            marker = status_map.get(saved_status, "🟡")
            status_line += f"{marker} 问题{i+1}  "
        st.markdown(status_line)

        # 场景信息
        st.subheader("场景信息")
        tabs = st.tabs(["角色分析", "场景描述", "对话内容"])
        
        with tabs[0]:
            st.markdown("### 角色信息")
            if "speaker_mapping" in qa_data:
                for speaker in qa_data["speaker_mapping"]:
                    st.markdown(f"**{speaker['character_name']}**: {speaker['visual_description']}")
            st.markdown("---")
            st.markdown("### 角色分析")
            st.markdown(char_analysis)
            
        with tabs[1]:
            if "raw_scene_data" in qa_data:
                st.markdown(f"**时间戳**: {qa_data['raw_scene_data']['timestamp']}")
                st.markdown("**场景描述**:")
                st.markdown(qa_data['raw_scene_data']['description'])
        
        with tabs[2]:
            if "raw_scene_data" in qa_data:
                for interaction in qa_data['raw_scene_data']['interactions']:
                    st.markdown(f"- {interaction}")

    with col2:
        st.subheader("ToM QA 验证")
        questions = get_all_questions(qa_data)
        
        # 加载已处理的问题状态
        processed_items = load_processed_questions(current_video, current_scene)
        
        # 显示当前组问题的处理进度
        processed_count = sum(1 for q in questions 
                            if q["question"] in processed_items.get(q["question_type"], {}))
        if len(questions) > 0:
            st.progress(processed_count / len(questions))
            st.markdown(f"当前场景进度: {processed_count}/{len(questions)}")
        else:
            st.info("当前场景没有问题需要处理")
        
        # 右侧问题验证区域
        # 找到第一个未处理的问题索引
        first_pending_index = -1
        for i, q in enumerate(questions):
            saved_status = processed_items.get(q["question_type"], {}).get(q["question"], QUESTION_STATUS_PENDING)
            if saved_status == QUESTION_STATUS_PENDING:
                first_pending_index = i
                break

        for i, q in enumerate(questions):
            # 获取已保存的状态
            saved_status = processed_items.get(q["question_type"], {}).get(q["question"], QUESTION_STATUS_PENDING)
            # 状态原点
            status_marker = {QUESTION_STATUS_PENDING: "🟡", QUESTION_STATUS_KEPT: "🟢", QUESTION_STATUS_DELETED: "🔴"}[saved_status]
            # 只有是第一个未处理的问题时才展开
            with st.expander(f"{status_marker} 问题 {i+1} [{q['question_type']}]", expanded=(i == first_pending_index)):
                # 显示问题和答案
                st.markdown(f"**问题**: {q['question']}")
                st.markdown(f"**时刻**: {q['moment']}")
                st.markdown(f"**正确答案**: {q['correct_answer']}")
                # 证据信息
                st.markdown("**多模态证据**:")
                st.markdown(q['modality_evidence'])
                st.markdown("**心理状态证据**:")
                st.markdown(q['mental_state_evidence'])
                # 添加用户反馈文本框
                st.markdown("---")
                feedback_text = st.text_area(
                    "Human Feedback",
                    value=st.session_state.get(f"feedback_{i}", ""),
                    key=f"feedback_{i}",
                    height=68
                )
                # 操作按钮
                st.markdown("---")
                cols = st.columns([1, 1])
                with cols[0]:
                    if st.button("✅ 保留", key=f"keep_{i}", use_container_width=True):
                        feedback_text = st.session_state.get(f"feedback_{i}", "")
                        mark_question_processed(
                            current_video, 
                            current_scene, 
                            q["question_type"], 
                            i, 
                            QUESTION_STATUS_KEPT,
                            question_data=q,
                            feedback_text=feedback_text
                        )
                        st.rerun()
                with cols[1]:
                    if st.button("❌ 删除", key=f"delete_{i}", use_container_width=True):
                        feedback_text = st.session_state.get(f"feedback_{i}", "")
                        mark_question_processed(
                            current_video, 
                            current_scene, 
                            q["question_type"], 
                            i, 
                            QUESTION_STATUS_DELETED,
                            question_data=q,
                            feedback_text=feedback_text
                        )
                        st.rerun()
                # 如果已经处理过，更新session state中的状态
                if saved_status != QUESTION_STATUS_PENDING:
                    if current_video not in st.session_state.processed_items:
                        st.session_state.processed_items[current_video] = {}
                    if current_scene not in st.session_state.processed_items[current_video]:
                        st.session_state.processed_items[current_video][current_scene] = {}
                    if q["question_type"] not in st.session_state.processed_items[current_video][current_scene]:
                        st.session_state.processed_items[current_video][current_scene][q["question_type"]] = {}
                    st.session_state.processed_items[current_video][current_scene][q["question_type"]][i] = saved_status
        
        # 导航控制
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.current_video_index > 0 or st.session_state.current_scene_index > 0:
                if st.button("⏮️ 上一个场景", use_container_width=True):
                    if st.session_state.current_scene_index > 0:
                        st.session_state.current_scene_index -= 1
                    elif st.session_state.current_video_index > 0:
                        st.session_state.current_video_index -= 1
                        st.session_state.current_scene_index = len(video_qa_files[list(video_qa_files.keys())[st.session_state.current_video_index]]["scene_files"]) - 1
                    # 添加滚动到顶部的JavaScript
                    st.components.v1.html("""
                        <script>
                            window.scrollTo(0, 0);
                        </script>
                    """, height=0)
                    st.rerun()
        with col2:
            if st.session_state.current_video_index < len(video_qa_files) - 1 or \
               st.session_state.current_scene_index < len(video_qa_files[current_video]["scene_files"]) - 1:
                if st.button("下一个场景 ⏭️", use_container_width=True):
                    if st.session_state.current_scene_index < len(video_qa_files[current_video]["scene_files"]) - 1:
                        st.session_state.current_scene_index += 1
                    else:
                        st.session_state.current_video_index += 1
                        st.session_state.current_scene_index = 0
                    # 添加滚动到顶部的JavaScript
                    st.components.v1.html("""
                        <script>
                            window.scrollTo(0, 0);
                        </script>
                    """, height=0)
                    st.rerun()

        # 场景跳转按钮下方增加视频跳转按钮
        st.markdown("---")
        # 获取当前视频在列表中的索引
        video_ids = list(video_qa_files.keys())
        current_video_idx = video_ids.index(current_video)
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⏮️ 上一个视频", disabled=current_video_idx == 0):
                st.session_state.current_video_index = current_video_idx - 1
                st.session_state.current_scene_index = 0
                st.session_state.force_jump = False  # 重置跳转状态
                # 添加滚动到顶部的JavaScript
                st.components.v1.html("""
                    <script>
                        window.scrollTo(0, 0);
                    </script>
                """, height=0)
                st.rerun()
        with col_next:
            if st.button("下一个视频 ⏭️", disabled=current_video_idx == len(video_ids) - 1):
                st.session_state.current_video_index = current_video_idx + 1
                st.session_state.current_scene_index = 0
                st.session_state.force_jump = False  # 重置跳转状态
                # 添加滚动到顶部的JavaScript
                st.components.v1.html("""
                    <script>
                        window.scrollTo(0, 0);
                    </script>
                """, height=0)
                st.rerun()

if __name__ == "__main__":
    main() 