# -*- coding: utf-8 -*-
# 从凌晨1点到6点就写了个 JavaServer 的状态获取，我这速度无敌了

from flask import Flask, render_template, request, jsonify
from mcstatus import JavaServer, BedrockServer
from flask_cors import CORS

# 我尝试了一下外部调用，出乎意料的可以跑
from srv_resolve import resolve_srv_record

import base64

app = Flask(__name__)
app.json.sort_keys = False
app.json.ensure_ascii = False
app.json.mimetype = 'application/json;charset=UTF-8'
app.json.compact = False
CORS(app)

http_code = None

@app.route('/')
def index():
    return render_template('index.html')

# 这里是 Java 服务器的状态获取逻辑
# 不管你有没有选择 srv 记录，他都会跑一遍来验证
@app.route('/java')
def java_motd():
    ip = request.args.get('ip') or ''
    srv = request.args.get('srv', 'true').lower()
    if not ip:
        http_code = 400
        return jsonify(
            {'status': http_code, 
             'message': '缺少 ip 参数',
             'usage': '/java?ip=<ip>&srv=<true|false>',
             'tip': '第一次解析可能延迟很高，你可以考虑二次调用'
             }
            ), http_code

    try:
        # 赋予默认变量
        address = ip
        port = 25565
        is_srv = srv
        resolved_type = 'normal'
        http_code = 200
        srv_warning_msg = None
        
        # 霸道总裁强制爱(不是)
        # 就是判断两个字符啦！qwq
        if srv not in ['true', 'false']:
            http_code = 400
            srv_error_msg = {
                'status': f'Ciallo～(∠・ω< )⌒★',
                'error': 'srv 参数只能为 true 或 false'
            }
            return jsonify(srv_error_msg), http_code
        
        if is_srv == 'true':
            # 如果没有冒号，尝试SRV解析
            if ':' not in ip:
                try:
                    address, port, resolved_type = resolve_srv_record(ip)
                except Exception as e:
                    print(f"SRV记录解析失败: {str(e)}")

            # 如果有冒号，直接解析地址和端口
            else:
                address, port_str = ip.split(':', 1)
                port = int(port_str)
                print(f"使用指定的地址和端口: {address}:{port}")

        else:
            # 禁用SRV解析，直接处理IP地址
            if ':' in ip:
                address, port_str = ip.split(':', 1)
                port = int(port_str)

            # 如果没有端口，使用默认端口25565
            else:
                port = 25565
                
                # 测试连接
                try:
                    test_server = JavaServer.lookup(f"{address}:{port}")
                    test_status = test_server.status()
                except Exception as e:
                    srv_warning_msg = f'此解析可能为 srv 解析,已自动转换'
                    # 转换为 srv 解析
                    resolve_srv_record(ip)
                    address, port, resolved_type = resolve_srv_record(ip)
        
        # 调用 mcstatus 获取服务器状态
        server = JavaServer.lookup(f'{address}:{port}')
        status = server.status()

        # 处理在线玩家名字
        player_name = []
        if status.players.sample:
            player_name = [player.name for player in status.players.sample]

        # 处理服务器图标
        icon_data = None
        if status.icon:
            icon_str = status.icon.strip()
                
            # 添加Base64前缀
            if not icon_str.startswith('data:image/png;base64,'):
                icon_str = f"data:image/png;base64,{icon_str}"
                
            # 验证Base64格式
            try:
                base64.b64decode(icon_str.split(',', 1)[-1])
                icon_data = icon_str
            except Exception as e:
                print(f"无效的Base64图标数据: {str(e)}")

        # 准备返回数据
        java_data = {
            'status': http_code,
            'ip': f"{address}:{port}",
            'description': status.description,
            'type': resolved_type,
            'version': status.version.name,
            'latency': f"{status.latency}ms",
            'players': {
                'current': status.players.online,
                'max': status.players.max,
                'player_name': player_name
            },
            'icon': icon_data
        }
        
        # 如果有 srv 解析警告，添加到返回数据中
        if srv_warning_msg:
            java_data['warning'] = srv_warning_msg

        return jsonify(java_data), http_code

    # 蜜汁错误，我不管了啊啊啊啊啊啊啊啊啊啊！！！！！！！！
    except Exception as e:
        unknow_error = f"无法获取服务器信息: {str(e)}"
        http_code = 500
        unknow_error_msg = {
            'status': http_code,
            'ip': f"{address}:{port}",
            'error': unknow_error
        }
        return jsonify(unknow_error_msg), http_code

# 这里是 Bedrock 服务器的状态获取逻辑
# 我已经做过功课了，他没有图标和在线玩家名字显示的！！！
@app.route('/be')
def bedrock_motd():
    ip = request.args.get('ip') or ''
    if not ip:
        http_code = 400
        return jsonify(
            {'status': f'Ciallo～(∠・ω< )⌒★', 
             'message': '缺少 ip 参数',
             'usage': '/be?ip=<ip>',
             'tip': '第一次解析可能延迟很高，你可以考虑二次调用'
             }
            ), http_code

    try:
        # 赋予默认变量
        address = ip
        port = 19132
        http_code = 200

        if ':' in ip:
            address, port_str = ip.split(':', 1)
            port = int(port_str)
            print(f"使用指定的地址和端口: {address}:{port}")

        server = BedrockServer.lookup(f'{address}:{port}')
        status = server.status()

        # 准备返回数据
        bedrock_data = {
            'status': http_code,
            'ip': f"{address}:{port}",
            'description': status.description,
            'version': status.version.name,
            'latency': f"{status.latency}ms",
            'players': {
                'current': status.players.online,
                'max': status.players.max
                }
        }   
        return jsonify(bedrock_data), http_code
    except Exception as e:
        unknow_error = f"无法获取服务器信息: {str(e)}"
        http_code = 500
        unknow_error_msg = {
            'status': http_code,
            'ip': f"{address}:{port}",
            'error': unknow_error
        }
        return jsonify(unknow_error_msg), http_code

if __name__ == '__main__':
    app.run(debug=True,port = 5000)
