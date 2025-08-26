import os
import sys
import time
import wave
import queue
import subprocess
import threading
import requests
import json
from dataclasses import dataclass
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS

import numpy as np
import sounddevice as sd
import webrtcvad



# Apple Silicon なら "coreml" を優先。ダメなら "cpu"
PROVIDER_ORDER = ["coreml", "cpu"]

# ====== ユーティリティ ======
def float_to_int16(audio_f32: np.ndarray) -> bytes:
    x = np.clip(audio_f32, -1.0, 1.0)
    return (x * 32767.0).astype(np.int16).tobytes()

def bytes_to_float32(pcm_bytes: bytes) -> np.ndarray:
    x = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    return x


# ====== グローバル設定 ======
current_model_id = 'openai/gpt-oss-120b'
current_max_tokens = 1000
conversation_history = []  # 会話履歴を保存

# ====== LMStudio API呼び出し ======
def execute_javascript(code: str) -> str:
    """JavaScriptコードを安全に実行"""
    try:
        # Node.jsでJavaScriptを実行
        result = subprocess.run(
            ['node', '-e', code], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            return f"Output: {result.stdout.strip()}"
        else:
            return f"Error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out"
    except FileNotFoundError:
        return "Error: Node.js not found. Please install Node.js"
    except Exception as e:
        return f"Error: {str(e)}"

def execute_python(code: str) -> str:
    """Pythonコードを安全に実行"""
    try:
        # Pythonコードを実行
        result = subprocess.run(
            ['python3', '-c', code], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            return f"Output: {result.stdout.strip()}"
        else:
            return f"Error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out"
    except Exception as e:
        return f"Error: {str(e)}"

def get_available_tools():
    """LMStudioで利用可能なツールを定義"""
    return [
        {
            "type": "function",
            "function": {
                "name": "javascript",
                "description": "Execute JavaScript code safely",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "JavaScript code to execute"
                        }
                    },
                    "required": ["code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "python",
                "description": "Execute Python code safely",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute"
                        }
                    },
                    "required": ["code"]
                }
            }
        }
    ]

def call_lmstudio_api(user_input: str, model_id: str = None, max_tokens: int = None, enable_tools: bool = False, system_prompt: str = None) -> str:
    # まずLMStudioのAPIが利用可能かテスト
    try:
        # モデル一覧を取得してAPIの状態をチェック
        models_response = requests.get('http://localhost:1234/api/v0/models', timeout=5)
        print(f"Models API response: {models_response.status_code}")
        
        if models_response.status_code != 200:
            print("LMStudio API not available, using fallback")
            return f"LMStudioに接続できません。『{user_input}』について承知しました。"
        
        models_data = models_response.json()
        print(f"Available models: {[model.get('id', 'unknown') for model in models_data.get('data', [])]}")
        
        # 指定されたモデルを使用（パラメータまたはグローバル設定）
        if model_id is None:
            model_id = current_model_id
        if max_tokens is None:
            max_tokens = current_max_tokens
        
        print(f"Using model: {model_id}")
        
        # システムメッセージを設定
        default_system_prompt = 'あなたは親しみやすい日本語のアシスタントです。簡潔で自然な日本語で応答してください。英語は一切使わないでください'
        system_message = {
            'role': 'system',
            'content': system_prompt if system_prompt else default_system_prompt
        }
        
        # 会話履歴に新しいユーザーメッセージを追加（空の場合はスキップ）
        global conversation_history
        if user_input.strip():
            conversation_history.append({
                'role': 'user',
                'content': user_input
            })
        
        # システムメッセージ + 会話履歴でメッセージリストを構築
        messages = [system_message] + conversation_history
        
        # API呼び出し用のペイロードを構築
        payload = {
            'model': model_id,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': 0.7,
            'stream': False
        }
        
        # ツールが有効な場合は追加
        if enable_tools:
            payload['tools'] = get_available_tools()
            payload['tool_choice'] = 'auto'
        
        # チャット completions API を呼び出し
        response = requests.post(
            'http://localhost:1234/v1/chat/completions',
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=30
        )
        
        print(f"Chat API response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            message = data['choices'][0]['message']
            
            # ツール呼び出しがある場合
            if message.get('tool_calls'):
                print(f"Tool calls detected: {len(message['tool_calls'])}")
                
                # アシスタントのメッセージを履歴に追加
                conversation_history.append(message)
                
                # 各ツール呼び出しを実行
                for tool_call in message['tool_calls']:
                    function_name = tool_call['function']['name']
                    arguments = json.loads(tool_call['function']['arguments'])
                    
                    print(f"Executing tool: {function_name}")
                    print(f"Arguments: {arguments}")
                    
                    # ツールの結果を取得
                    if function_name == 'javascript':
                        tool_result = execute_javascript(arguments['code'])
                    elif function_name == 'python':
                        tool_result = execute_python(arguments['code'])
                    else:
                        tool_result = f"Unknown tool: {function_name}"
                    
                    # ツールの結果を履歴に追加
                    conversation_history.append({
                        'role': 'tool',
                        'tool_call_id': tool_call['id'],
                        'name': function_name,
                        'content': tool_result
                    })
                
                # ツールの結果を含めて再度API呼び出し
                return call_lmstudio_api("", model_id, max_tokens, enable_tools=False)
            
            else:
                # 通常のレスポンス処理
                ai_response = message.get('content', '')
                print(ai_response)
                
                # <thinking>タグとその内容を削除
                import re
                ai_response = re.sub(r'<thinking>.*?</thinking>', '', ai_response, flags=re.DOTALL)
                ai_response = ai_response.strip()
                
                # 会話履歴にAIの応答を追加
                conversation_history.append({
                    'role': 'assistant',
                    'content': ai_response
                })
                
                print(f"AI response: {ai_response[:100]}...")  # 最初の100文字をログ
                print(f"Conversation history length: {len(conversation_history)}")
                
                return ai_response
        else:
            print(f"Chat API error: {response.status_code}, {response.text}")
            return f"LMStudioからエラーが返されました。『{user_input}』について承知しました。"
            
    except requests.exceptions.ConnectionError:
        print("LMStudio connection failed - server not running?")
        return f"LMStudioが起動していないようです。『{user_input}』について承知しました。"
    except requests.exceptions.RequestException as e:
        print(f"LMStudio API error: {e}")
        return f"LMStudioでエラーが発生しました。『{user_input}』について承知しました。"

# ====== Flask Web & API サーバー ======
app = Flask(__name__)
CORS(app)  # CORS問題を解決

# 静的ファイルの配信
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

# モデル一覧取得エンドポイント
@app.route('/api/models', methods=['GET'])
def get_models():
    try:
        models_response = requests.get('http://localhost:1234/api/v0/models', timeout=5)
        if models_response.status_code == 200:
            models_data = models_response.json()
            print(f"Raw models data from /api/v0/models: {json.dumps(models_data, indent=2)[:500]}...")  # 最初の500文字のみ表示
            
            # v0 APIからmax_context_lengthを直接取得
            models_with_context = []
            for model in models_data.get('data', []):
                model_info = {
                    'id': model.get('id'),
                    'object': model.get('object', 'model'),
                    'owned_by': model.get('publisher', 'organization_owner'),
                    'max_context_length': model.get('max_context_length', 4096),
                    'state': model.get('state', 'unknown'),
                    'type': model.get('type', 'llm')
                }
                models_with_context.append(model_info)
            
            print("Retrieved context lengths:", [(m['id'], m['max_context_length']) for m in models_with_context[:3]])
            return jsonify({
                'models': models_with_context,
                'status': 'success'
            })
        else:
            return jsonify({
                'error': f'LMStudio API returned status {models_response.status_code}',
                'status': 'error'
            }), 500
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'  
        }), 500

# 設定更新エンドポイント
@app.route('/api/config', methods=['POST'])
def update_config():
    global current_model_id, current_max_tokens
    try:
        data = request.get_json()
        
        if 'model_id' in data:
            current_model_id = data['model_id']
        if 'max_tokens' in data:
            current_max_tokens = int(data['max_tokens'])
            
        return jsonify({
            'model_id': current_model_id,
            'max_tokens': current_max_tokens,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

# 会話履歴関連エンドポイント
@app.route('/api/conversation', methods=['DELETE'])
def clear_conversation():
    global conversation_history
    conversation_history = []
    return jsonify({
        'message': 'Conversation history cleared',
        'status': 'success'
    })

@app.route('/api/conversation', methods=['GET'])
def get_conversation():
    return jsonify({
        'conversation': conversation_history,
        'length': len(conversation_history),
        'status': 'success'
    })

# 現在の設定取得エンドポイント
@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        'model_id': current_model_id,
        'max_tokens': current_max_tokens,
        'status': 'success'
    })

# 利用可能なツール一覧エンドポイント
@app.route('/api/tools', methods=['GET'])
def get_tools():
    return jsonify({
        'tools': get_available_tools(),
        'status': 'success'
    })

@app.route('/api/chat', methods=['POST'])
def chat_api():
    try:
        data = request.get_json()
        user_input = data.get('message', '')
        model_id = data.get('model_id')  # オプション
        max_tokens = data.get('max_tokens')  # オプション
        enable_tools = data.get('enable_tools', False)  # ツール有効化
        system_prompt = data.get('system_prompt')  # システムプロンプト
        
        if not user_input:
            return jsonify({'error': 'No message provided'}), 400
        
        # LMStudio APIを呼び出し
        response = call_lmstudio_api(user_input, model_id, max_tokens, enable_tools, system_prompt)
        
        return jsonify({
            'response': response,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'API server is running'})

# ====== 応答ロジック（フォールバック用） ======
def generate_reply(text: str) -> str:
    return call_lmstudio_api(text)

# ====== サーバー起動 ======
def run_server():
    print("Starting Web & API server on http://localhost:8000")
    print("Available endpoints:")
    print("  GET  /           - Voice UI Web App")
    print("  POST /api/chat   - Chat with LMStudio")
    print("  GET  /api/health - Health check")
    print("  GET  /<filename> - Static files")
    app.run(host='0.0.0.0', port=8000, debug=False)
if __name__ == "__main__":
    run_server()
