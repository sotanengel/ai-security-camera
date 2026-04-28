# ai-security-camera

ローカル VLM による二段パイプライン（軽量検知 → VLM 本判定）の **Phase 1 PoC** 実装です。要件の全体像はプロジェクト外の要件定義書（LLM監視カメラ）に準拠します。

## 前提

- Python 3.11+
- 推奨: [Ollama](https://ollama.com/)（VLM）、[go2rtc](https://github.com/AlexxIT/go2rtc)（ストリーム中継）
- Docker 利用時は `docker compose`（`docker-compose.yml` 参照）

## 開発環境

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check src tests
```

### Takumi Guard（PyPI / 任意）

悪意あるパッケージのブロック用に [Takumi Guard](https://flatt.tech/takumi-guard) のトークンを使い、pip / uv の index を `pypi.flatt.tech` に向けます。**トークンはリポジトリに含めないでください。**

- **ローカル（pip）**

  ```bash
  pip config set global.index-url "https://token:tg_YOUR_TOKEN@pypi.flatt.tech/simple/"
  ```

- **uv**

  ```bash
  export UV_INDEX_URL="https://token:tg_YOUR_TOKEN@pypi.flatt.tech/simple/"
  ```

- **CI（GitHub Actions）**  
  リポジトリの **Secrets** に `TAKUMI_GUARD_TOKEN` を登録すると、ワークフローが Guard 経由で `pip install` します。未設定の場合は **パブリック PyPI** でインストールします（フォークや外部コントリビュータ向け）。

- **動作確認（任意）**  
  npm エコシステムでは `npm install @panda-guard/test-malicious` が `403` になることで Guard の有効性を確認できます（[ドキュメント](https://flatt.tech) 参照）。

## 設定（環境変数）

接頭辞 `ASC_`（例: `ASC_OLLAMA_BASE_URL=http://127.0.0.1:11434`）。`.env` を置くと読み込みます。本番では `ASC_API_TOKEN` を必ず変更してください。

## API

FastAPI 起動例:

```bash
uvicorn ai_security_camera.api.app:app --app-dir src --host 0.0.0.0 --port 8000
```

`Authorization: Bearer <ASC_API_TOKEN>` で保護されたエンドポイントがあります。

## Docker（go2rtc + Ollama + アプリ）

```bash
cp .env.example .env
# .env を編集してから
docker compose up -d
```

## 実行環境レベル（要件書 §7.2 要約）

| Level | 環境 | 主な役割 |
| --- | --- | --- |
| 1 | ラズパイ | 軽量検知・常時取得、VLM は上位へオフロード可 |
| 2 | スマホ | 補助 UI、軽量 on-device、通知確認 |
| 3 | ノート PC | 本 PoC の標準、中型 VLM、テンプレ・ルール編集 |
| 4 | ゲーミング PC | 大型 VLM サーバ、学習・配布元 |

## ライセンス

See [LICENSE](LICENSE).
