"""
测试 WebSocket 连接
"""
import socketio
import time

# 创建 Socket.IO 客户端
sio = socketio.Client()

@sio.event
def connect():
    print('[测试] 已连接到服务器')

@sio.event
def disconnect():
    print('[测试] 已断开连接')

@sio.on('authenticated')
def on_authenticated(data):
    print(f'[测试] 认证成功: {data}')

@sio.on('auth_error')
def on_auth_error(data):
    print(f'[测试] 认证失败: {data}')

@sio.on('incoming_call')
def on_incoming_call(data):
    print(f'[测试] 收到来电: {data}')

def test_connection(token):
    """测试 WebSocket 连接"""
    try:
        print('[测试] 正在连接到 http://localhost:5000...')
        sio.connect('http://localhost:5000', transports=['websocket', 'polling'])
        
        print('[测试] 发送认证请求...')
        sio.emit('authenticate', {'token': token})
        
        # 等待响应
        time.sleep(2)
        
        print('[测试] 断开连接...')
        sio.disconnect()
        
    except Exception as e:
        print(f'[测试] 错误: {e}')

if __name__ == '__main__':
    # 需要一个有效的 JWT token 来测试
    # 可以从浏览器的 localStorage 中获取
    print('WebSocket 测试脚本')
    print('请提供一个有效的 JWT token 来测试连接')
    print('可以从浏览器控制台运行: localStorage.getItem("token")')
    
    token = input('请输入 token: ').strip()
    if token:
        test_connection(token)
    else:
        print('未提供 token，跳过测试')
