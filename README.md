# Local LLM音声応答システム

sherpa-onnxとLMStudioを使用したローカル音声対話システムです。音声認識、LLM応答、音声合成を組み合わせて、完全にプライベートな音声アシスタントを構築できます。

## 特徴

- 🎤 **音声認識**: sherpa-onnx WebAssemblyによるリアルタイム音声認識
- 🤖 **LLM応答**: LMStudioとの連携による自然言語応答
- 🗣️ **多言語音声合成**: 日本語・英語の自動切り替え音声合成
- 💬 **マークダウン対応**: 応答テキストのマークダウン表記をサポート
- 🔒 **プライベート**: すべての処理がローカルで実行

## システム構成

```
音声入力 → sherpa-onnx → Python API → LMStudio → 音声合成
                            ↓
                      Web Interface
```

## 必要な環境

- Python 3.8+
- LMStudio
- macOS (音声合成にSystem Voicesを使用)

## インストール

1. リポジトリをクローン
```bash
git clone <リポジトリURL>
cd voiceui
```

2. Python依存関係をインストール
```bash
pip install -r requirements.txt
```

3. LMStudioをインストールしてモデルをロード
   - [LMStudio](https://lmstudio.ai/)をダウンロード
   - `openai/gpt-oss-120b`モデルをロード
   - ポート1234でAPIサーバーを起動

## 使用方法

1. **LMStudioを起動**
   ```bash
   # LMStudioでAPIサーバーを localhost:1234 で起動
   ```

2. **Pythonサーバーを起動**
   ```bash
   python main.py server
   ```

3. **ブラウザでアクセス**
   ```
   http://localhost:8000
   ```

4. **音声対話を開始**
   - "Start"ボタンをクリック
   - マイクに向かって話す
   - AIが音声で応答

## ファイル構成

```
voiceui/
├── main.py                 # PythonサーバーとLMStudio API連携
├── index.html             # Web UI
├── app-vad-asr.js        # 音声認識制御
├── sherpa-onnx-*.js      # sherpa-onnx WebAssembly
├── requirements.txt       # Python依存関係
└── README.md             # このファイル
```

## 主要機能

### 音声認識
- VAD (Voice Activity Detection) による音声区間検出
- sherpa-onnx WebAssemblyによる高精度音声認識
- 日本語音声認識対応

### LLM応答
- LMStudio APIとの連携
- `<thinking>`タグの自動削除
- エラーハンドリング付きフォールバック

### 音声合成
- Web Speech API使用
- 日本語・英語の自動言語検出
- 自然な多言語音声合成

### UI機能
- リアルタイム会話履歴表示
- マークダウン形式の応答表示
- レスポンシブデザイン

## カスタマイズ

### モデル変更
`main.py`の`model_id`を変更してください:
```python
model_id = 'your-model-name'
```

### システムプロンプト変更
`main.py`の`content`を編集してください:
```python
'content': 'あなたは親しみやすい日本語のアシスタントです。'
```

### 音声設定
`index.html`の音声合成設定を調整できます:
```javascript
utterance.rate = 0.9;    // 話速
utterance.pitch = 1.0;   // 音高
utterance.volume = 1.0;  // 音量
```

## トラブルシューティング

### ポート5000が使用中
macOSのAirPlayが使用している場合があります:
```bash
# システム設定 > 一般 > AirDropとHandoff > AirPlayレシーバー を無効化
```

### 音声が出ない
1. ブラウザの音声権限を確認
2. システムの音声設定を確認
3. 日本語/英語音声がインストールされているか確認

### LMStudio接続エラー
1. LMStudioが起動しているか確認
2. APIサーバーが有効になっているか確認
3. モデルがロードされているか確認

## 技術詳細

### 音声認識フロー
```
マイク → VAD → 音声区間検出 → sherpa-onnx → テキスト
```

### API通信フロー
```
JavaScript → Flask API → LMStudio API → 応答
```

### 多言語音声合成
- 正規表現による英語部分検出
- セグメント別言語設定
- 順次音声合成再生

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

プルリクエストやイシューの報告を歓迎します。

## 謝辞

- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) - 音声認識エンジン
- [LMStudio](https://lmstudio.ai/) - ローカルLLM実行環境
- [Marked.js](https://marked.js.org/) - マークダウンパーサー