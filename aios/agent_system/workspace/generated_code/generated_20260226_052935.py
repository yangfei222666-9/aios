# 需要安装: pip install flask

from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/time', methods=['GET'])
def get_time():
    """返回当前服务器时间"""
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return jsonify({
            'status': 'success',
            'time': current_time
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/calculate', methods=['POST'])
def calculate():
    """接收两个数字并返回它们的和"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '请提供 JSON 数据'
            }), 400
        
        num1 = data.get('num1')
        num2 = data.get('num2')
        
        if num1 is None or num2 is None:
            return jsonify({
                'status': 'error',
                'message': '请提供 num1 和 num2 参数'
            }), 400
        
        # 转换为数字类型
        num1 = float(num1)
        num2 = float(num2)
        
        result = num1 + num2
        
        return jsonify({
            'status': 'success',
            'num1': num1,
            'num2': num2,
            'sum': result
        }), 200
        
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': '参数必须是有效的数字'
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)