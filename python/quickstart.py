#!/usr/bin/env python3
"""PoisGoal 数据 API 快速示例：列出某个联赛未开赛的比赛，再取第一场的完整数据。

用法：
    export POISGOAL_KEY="pg_live_你的密钥"
    python3 quickstart.py [联赛编号，默认 39 英超]
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("POISGOAL_BASE", "https://poisgoal.com/api/v1")
KEY = os.environ.get("POISGOAL_KEY", "")


def get(path, **params):
    """发一个 GET 请求，返回解析后的 JSON。出错时打印接口给的错误信息并退出。"""
    url = f"{BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        try:
            body = json.load(e)
        except Exception:
            body = {}
        wait = e.headers.get("Retry-After")
        print(f"请求失败 {e.code}：{body.get('error', '')} {body.get('message', '')}".strip())
        if wait:
            print(f"请在 {wait} 秒后重试。")
        sys.exit(1)


def pct(x):
    return "-" if x is None else f"{x * 100:.0f}%"


def all_matches(league):
    """按 next_cursor 翻页，取回该联赛全部未开赛的比赛。"""
    rows, cursor = [], None
    while True:
        params = {"league": league, "lang": "zh-CN", "limit": 100}
        if cursor:
            params["cursor"] = cursor
        page = get("/matches", **params)
        rows.extend(page["data"])
        if not page["pagination"]["has_more"]:
            return rows
        cursor = page["pagination"]["next_cursor"]


def main():
    if not KEY:
        print("请先设置环境变量 POISGOAL_KEY。")
        sys.exit(1)
    league = sys.argv[1] if len(sys.argv) > 1 else "39"

    matches = all_matches(league)
    if not matches:
        print("这个联赛目前没有未开赛的比赛。")
        return

    print(f"{matches[0]['league']['display_name']}：{len(matches)} 场未开赛\n")
    for m in matches[:10]:
        p = m["probabilities"] or {}
        xg = m["expected_goals"] or {}
        print(
            f"{m['date']}  {m['home']['display_name']} vs {m['away']['display_name']}\n"
            f"    主胜 {pct(p.get('home'))} / 平 {pct(p.get('draw'))} / 客胜 {pct(p.get('away'))}"
            f"    预期进球 {xg.get('home', '-')} : {xg.get('away', '-')}"
        )

    # 取第一场有模型数据的比赛，看完整数据
    first = next((m for m in matches if m["status"] == "predicted"), None)
    if not first:
        return
    d = get(f"/matches/{first['fixture_id']}", lang="zh-CN")["data"]
    print(f"\n完整数据：{d['home']['display_name']} vs {d['away']['display_name']}")
    if d.get("top_scores"):
        scores = "，".join(f"{s['home']}-{s['away']}（{pct(s['probability'])}）" for s in d["top_scores"][:3])
        print(f"  最可能的比分：{scores}")
    if d.get("total_goals"):
        over = d["total_goals"]["over"]
        print(f"  大于 1.5 球 {pct(over['1.5'])}，大于 2.5 球 {pct(over['2.5'])}，大于 3.5 球 {pct(over['3.5'])}")
    if d.get("both_teams_score"):
        print(f"  双方都进球：{pct(d['both_teams_score']['yes'])}")
    if d.get("half_time"):
        h = d["half_time"]
        print(f"  半场：主胜 {pct(h['home'])} / 平 {pct(h['draw'])} / 客胜 {pct(h['away'])}")
    form = d.get("form") or {}
    print(f"  近期战绩（由旧到新）：主队 {form.get('home') or '-'}，客队 {form.get('away') or '-'}")


if __name__ == "__main__":
    main()
