#!/usr/bin/env node
// PoisGoal 数据 API 快速示例：列出某个联赛未开赛的比赛，再取第一场的完整数据。
//
// 用法：
//   export POISGOAL_KEY="pg_live_你的密钥"
//   node quickstart.mjs [联赛编号，默认 39 英超]

const BASE = process.env.POISGOAL_BASE ?? "https://poisgoal.com/api/v1";
const KEY = process.env.POISGOAL_KEY ?? "";

async function get(path, params = {}) {
  const url = new URL(BASE + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const res = await fetch(url, { headers: { Authorization: `Bearer ${KEY}` } });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    console.error(`请求失败 ${res.status}：${body.error ?? ""} ${body.message ?? ""}`.trim());
    const wait = res.headers.get("retry-after");
    if (wait) console.error(`请在 ${wait} 秒后重试。`);
    process.exit(1);
  }
  return res.json();
}

const pct = (x) => (x == null ? "-" : `${Math.round(x * 100)}%`);

// 按 next_cursor 翻页，取回该联赛全部未开赛的比赛
async function allMatches(league) {
  const rows = [];
  let cursor = null;
  for (;;) {
    const params = { league, lang: "zh-CN", limit: 100 };
    if (cursor) params.cursor = cursor;
    const page = await get("/matches", params);
    rows.push(...page.data);
    if (!page.pagination.has_more) return rows;
    cursor = page.pagination.next_cursor;
  }
}

if (!KEY) {
  console.error("请先设置环境变量 POISGOAL_KEY。");
  process.exit(1);
}
const league = process.argv[2] ?? "39";
const matches = await allMatches(league);
if (matches.length === 0) {
  console.log("这个联赛目前没有未开赛的比赛。");
  process.exit(0);
}

console.log(`${matches[0].league.display_name}：${matches.length} 场未开赛\n`);
for (const m of matches.slice(0, 10)) {
  const p = m.probabilities ?? {};
  const xg = m.expected_goals ?? {};
  console.log(
    `${m.date}  ${m.home.display_name} vs ${m.away.display_name}\n` +
      `    主胜 ${pct(p.home)} / 平 ${pct(p.draw)} / 客胜 ${pct(p.away)}` +
      `    预期进球 ${xg.home ?? "-"} : ${xg.away ?? "-"}`,
  );
}

// 取第一场有模型数据的比赛，看完整数据
const first = matches.find((m) => m.status === "predicted");
if (first) {
  const { data: d } = await get(`/matches/${first.fixture_id}`, { lang: "zh-CN" });
  console.log(`\n完整数据：${d.home.display_name} vs ${d.away.display_name}`);
  if (d.top_scores) {
    const scores = d.top_scores.slice(0, 3).map((s) => `${s.home}-${s.away}（${pct(s.probability)}）`).join("，");
    console.log(`  最可能的比分：${scores}`);
  }
  if (d.total_goals) {
    const o = d.total_goals.over;
    console.log(`  大于 1.5 球 ${pct(o["1.5"])}，大于 2.5 球 ${pct(o["2.5"])}，大于 3.5 球 ${pct(o["3.5"])}`);
  }
  if (d.both_teams_score) console.log(`  双方都进球：${pct(d.both_teams_score.yes)}`);
  if (d.half_time) {
    const h = d.half_time;
    console.log(`  半场：主胜 ${pct(h.home)} / 平 ${pct(h.draw)} / 客胜 ${pct(h.away)}`);
  }
  console.log(`  近期战绩（由旧到新）：主队 ${d.form?.home ?? "-"}，客队 ${d.form?.away ?? "-"}`);
}
