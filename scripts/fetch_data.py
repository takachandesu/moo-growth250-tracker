"""
日本株グロース250 ベスト/ワースト ランキング データ取得スクリプト

JPX東証グロース市場250指数の構成銘柄について、
当日騰落率を計算してベスト30/ワースト30のJSONを生成する。

実行: python scripts/fetch_data.py
出力: public/growth250-data.json
"""
from __future__ import annotations
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
MASTER_PATH = ROOT / "scripts" / "ticker_list.json"
OUTPUT_PATH = ROOT / "public" / "growth250-data.json"
JST = timezone(timedelta(hours=9))


def load_master() -> dict:
    with MASTER_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_close_series(df, ticker: str):
    """yfinanceレスポンスから指定tickerのClose系列を抽出"""
    try:
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            lvl0 = set(df.columns.get_level_values(0))
            if ticker in lvl0:
                sub = df[ticker]
                if "Close" in sub.columns:
                    return sub["Close"].dropna()
        else:
            close = df["Close"]
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            return close.dropna()
    except Exception as e:
        print(f"[warn] {ticker}: extract failed ({e})", flush=True)
    return None


def compute_daily_change_pct(series) -> float | None:
    """当日騰落率 (終値 / 前日終値 - 1) × 100"""
    if series is None or len(series) < 2:
        return None
    latest = float(series.iloc[-1])
    prev = float(series.iloc[-2])
    if prev == 0:
        return None
    return (latest / prev - 1.0) * 100.0


def fetch_with_retry(tickers: list[str], max_retries: int = 3):
    """yfinanceで一括取得。失敗したら指数バックオフでリトライ"""
    for attempt in range(max_retries):
        try:
            df = yf.download(
                tickers,
                period="10d",  # 休場日バッファ込み
                progress=False,
                group_by="ticker",
                auto_adjust=False,
                threads=True,
            )
            if not df.empty:
                return df
            print(f"[warn] empty response, attempt {attempt + 1}/{max_retries}", flush=True)
        except Exception as e:
            print(f"[warn] fetch error (attempt {attempt + 1}): {e}", flush=True)
        time.sleep(5 * (attempt + 1))
    return None


def main() -> int:
    print(f"[info] start: {datetime.now(JST).isoformat()}", flush=True)
    master = load_master()
    tickers = [t["symbol"] for t in master["tickers"]]
    print(f"[info] fetching {len(tickers)} tickers...", flush=True)

    df = fetch_with_retry(tickers)
    if df is None:
        print("[error] all fetch attempts failed", flush=True)
        return 1

    results = []
    skipped = []
    for t in master["tickers"]:
        series = get_close_series(df, t["symbol"])
        pct = compute_daily_change_pct(series)
        if pct is None:
            skipped.append({"symbol": t["symbol"], "name": t["name_jp"]})
            continue
        latest = float(series.iloc[-1])
        prev = float(series.iloc[-2])
        results.append({
            "symbol": t["symbol"],
            "code": t["code"],
            "name_jp": t["name_jp"],
            "latest": round(latest, 2),
            "prev_close": round(prev, 2),
            "change_pct": round(pct, 2),
        })

    # 騰落率降順でソート
    results.sort(key=lambda x: x["change_pct"], reverse=True)

    output = {
        "updated_at": datetime.now(JST).strftime("%Y-%m-%d %H:%M JST"),
        "source": "Yahoo Finance (yfinance)",
        "index": "東証グロース市場250指数",
        "total_count": len(results),
        "skipped_count": len(skipped),
        "best": results[:30],
        "worst": list(reversed(results[-30:])),
        "all": results,
        "skipped": skipped,  # デバッグ用：取得できなかった銘柄一覧
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[info] ok={len(results)}, skipped={len(skipped)}", flush=True)
    if skipped:
        sample = ", ".join(s["symbol"] for s in skipped[:10])
        more = f" (他{len(skipped) - 10}件)" if len(skipped) > 10 else ""
        print(f"[info] skipped sample: {sample}{more}", flush=True)
    print(f"[info] done -> {OUTPUT_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
