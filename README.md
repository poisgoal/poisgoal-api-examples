# PoisGoal 足球数据 API 示例

[PoisGoal](https://poisgoal.com) 的足球数据接口示例代码，Python 和 Node.js 各一份。

接口返回的不是比分直播，而是模型算好的数据：每场比赛的胜平负概率、比分概率、进球数分布、预期进球 xG、近期战绩等。覆盖 120 多个联赛与杯赛。

- 接口文档：https://poisgoal.com/docs
- OpenAPI 规范：https://poisgoal.com/openapi.v1.json

## 能拿到什么

| 接口 | 内容 |
|---|---|
| `GET /api/v1/meta` | 接口与模型版本、最近更新时间、覆盖的全部赛事 |
| `GET /api/v1/matches` | 全部未开赛的比赛，带胜平负概率和预期进球，支持按日期、联赛筛选和分页 |
| `GET /api/v1/matches/{fixture_id}` | 单场完整数据：比分概率、进球数分布、大于 1.5 / 2.5 / 3.5 球、双方是否进球、半场概率、近期战绩 |
| `GET /api/v1/results` | 已结束的比赛：赛前数据、最终比分、是否命中 |
| `GET /api/v1/accuracy` | 近期与长期回测的命中率，整体和分联赛 |

全部是 GET，返回 JSON。`lang` 参数可选 `en`、`es`、`zh-CN`、`pt-BR`，只影响球队和联赛的显示名称。

## 准备

1. 在 poisgoal.com 注册并开通 Pro。
2. 打开控制台创建一个密钥（`pg_live_` 开头）。密钥只显示一次，请立即保存。
3. 把密钥放进环境变量：

```bash
export POISGOAL_KEY="pg_live_你的密钥"
```

限额：每个密钥每分钟 60 次、每天 10,000 次。数据每小时更新数次，成功的响应带 60 秒缓存，所以每分钟请求超过一次没有意义。

## 一行命令先试试

```bash
curl -s "https://poisgoal.com/api/v1/matches?league=39&lang=zh-CN&limit=5" \
  -H "Authorization: Bearer $POISGOAL_KEY"
```

`league=39` 是英超。全部联赛的编号可以从 `/api/v1/meta` 里查。

## Python

只用标准库，不需要安装依赖。

```bash
python3 python/quickstart.py            # 默认英超
python3 python/quickstart.py 140        # 西甲
```

## Node.js

需要 Node 18 或更高版本（自带 fetch）。

```bash
node node/quickstart.mjs                # 默认英超
node node/quickstart.mjs 140            # 西甲
```

## 返回的字段

列表里每场比赛的主要字段：

```json
{
  "fixture_id": 1557473,
  "status": "predicted",
  "date": "2026-11-22",
  "kickoff_at": "2026-11-22T16:30:00+00:00",
  "league": { "id": 39, "key": "epl", "name": "Premier League", "display_name": "英超联赛", "country": "England" },
  "home": { "name": "Liverpool", "display_name": "利物浦" },
  "away": { "name": "Manchester United", "display_name": "曼彻斯特联" },
  "probabilities": { "home": 0.5612, "draw": 0.2231, "away": 0.2157 },
  "expected_goals": { "home": 2.06, "away": 1.16, "total": 3.22 }
}
```

上面的数字是示例，实际值以接口返回为准。概率都是 0 到 1 的小数，保留 4 位。`status` 为 `listed` 时表示比赛已排期但模型还没算出数据，这时 `probabilities` 等字段为 `null`，代码里要判空。

## 错误处理

所有错误都是同一种结构：

```json
{ "error": "invalid_parameter", "message": "..." }
```

常见的有：`missing_api_key`（没带密钥，401）、`plan_inactive`（Pro 已到期，403）、`rate_limited` 和 `daily_quota_exceeded`（超限，429，响应头 `Retry-After` 给出要等的秒数）。

## 说明

PoisGoal 提供的是足球比赛的统计分析数据，不是投注建议，也不保证任何结果。

接口里没有：博彩公司赔率、球队队徽、伤停、裁判、天气、历史交锋。
