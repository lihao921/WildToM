import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import httplib2
import socket
from google_auth_httplib2 import AuthorizedHttp

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# 代理设置
PROXY_HOST = "127.0.0.1"  # 修改为你的代理地址
PROXY_PORT = 7890        # 修改为你的代理端口
USE_PROXY = True         # 是否使用代理

def create_http_with_proxy():
    """创建带有代理设置的HTTP对象"""
    if USE_PROXY:
        proxy_info = httplib2.ProxyInfo(
            proxy_type=httplib2.socks.PROXY_TYPE_HTTP,
            proxy_host=PROXY_HOST,
            proxy_port=PROXY_PORT
        )
        return httplib2.Http(proxy_info=proxy_info, timeout=30)
    return httplib2.Http(timeout=30)

def get_gdrive_service():
    """获取Google Drive服务实例"""
    creds = None
    
    # 设置socket超时
    socket.setdefaulttimeout(30)
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            if USE_PROXY:
                flow.authorized_http = create_http_with_proxy()
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    # 创建服务实例
    http = create_http_with_proxy()
    authorized_http = AuthorizedHttp(creds, http=http)
    service = build('drive', 'v3', http=authorized_http)
    return service

def extract_folder_id(folder_url):
    """
    从Google Drive文件夹URL中提取文件夹ID
    支持以下格式:
    - https://drive.google.com/drive/folders/{folder_id}?usp=drive_link
    - https://drive.google.com/drive/folders/{folder_id}
    - {folder_id}
    """
    try:
        if 'drive.google.com' in folder_url:
            # 从完整URL中提取
            import re
            match = re.search(r'folders/([^/?]+)', folder_url)
            if match:
                return match.group(1)
        # 如果输入的直接是folder_id
        return folder_url.strip()
    except Exception as e:
        print(f"Error extracting folder ID: {str(e)}")
        return None

def list_videos_in_folder(folder_id_or_url, mode='cloud'):
    """
    获取文件夹中的视频列表
    Args:
        folder_id_or_url: Google Drive文件夹ID或完整URL
        mode: 'cloud' 用于云端流式播放, 'local' 用于本地下载播放
    Returns:
        包含视频ID和URL的字典
    """
    try:
        folder_id = extract_folder_id(folder_id_or_url)
        if not folder_id:
            raise ValueError("Invalid folder ID or URL")

        service = get_gdrive_service()
        # 不在查询中过滤文件类型，而是获取所有文件
        query = f"'{folder_id}' in parents"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            pageSize=1000  # 增加页面大小以确保获取所有文件
        ).execute()
        
        files = results.get('files', [])
        if not files:
            print(f"No files found in folder {folder_id}")
            return {}

        mapping = {}
        for file in files:
            # 只处理视频文件
            if not file['mimeType'].startswith('video/'):
                continue
                
            # 获取原始文件名
            original_name = file['name']
            if original_name.lower().endswith('.mp4'):
                original_name = original_name[:-4]
            
            # 创建不同版本的视频ID用于匹配
            video_ids = {
                original_name,  # 原始名称
                original_name.lstrip('-'),  # 移除开头的减号
                f"-{original_name.lstrip('-')}"  # 添加减号版本
            }
            
            file_id = file['id']
            url = f"https://drive.google.com/file/d/{file_id}/preview" if mode == 'cloud' else f"https://drive.google.com/uc?id={file_id}&export=download"
            
            # 为所有可能的视频ID版本创建映射
            for vid in video_ids:
                if vid:  # 确保ID不为空
                    mapping[vid] = url
        
        print(f"Found {len(files)} files in the folder, created {len(mapping)} video mappings")
        return mapping
    except Exception as e:
        print(f"Error in list_videos_in_folder: {str(e)}")
        return {} # Return empty dict instead of raising to handle errors gracefully 