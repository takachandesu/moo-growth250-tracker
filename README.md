# moo-growth250-tracker

東証グロース市場250指数の構成銘柄について、当日騰落率ベスト30/ワースト30を毎日自動生成して
ロリポップ（moo-stock-blog.com）にアップロードするシステム。

## 仕組み

```
GitHub Actions (06:30 UTC = 15:30 JST 平日)
   ↓ python scripts/fetch_data.py
yfinance で250銘柄の株価を一括取得
   ↓
public/growth250-data.json を生成
   ↓ FTP-Deploy-Action
ロリポップ /moo-stock-blog/growth250-data.json
   ↓
WordPress固定ページの widget.html が fetch して表示
```

## ファイル

| ファイル | 役割 |
|---|---|
| `scripts/ticker_list.json` | 250銘柄マスター（JPX定期選定ベース） |
| `scripts/fetch_data.py` | データ取得・JSON生成 |
| `.github/workflows/update.yml` | 定時実行 |

## 必要なGitHub Secrets

既存リポジトリ（moo-adr-tracker）と同じ値を設定:

- `LOLIPOP_FTP_HOST` = `ftp.lolipop.jp`
- `LOLIPOP_FTP_USER` = `moo.jp-tako`
- `LOLIPOP_FTP_PASSWORD` = （パスワード）
- `LOLIPOP_FTP_PATH` = `/moo-stock-blog/`

## 銘柄リストの更新

JPXは半年毎（4月末・10月末）に構成銘柄を入替える。
最新版PDFを取得して `scripts/ticker_list.json` を更新する。

最新版URL: https://www.jpx.co.jp/markets/indices/line-up/files/mei2_31_mothers.pdf

## ローカル動作確認

```bash
pip install yfinance pandas
python scripts/fetch_data.py
cat public/growth250-data.json | python -m json.tool | head -50
```

## 出力JSONのスキーマ

```json
{
  "updated_at": "2026-05-26 15:30 JST",
  "source": "Yahoo Finance (yfinance)",
  "index": "東証グロース市場250指数",
  "total_count": 250,
  "skipped_count": 2,
  "best": [
    {"symbol": "...", "code": "...", "name_jp": "...",
     "latest": ..., "prev_close": ..., "change_pct": ...}
  ],
  "worst": [ ... ],
  "all": [ ... ],
  "skipped": [{"symbol": "...", "name": "..."}]
}
```
