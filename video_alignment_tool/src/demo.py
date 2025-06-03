from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# 初始化 Google 授权
gauth = GoogleAuth()

# 使用本地服务器认证 (会自动弹出浏览器登录)
gauth.LocalWebserverAuth()  

# 认证成功后，创建 GoogleDrive 实例
drive = GoogleDrive(gauth)
print("认证成功")
