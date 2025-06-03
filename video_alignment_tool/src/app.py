import streamlit as st
import streamlit.components.v1 as components
import json
import os
from pathlib import Path
import time
import re
# from gdrive_utils import list_videos_in_folder, get_gdrive_service

# 添加模式选择和视频处理功能
VIDEO_MODE_LOCAL = "本地视频模式"
VIDEO_MODE_CLOUD = "云存储模式"

# 定义默认路径
DEFAULT_VIDEO_DIR = r"G:\Phd\datasets\videoQA\social-IQ2.0\Social-IQ-2.0-Challenge-main\siq2\siq2\siq_full\video\videos_trainval_tom"
DEFAULT_SCRIPT_DIR = r"J:\Code\paper3\data\4_global_speaker_alignment\output\v5.1_stage1_alignment_qa_trainval\openai_full_gpt-4-1_merged_scenes"

# DEFAULT_VIDEO_DIR = r"G:\Phd\datasets\videoQA\social-IQ2.0\Social-IQ-2.0-Challenge-main\siq2\siq2\siq_full\video"
# DEFAULT_SCRIPT_DIR = r"J:\Code\paper3\data\4_global_speaker_alignment\output\v5.1_stage1_alignment_qa_trainval"


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
            st.error(f"Invalid timestamp format: {timestamp}")
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

def save_feedback(video_id, scene_number, feedback, original_script):
    """Save user feedback to a JSON file while maintaining the original script structure."""
    # 使用绝对路径
    feedback_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'feedback'))
    os.makedirs(feedback_dir, exist_ok=True)
    
    feedback_file = os.path.join(feedback_dir, f"{video_id}_feedback_script.json")
    
    # try:
    # 尝试加载现有的反馈脚本
    script_with_feedback = None
    if os.path.exists(feedback_file):
        try:
            with open(feedback_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    script_with_feedback = json.loads(content)
        except json.JSONDecodeError:
            st.warning(f"Invalid JSON in {feedback_file}, creating new file")
    
    # 如果没有现有的反馈脚本，使用原始脚本作为基础
    if not script_with_feedback:
        script_with_feedback = original_script.copy()
    
    # 确保scenes列表存在
    if 'scenes' not in script_with_feedback:
        script_with_feedback['scenes'] = []
        
    # 找到对应的场景
    scene_index = None
    for i, scene in enumerate(script_with_feedback['scenes']):
        if scene['scene_number'] == scene_number:
            scene_index = i
            break
    
    if scene_index is not None:
        # 更新现有场景
        scene = script_with_feedback['scenes'][scene_index]
        
        # 确保interactions_feedback字段存在
        if 'interactions_feedback' not in scene:
            scene['interactions_feedback'] = []
        
        # 清除现有的反馈（如果有）并添加新的反馈
        scene['interactions_feedback'] = []
        
        # 添加每个交互的反馈
        for key, value in feedback.items():
            if key.startswith('interaction_'):
                if isinstance(value, dict):
                    scene['interactions_feedback'].append({
                        'index': value['index'],
                        'content': value['content'],
                        'speaker_feedback': value['speaker_feedback'],
                        'target_feedback': value['target_feedback'],
                        'action_emotion_feedback': value['action_emotion_feedback'],
                        'mental_feedback': value['mental_feedback']
                    })
        
        # 添加场景笔记（如果有）
        if 'notes' in feedback and isinstance(feedback['notes'], str):
            scene['notes'] = feedback['notes'].strip()
        
        # 保存更新后的脚本
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(script_with_feedback, f, indent=2, ensure_ascii=False)
        
        # 显示成功消息
        st.success("保存成功！")
        return True
        


def main():
    st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
    
    # 增加顶部padding，避免内容被遮盖
    st.markdown(
        '''
        <style>
        .block-container { padding-top: 2rem !important; }
        .stButton button {
            padding: 0.2rem 1rem;
            font-size: 0.8rem;
        }
        /* 调整文本框样式 */
        .stTextArea textarea {
            min-height: 68px !important;
            padding: 0.3rem !important;
            font-size: 0.9rem !important;
            line-height: 1.2 !important;
        }
        /* 减小文本框label的间距 */
        .stTextArea label {
            padding-bottom: 0.2rem !important;
            font-size: 0.9rem !important;
        }
        /* 减小每个交互之间的间距 */
        .element-container {
            margin-bottom: 0.5rem !important;
        }
        </style>
        ''',
        unsafe_allow_html=True
    )
    st.markdown("""
        <style>
        html, body, .stApp { font-size: 18px !important; }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'current_scene' not in st.session_state:
        st.session_state.current_scene = None
    if 'current_video' not in st.session_state:
        st.session_state.current_video = None
    if 'feedback_saved' not in st.session_state:
        st.session_state.feedback_saved = False
    if 'current_script_index' not in st.session_state:
        st.session_state.current_script_index = 0
    if 'video_mode' not in st.session_state:
        st.session_state.video_mode = None
    if 'video_dir' not in st.session_state:
        st.session_state.video_dir = DEFAULT_VIDEO_DIR
    if 'script_dir' not in st.session_state:
        st.session_state.script_dir = DEFAULT_SCRIPT_DIR
    if 'remote_folder' not in st.session_state:
        st.session_state.remote_folder = ""
    if 'show_settings' not in st.session_state:
        st.session_state.show_settings = False
    if 'mapping_initialized' not in st.session_state:
        # 检查是否已有映射文件
        mapping_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'video_mapping.json')
        if not os.path.exists(mapping_file):
            # 只有在映射文件不存在时才创建空映射
            save_video_mapping({}, mode=VIDEO_MODE_CLOUD)
        st.session_state.mapping_initialized = True

    # 模式选择界面
    if st.session_state.video_mode is None:
        st.title("视频场景标注工具")
        st.markdown("### 请选择视频访问模式")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("本地视频模式", use_container_width=True):
                st.session_state.video_mode = VIDEO_MODE_LOCAL
                st.session_state.show_settings = True  # 自动显示设置界面
                st.rerun()
        
        with col2:
            if st.button("云存储模式", use_container_width=True):
                st.session_state.video_mode = VIDEO_MODE_CLOUD
                st.session_state.show_settings = True  # 自动显示设置界面
                st.rerun()
        
        st.markdown("---")
        st.markdown("""
        **模式说明：**
        
        - **本地视频模式**：从本地磁盘加载视频文件，适合离线工作或大量视频处理
        - **云存储模式**：从云存储（如Google Drive）加载视频，适合在线部署和远程访问
        
        请根据您的实际需求选择合适的模式。
        """)
        
        return  # 停止继续执行，等待用户选择

    # 如果是本地模式且需要显示设置界面
    if st.session_state.video_mode == VIDEO_MODE_LOCAL and st.session_state.show_settings:
        st.title("本地视频模式设置")
        
        # 显示返回按钮
        if st.button("← 返回主界面"):
            st.session_state.show_settings = False
            st.rerun()
            
        st.markdown("### 视频文件夹设置")
        st.markdown("""
        请设置以下路径：
        1. 视频文件夹路径：存放所有视频文件的文件夹
        2. 脚本文件夹路径：存放所有脚本文件的文件夹
        
        **注意：**
        - 视频文件名应该为"视频ID.mp4"格式
        - 脚本文件名应该为"视频ID_script.json"格式
        """)
        
        # 使用form来确保设置被正确保存
        with st.form("local_storage_settings"):
            new_video_dir = st.text_input(
                "视频文件夹路径",
                value=st.session_state.get('video_dir', ''),
                help="输入存放所有视频文件的文件夹路径"
            )
            
            new_script_dir = st.text_input(
                "脚本文件夹路径",
                value=st.session_state.get('script_dir', ''),
                help="输入存放所有脚本文件的文件夹路径"
            )
            
            submitted = st.form_submit_button("保存设置", type="primary")
            if submitted:
                if not new_video_dir or not new_script_dir:
                    st.error("请填写所有必需的路径！")
                elif not os.path.exists(new_video_dir):
                    st.error(f"视频文件夹路径不存在：{new_video_dir}")
                elif not os.path.exists(new_script_dir):
                    st.error(f"脚本文件夹路径不存在：{new_script_dir}")
                else:
                    st.session_state.video_dir = new_video_dir
                    st.session_state.script_dir = new_script_dir
                    st.session_state.show_settings = False
                    st.success("设置已保存！")
                    st.rerun()
        
        return  # 停止继续执行，等待用户完成设置

    # 如果是云存储模式且需要显示设置界面
    if st.session_state.video_mode == VIDEO_MODE_CLOUD and st.session_state.show_settings:
        show_cloud_storage_settings()
        return

    # 创建左右两列主布局
    left_col, right_col = st.columns([0.8, 1])
    
    # 在左列创建上下布局
    with left_col:
        # 视频区域（最上方）
        video_container = st.container()
        
        # 场景按钮区域（视频下方）
        scene_container = st.container()
        
        # 控制区（如设置按钮等）
        with st.container():
            # 云存储模式下显示设置按钮
            if st.session_state.video_mode == VIDEO_MODE_CLOUD:
                if st.button("⚙️ 设置", use_container_width=True):
                    st.session_state.show_settings = True
                    st.rerun()
            # 如果是云存储模式且未设置远程文件夹，显示警告
            if st.session_state.video_mode == VIDEO_MODE_CLOUD and not st.session_state.remote_folder:
                st.warning("⚠️ 请先设置云存储", icon="⚠️")
        
        # 获取数据
        video_dir = st.session_state.get('video_dir', DEFAULT_VIDEO_DIR)
        script_dir = st.session_state.get('script_dir', DEFAULT_SCRIPT_DIR)
        
        # 检查目录
        if st.session_state.video_mode == VIDEO_MODE_LOCAL:
            if not os.path.exists(video_dir) or not os.path.exists(script_dir):
                st.error("请检查目录路径设置")
                return
        
        # 检查脚本目录
        try:
            script_files = sorted([f for f in os.listdir(script_dir) if f.endswith('_script.json')])
            if not script_files:
                st.warning("未找到脚本文件")
                return
        except Exception as e:
            st.error(f"访问目录时出错: {str(e)}")
            return

        # 加载当前脚本
        selected_file = script_files[st.session_state.current_script_index]
        script_path = os.path.join(script_dir, selected_file)
        script_data = load_script(script_path)
        video_id = script_data['meta']['visual_file_id']
        
        # 根据模式获取视频路径
        video_path = get_video_path(video_id, st.session_state.video_mode)
        
        # 检查视频是否可访问
        video_accessible = False
        if st.session_state.video_mode == VIDEO_MODE_LOCAL:
            video_accessible = os.path.exists(video_path)
        else:
            # 云模式假设视频总是可访问的，除非链接为空
            video_accessible = bool(video_path)
        
        if not video_accessible:
            st.error(f"Video not found: {video_id}")
            if st.session_state.video_mode == VIDEO_MODE_CLOUD:
                st.warning("云存储模式下未找到视频链接，请确保在 get_video_path 函数中添加了正确的视频映射。")
            return
        
        # Load feedback data
        existing_feedback = load_feedback(video_id)
        scenes = script_data.get('scenes', [])
        scene_numbers = [scene['scene_number'] for scene in scenes]
        
        # 显示视频
        if st.session_state.current_scene is not None:
            scene = scenes[scene_numbers.index(st.session_state.current_scene)]
            with video_container:
                st.header(f"Scene {st.session_state.current_scene}")
                timestamp = scene['timestamp']
                st.markdown(f"**Time**: {timestamp}")
                
                start_time, end_time = timestamp.split(' - ')
                start_seconds = convert_timestamp_to_seconds(start_time)
                end_seconds = convert_timestamp_to_seconds(end_time)
                
                try:
                    if st.session_state.video_mode == VIDEO_MODE_LOCAL:
                        # 本地视频模式
                        with open(video_path, 'rb') as video_file:
                            video_bytes = video_file.read()
                            st.video(video_bytes, start_time=start_seconds, format="video/mp4")
                    else:
                        # 云存储模式 - 使用iframe播放Google Drive视频
                        if 'drive.google.com' in video_path:
                            try:
                                # 提取文件ID
                                file_id = None
                                if '/file/d/' in video_path:
                                    file_id = video_path.split('/file/d/')[1].split('/')[0]
                                elif 'id=' in video_path:
                                    file_id = video_path.split('id=')[1].split('&')[0]
                                elif 'export=download' in video_path:
                                    file_id = video_path.split('id=')[1].split('&')[0]
                                
                                if not file_id:
                                    st.error(f"无法从URL中提取文件ID: {video_path}")
                                    return
                                
                                # 构建预览URL
                                preview_url = f"https://drive.google.com/file/d/{file_id}/preview"
                                
                                # 使用iframe显示视频（高度进一步减小）
                                components.iframe(preview_url, height=180)
                            except Exception as e:
                                st.error(f"处理Google Drive视频时出错: {str(e)}")
                        else:
                            # 其他云存储服务使用普通视频播放器
                            st.video(video_path, start_time=start_seconds, format="video/mp4")
                except Exception as e:
                    st.error(f"Error displaying video: {str(e)}")
        
        # 视频下方显示自动生成的事实陈述与中文字幕
        facts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config', 'facts_translated_results.json'))
        if not hasattr(st.session_state, 'facts_translated_results'):
            if os.path.exists(facts_path):
                with open(facts_path, 'r', encoding='utf-8') as f:
                    st.session_state.facts_translated_results = json.load(f)
            else:
                st.session_state.facts_translated_results = {}
        facts = st.session_state.facts_translated_results.get(video_id, {})
        # print(f"Looking up video_id: {video_id}")
        # print(f"Available keys in facts_translated_results: {st.session_state.facts_translated_results.keys()}")
        with st.expander('显示自动生成的事实陈述与中文字幕', expanded=True):
            if facts:
                st.markdown(f'**事实陈述：** {facts.get("fact_statement", "无")}', unsafe_allow_html=True)
                st.markdown('**中文字幕：**')
                for line in facts.get('subtitles_zh', []):
                    st.markdown(line)
            else:
                st.info('无自动生成信息')
        
        # 场景按钮（视频正下方）
        with scene_container:
            st.markdown("---")
            # 创建两行：上面是时间戳，下面是按钮
            timestamp_cols = st.columns(len(scene_numbers))
            scene_cols = st.columns(len(scene_numbers))
            
            for i, scene_num in enumerate(scene_numbers):
                scene = scenes[i]  # 获取场景信息
                scene_key = f"scene_{scene_num}"
                
                # 显示时间戳
                with timestamp_cols[i]:
                    st.markdown(f"<div style='text-align: center; font-size: 1.1em; color: #666;'>{scene['timestamp']}</div>", 
                              unsafe_allow_html=True)
                
                # 显示场景按钮
                with scene_cols[i]:
                    prefix = "✓" if video_id in existing_feedback and scene_key in existing_feedback[video_id] else "○"
                    if st.button(f"{prefix} {scene_num}", key=f"scene_btn_{scene_num}", 
                               use_container_width=True):
                        # 更新当前场景和视频ID
                        st.session_state.current_scene = scene_num
                        st.session_state.current_video = video_id
                        st.session_state.feedback_saved = False
                        
                        # 立即加载该场景的反馈数据
                        scene_key = str(scene_num)
                        scene_feedback = existing_feedback.get(video_id, {}).get(scene_key, {})
                        
                        # 遍历所有交互，预先设置session_state
                        for idx, _ in enumerate(scenes[scene_numbers.index(scene_num)]['interactions']):
                            feedback_key = f"interaction_{idx}"
                            if feedback_key in scene_feedback and isinstance(scene_feedback[feedback_key], dict):
                                # 设置各个反馈字段的session_state
                                st.session_state[f"scene_{scene_key}_{feedback_key}_speaker"] = scene_feedback[feedback_key].get("speaker_feedback", "")
                                st.session_state[f"scene_{scene_key}_{feedback_key}_target"] = scene_feedback[feedback_key].get("target_feedback", "")
                                st.session_state[f"scene_{scene_key}_{feedback_key}_action_emotion"] = scene_feedback[feedback_key].get("action_emotion_feedback", "")
                                st.session_state[f"scene_{scene_key}_{feedback_key}_mental"] = scene_feedback[feedback_key].get("mental_feedback", "")
                        
                        # 设置笔记的session_state
                        notes_key = f"scene_{scene_key}_notes"
                        st.session_state[notes_key] = scene_feedback.get("notes", "")
                        
                        st.rerun()
        
        # Navigation（移到右下角）
        st.markdown("---")
        with st.expander("Navigation", expanded=False):
            # 路径设置（可折叠）
            new_video_dir = st.text_input(
                "Video Directory Path", 
                value=video_dir,
                help="默认路径：" + DEFAULT_VIDEO_DIR
            )
            new_script_dir = st.text_input(
                "Script Directory Path", 
                value=script_dir,
                help="默认路径：" + DEFAULT_SCRIPT_DIR
            )
            if st.button("保存路径设置", type="primary"):
                if new_video_dir != video_dir or new_script_dir != script_dir:
                    st.session_state.video_dir = new_video_dir
                    st.session_state.script_dir = new_script_dir
                    st.success("路径设置已保存！")
                    st.rerun()
            
            # Current file info
            st.markdown(f"**Current File**: _{selected_file.replace('_script.json', '')}_")
            
            # Script navigation
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("⬅️ Previous", disabled=st.session_state.current_script_index <= 0):
                    st.session_state.current_script_index -= 1
                    # 自动选择第一个场景
                    next_script = script_files[st.session_state.current_script_index]
                    next_script_data = load_script(os.path.join(script_dir, next_script))
                    next_scenes = next_script_data.get('scenes', [])
                    if next_scenes:
                        st.session_state.current_scene = next_scenes[0]['scene_number']
                    st.session_state.current_video = None
                    st.session_state.feedback_saved = False
                    st.rerun()
            
            with col2:
                current_num = st.session_state.current_script_index + 1
                st.markdown(f"**{current_num}/{len(script_files)}**")
            
            with col3:
                if st.button("Next ➡️", disabled=st.session_state.current_script_index >= len(script_files) - 1):
                    st.session_state.current_script_index += 1
                    # 自动选择第一个场景
                    next_script = script_files[st.session_state.current_script_index]
                    next_script_data = load_script(os.path.join(script_dir, next_script))
                    next_scenes = next_script_data.get('scenes', [])
                    if next_scenes:
                        st.session_state.current_scene = next_scenes[0]['scene_number']
                    st.session_state.current_video = None
                    st.session_state.feedback_saved = False
                    st.rerun()
    
    # 右侧标注区域
    with right_col:
        # 在右上角添加模式信息和切换按钮
        mode_col, switch_col = st.columns([4, 1])
        with mode_col:
            st.caption(f"当前模式: {st.session_state.video_mode}")
        with switch_col:
            if st.button("🔄", help="切换模式", type="secondary"):
                st.session_state.video_mode = None
                st.session_state.show_settings = False
                st.rerun()

        if st.session_state.current_scene is not None and st.session_state.current_video == video_id:
            scene = scenes[scene_numbers.index(st.session_state.current_scene)]
            
            # 右侧显示标注界面
            st.subheader("Description")
            st.markdown(f"_{scene['description']}_")
            
            st.subheader("Interactions")
            interaction_feedback = {}
            
            # 获取当前场景的已保存反馈
            scene_key = str(st.session_state.current_scene)
            
            # 获取场景反馈
            scene_feedback = existing_feedback.get(video_id, {}).get(scene_key, {})
            
            for idx, interaction in enumerate(scene['interactions']):
                st.markdown(f"- {interaction}")
                
                # 构造反馈键
                feedback_key = f"interaction_{idx}"
                
                # 获取已保存的反馈 - 检查新旧格式
                saved_speaker_feedback = ""
                saved_target_feedback = ""
                saved_action_emotion_feedback = ""
                saved_mental_feedback = ""
                if feedback_key in scene_feedback:
                    if isinstance(scene_feedback[feedback_key], dict):
                        # 新格式
                        saved_speaker_feedback = scene_feedback[feedback_key].get("speaker_feedback", "")
                        saved_target_feedback = scene_feedback[feedback_key].get("target_feedback", "")
                        saved_action_emotion_feedback = scene_feedback[feedback_key].get("action_emotion_feedback", "")
                        saved_mental_feedback = scene_feedback[feedback_key].get("mental_feedback", "")
                    else:
                        # 旧格式 - 将原有的fact_feedback复制到action_emotion_feedback
                        saved_action_emotion_feedback = scene_feedback[feedback_key].get("fact_feedback", "")
                        saved_mental_feedback = scene_feedback[feedback_key].get("mental_feedback", "")
                
                # 使用session_state来保持状态
                speaker_state_key = f"scene_{scene_key}_{feedback_key}_speaker"
                target_state_key = f"scene_{scene_key}_{feedback_key}_target"
                action_emotion_state_key = f"scene_{scene_key}_{feedback_key}_action_emotion"
                mental_state_key = f"scene_{scene_key}_{feedback_key}_mental"
                
                # 初始化或更新session_state
                if speaker_state_key not in st.session_state:
                    st.session_state[speaker_state_key] = saved_speaker_feedback
                if target_state_key not in st.session_state:
                    st.session_state[target_state_key] = saved_target_feedback
                if action_emotion_state_key not in st.session_state:
                    st.session_state[action_emotion_state_key] = saved_action_emotion_feedback
                if mental_state_key not in st.session_state:
                    st.session_state[mental_state_key] = saved_mental_feedback
                
                # 使用列布局来并排显示所有文本框
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    current_speaker_feedback = st.text_area(
                        "Speaker:",
                        key=speaker_state_key,
                        height=68
                    )
                
                with col2:
                    current_target_feedback = st.text_area(
                        "Target:",
                        key=target_state_key,
                        height=68
                    )
                
                with col3:
                    current_action_emotion_feedback = st.text_area(
                        "Action & Emotion:",
                        key=action_emotion_state_key,
                        height=68
                    )
                
                with col4:
                    current_mental_feedback = st.text_area(
                        "Mental state:",
                        key=mental_state_key,
                        height=68
                    )
                
                # 更新反馈字典，使用新的数据结构
                interaction_feedback[feedback_key] = {
                    "index": idx,
                    "content": interaction,
                    "speaker_feedback": current_speaker_feedback,
                    "target_feedback": current_target_feedback,
                    "action_emotion_feedback": current_action_emotion_feedback,
                    "mental_feedback": current_mental_feedback
                }
            
            st.subheader("Speaker Information")
            for speaker in script_data.get('speaker_mapping', []):
                with st.expander(f"{speaker['character_name']} (ID: {speaker['character_id']})"):
                    st.markdown(f"""
                    - 👤 **Description**: {speaker['visual_description']}
                    - 🎤 **Audio**: {speaker['audio_labels']}
                    - 📝 **Also known as**: {', '.join(speaker['referenced_names'])}
                    """)
            
            # 保存笔记
            notes_key = f"scene_{scene_key}_notes"
            saved_notes = scene_feedback.get("notes", "")
            
            # 更新notes的session_state
            if notes_key not in st.session_state:
                st.session_state[notes_key] = saved_notes
            
            # 显示笔记文本框
            current_notes = st.text_area(
                "Additional Notes",
                key=notes_key,
                height=100
            )
            
            # 构建要保存的反馈数据
            feedback = {}
            
            # 添加每个interaction的反馈到feedback字典
            for key, value in interaction_feedback.items():
                feedback[key] = value
            
            # 添加笔记到feedback字典
            if current_notes.strip() or saved_notes:  # 如果有新内容或原有内容
                feedback["notes"] = current_notes
            
            save_btn, save_next_btn = st.columns(2)
            
            # 保存按钮
            with save_btn:
                if st.button("💾 Save", type="primary"):
                    if save_feedback(video_id, st.session_state.current_scene, feedback, script_data):
                        st.session_state.feedback_saved = True
                        st.rerun()
            
            with save_next_btn:
                current_index = scene_numbers.index(st.session_state.current_scene)
                if current_index < len(scene_numbers) - 1:
                    if st.button("Save & Next →", type="primary"):
                        if save_feedback(video_id, st.session_state.current_scene, feedback, script_data):
                            st.session_state.current_scene = scene_numbers[current_index + 1]
                            st.session_state.feedback_saved = False
                            st.rerun()
                elif current_index == len(scene_numbers) - 1:
                    if st.session_state.current_script_index < len(script_files) - 1:
                        if st.button("Next Video →", type="primary"):
                            if save_feedback(video_id, st.session_state.current_scene, feedback, script_data):
                                st.session_state.current_script_index += 1
                                next_script = script_files[st.session_state.current_script_index]
                                next_script_data = load_script(os.path.join(script_dir, next_script))
                                next_scenes = next_script_data.get('scenes', [])
                                if next_scenes:
                                    st.session_state.current_scene = next_scenes[0]['scene_number']
                                st.session_state.current_video = None
                                st.session_state.feedback_saved = False
                                st.rerun()

            # 在右侧标注区域的底部添加快速跳转按钮
            st.markdown("---")
            jump_col1, jump_col2 = st.columns(2)
            
            # 获取当前视频的文件名（不包含_script.json）
            current_video_name = selected_file.replace('_script.json', '')
            
            # 查找前一个和后一个视频的索引
            prev_video_index = max(0, st.session_state.current_script_index - 1)
            next_video_index = min(len(script_files) - 1, st.session_state.current_script_index + 1)
            
            # 获取前一个和后一个视频的名称
            prev_video_name = script_files[prev_video_index].replace('_script.json', '')
            next_video_name = script_files[next_video_index].replace('_script.json', '')
            
            with jump_col1:
                if st.button(f"⬅️ Previous Video: {prev_video_name}", 
                           disabled=st.session_state.current_script_index <= 0,
                           use_container_width=True):
                    # 清除所有场景相关的session_state
                    keys_to_remove = [key for key in st.session_state.keys() 
                                    if key.startswith("scene_")]
                    for key in keys_to_remove:
                        del st.session_state[key]
                    st.session_state.current_script_index = prev_video_index
                    # 自动选择第一个场景
                    next_script = script_files[prev_video_index]
                    next_script_data = load_script(os.path.join(script_dir, next_script))
                    next_scenes = next_script_data.get('scenes', [])
                    if next_scenes:
                        st.session_state.current_scene = next_scenes[0]['scene_number']
                    st.session_state.current_video = None
                    st.session_state.feedback_saved = False
                    st.rerun()
            
            with jump_col2:
                if st.button(f"Next Video: {next_video_name} ➡️", 
                           disabled=st.session_state.current_script_index >= len(script_files) - 1,
                           use_container_width=True):
                    # 清除所有场景相关的session_state
                    keys_to_remove = [key for key in st.session_state.keys() 
                                    if key.startswith("scene_")]
                    for key in keys_to_remove:
                        del st.session_state[key]
                    st.session_state.current_script_index = next_video_index
                    # 自动选择第一个场景
                    next_script = script_files[next_video_index]
                    next_script_data = load_script(os.path.join(script_dir, next_script))
                    next_scenes = next_script_data.get('scenes', [])
                    if next_scenes:
                        st.session_state.current_scene = next_scenes[0]['scene_number']
                    st.session_state.current_video = None
                    st.session_state.feedback_saved = False
                    st.rerun()

if __name__ == "__main__":
    main() 