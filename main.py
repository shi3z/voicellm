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


# ====== LMStudio API呼び出し ======
def call_lmstudio_api(user_input: str) -> str:
    # まずLMStudioのAPIが利用可能かテスト
    try:
        # モデル一覧を取得してAPIの状態をチェック
        models_response = requests.get('http://localhost:1234/v1/models', timeout=5)
        print(f"Models API response: {models_response.status_code}")
        
        if models_response.status_code != 200:
            print("LMStudio API not available, using fallback")
            return f"LMStudioに接続できません。『{user_input}』について承知しました。"
        
        models_data = models_response.json()
        print(f"Available models: {[model.get('id', 'unknown') for model in models_data.get('data', [])]}")
        
        # 指定されたモデルを使用
        model_id = 'openai/gpt-oss-120b'
        
        print(f"Using model: {model_id}")
        
        # チャット completions API を呼び出し
        response = requests.post(
            'http://localhost:1234/v1/chat/completions',
            headers={'Content-Type': 'application/json'},
            json={
                'model': model_id,
                'messages': [
                    {
                        'role': 'system',
                        'content': 'あなたは親しみやすい日本語のアシスタントです。簡潔で自然な日本語で応答してください。英語は一歳使わないでください'
                    },
                    {
                        'role': 'user',
                        'content': user_input
                    }
                ],
                'max_tokens': 1000,
                'temperature': 0.7,
                'stream': False
            },
            timeout=30
        )
        
        print(f"Chat API response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data['choices'][0]['message']['content']
            print(ai_response)
            # <thinking>タグとその内容を削除
            import re
            ai_response = re.sub(r'<thinking>.*?</thinking>', '', ai_response, flags=re.DOTALL)
            ai_response = ai_response.strip()
            
            print(f"AI response: {ai_response[:100]}...")  # 最初の100文字をログ
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

@app.route('/api/chat', methods=['POST'])
def chat_api():
    try:
        data = request.get_json()
        user_input = data.get('message', '')
        
        if not user_input:
            return jsonify({'error': 'No message provided'}), 400
        
        # LMStudio APIを呼び出し
        response = call_lmstudio_api(user_input)
        
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
