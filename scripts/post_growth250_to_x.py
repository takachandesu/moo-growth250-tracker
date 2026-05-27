"""
日本株グロース250 当日騰落率ベスト/ワーストを毎日Xに投稿するスクリプト。
growth250-data.json を取得 → ベスト4・ワースト4を1ツイートで投稿。

post_adr_to_x.py をベースに、Growth 250用にカスタマイズ。
"""
from __future__ import annotations

import os
import sys
import unicodedata
from datetime import datetime, timezone, timedelta

import requests
import tweepy


JST = timezone(timedelta(hours=9))
JSON_URL = "https://moo-stock-blog.com/growth250-data.json"

# 長い銘柄名の短縮表記（X 280文字制限に収めるため）
# Growth 250は大型株より短い名前が多いが、長い英字混在名を中心に登録
NAME_SHORT = {
    "アンビション　ＤＸ　ホールディングス": "アンビションDX",
    "ＡｎｙＭｉｎｄ　Ｇｒｏｕｐ": "AnyMind",
    "ＳＢＩインシュアランスグループ": "SBIインシュ",
    "ＴＷＯＳＴＯＮＥ＆Ｓｏｎｓ": "TWOSTONE",
    "グローバルセキュリティエキスパート": "GSX",
    "ペイクラウドホールディングス": "ペイクラウド",
    "ファーストアカウンティング": "ファスト会計",
    "バリュエンスホールディングス": "バリュエンス",
    "ライズ・コンサルティング・グループ": "ライズC",
    "バルテス・ホールディングス": "バルテス",
    "スリー・ディー・マトリックス": "3Dマトリ",
    "アクセルスペースホールディングス": "アクセルスペ",
    "ＳＭ　ＥＮＴＥＲＴＡＩＮＭＥＮＴ　ＪＡＰＡＮ": "SM ENT",
    "ＨＡＮＡＴＯＵＲ　ＪＡＰＡＮ": "HANATOUR",
    "シンメンテホールディングス": "シンメンテ",
    "フリークアウト・ホールディングス": "フリークアウト",
    "トランザクション・メディア・ネットワークス": "TMN",
    "サイバーセキュリティクラウド": "CSC",
    "プロパティデータバンク": "プロパティDB",
    "バンク・オブ・イノベーション": "BoI",
    "コアコンセプト・テクノロジー": "コアコンセプト",
    "ＲＯＢＯＴ　ＰＡＹＭＥＮＴ": "ROBOTPAY",
    "くふうカンパニーホールディングス": "くふうCo",
    "ＡｅｒｏＥｄｇｅ": "AeroEdge",
    "ＢｕｙＳｅｌｌ　Ｔｅｃｈｎｏｌｏｇｉｅｓ": "BuySell",
    "ジャパン・ティッシュエンジニアリング": "J-TEC",
    "アドバンスト・メディア": "アドバンスト",
    "ＦＦＲＩセキュリティ": "FFRIセキュ",
    "リネットジャパングループ": "リネットJP",
    "ＧＡ　ｔｅｃｈｎｏｌｏｇｉｅｓ": "GA tech",
    "ヘッドウォータース": "ヘッドWS",
    "サイバートラスト": "サイバート",
    "アイキューブドシステムズ": "アイキューブ",
    "Ｆｉｎａｔｅｘｔホールディングス": "Finatext",
    "Ｃｈｏｒｄｉａ　Ｔｈｅｒａｐｅｕｔｉｃｓ": "Chordia",
    "ＳＢＩレオスひふみ": "SBIレオス",
    "ＧＭＯコマース": "GMOコマース",
    "Ｓｙｎｓｐｅｃｔｉｖｅ": "Synspective",
    "ククレブ・アドバイザーズ": "ククレブ",
    "Ｌｉｂｅｒａｗａｒｅ": "Liberaware",
    "Ｈｅａｒｔｓｅｅｄ": "Heartseed",
    "Ａｉロボティクス": "AIロボ",
    "技術承継機構": "技術承継機",
    "ダイナミックマッププラットフォーム": "ダイナミMP",
    "ＺｅｎｍｕＴｅｃｈ": "ZenmuTech",
    "プログレス・テクノロジーズ　グループ": "プログレス",
    "アストロスケールホールディングス": "アストロ",
    "アイドマ・ホールディングス": "アイドマ",
    "コンフィデンス・インターワークス": "コンフィデンス",
    "セレンディップ・ホールディングス": "セレンディプ",
    "ハルメクホールディングス": "ハルメク",
    "日本ホスピスホールディングス": "日本ホスピス",
    "フィードフォースグループ": "フィードフォース",
    "フロンティアインターナショナル": "フロンティア",
    "ＨＹＵＧＡ　ＰＲＩＭＡＲＹ　ＣＡＲＥ": "HYUGA",
    "ヒューマンテクノロジーズ": "ヒューマンT",
    "ファイナテキスト": "Finatext",
    "ライトアップ": "ライトアップ",
    "Ｊストリーム": "Jストリーム",
    "クラウドワークス": "クラウドWK",
}


def fetch_data():
    """ロリポップから growth250-data.json を取得（WAF回避のためUser-Agent指定）"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }
    r = requests.get(JSON_URL, timeout=15, headers=headers)
    r.raise_for_status()
    return r.json()


def short_name(name, max_len=8):
    """銘柄名を短く整形（全角英数字は半角に正規化してX文字数を節約）"""
    # 辞書ヒット時はそれを採用、なければ正規化＋切詰め
    if name in NAME_SHORT:
        name = NAME_SHORT[name]
    # NFKC正規化で全角英数記号→半角化（X weighted count を半減できる）
    name = unicodedata.normalize("NFKC", name)
    if len(name) <= max_len:
        return name
    return name[:max_len]


def format_line(rank, item):
    """1行整形: '1. 4385 メルカリ +14.61%'"""
    code = item.get("code", "----")
    name = short_name(item.get("name_jp", ""))
    pct = item.get("change_pct", 0.0)
    sign = "+" if pct >= 0 else ""
    return f"{rank}. {code} {name} {sign}{pct:.2f}%"


def _weighted_length(text: str) -> int:
    """Twitter weighted-length (V2) 近似: ASCII/Latin-1 を1、他は2でカウント。
    実測でTwitter公式アルゴリズムと一致する範囲。"""
    n = 0
    for c in text:
        if ord(c) < 0x100:
            n += 1
        elif 0x2000 <= ord(c) <= 0x200D or 0x2010 <= ord(c) <= 0x201F:
            n += 1
        else:
            n += 2
    return n


def _build_tweet_with_topn(data, n: int) -> str:
    """TOP n件で組み立て"""
    now = datetime.now(JST)
    date_str = f"{now.month}/{now.day}"

    lines = [f"📊グロース250 {date_str}", "", f"📈上昇TOP{n}"]
    for i, item in enumerate(data["best"][:n], 1):
        lines.append(format_line(i, item))
    lines.append("")
    lines.append(f"📉下落TOP{n}")
    for i, item in enumerate(data["worst"][:n], 1):
        lines.append(format_line(i, item))
    lines.append("")
    lines.append("詳細はプロフィール固定のWEBにて")
    return "\n".join(lines)


def build_tweet(data):
    """ツイート本文を組み立てる。TOP4で280文字超なら自動でTOP3に縮退。"""
    LIMIT = 280
    for n in (4, 3):
        tweet = _build_tweet_with_topn(data, n)
        if _weighted_length(tweet) <= LIMIT:
            print(f"[info] tweet built with TOP{n} (weighted={_weighted_length(tweet)})", flush=True)
            return tweet
    # 最悪：TOP3でもオーバーしたらフッターを削って返す
    tweet = _build_tweet_with_topn(data, 3)
    tweet = tweet.replace("\n\n詳細はプロフィール固定のWEBにて", "")
    print(f"[warn] fallback: TOP3 + no footer (weighted={_weighted_length(tweet)})", flush=True)
    return tweet


def post_to_x(text):
    """X API v2 でツイート投稿"""
    api_key = os.environ["X_API_KEY"]
    api_secret = os.environ["X_API_SECRET"]
    access_token = os.environ["X_ACCESS_TOKEN"]
    access_secret = os.environ["X_ACCESS_SECRET"]

    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )
    return client.create_tweet(text=text)


def main():
    print(f"[info] start: {datetime.now(JST).isoformat()}", flush=True)

    try:
        data = fetch_data()
        print(f"[info] data updated_at: {data.get('updated_at')}", flush=True)
        print(f"[info] best count: {len(data.get('best', []))}", flush=True)
        print(f"[info] worst count: {len(data.get('worst', []))}", flush=True)
    except Exception as e:
        print(f"[error] fetch failed: {e}", file=sys.stderr, flush=True)
        return 1

    if not data.get("best") or not data.get("worst"):
        print("[error] best/worst data missing", file=sys.stderr, flush=True)
        return 1

    tweet_text = build_tweet(data)
    print(f"[info] tweet length: {len(tweet_text)} python-chars", flush=True)
    print("[info] tweet preview:", flush=True)
    print("-" * 40, flush=True)
    print(tweet_text, flush=True)
    print("-" * 40, flush=True)

    try:
        result = post_to_x(tweet_text)
        print(f"[info] posted successfully: id={result.data.get('id') if result.data else 'unknown'}", flush=True)
        return 0
    except Exception as e:
        print(f"[error] post failed: {e}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
