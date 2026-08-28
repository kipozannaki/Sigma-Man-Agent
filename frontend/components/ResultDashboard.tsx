/**
 * 结果页仪表盘：ECharts 雷达图展示五维得分 + 红/黄/绿裁决大圆点。
 * 雷达图维度标签与后端 dimensions 字段严格对齐。
 *
 * 依赖：npm i echarts
 */
import { useEffect, useRef } from "react";
import * as echarts from "echarts";

/** 五维标签：key 与后端 ScoreResult 字段完全一致 */
const DIMENSIONS = [
  { key: "finance", label: "财务安全" },
  { key: "emotion", label: "情感质量" },
  { key: "reproduction", label: "生育一致" },
  { key: "reputation", label: "名声安全" },
  { key: "legal", label: "法律风险" },
] as const;

/** 裁决等级 → 颜色与文案 */
const LIGHT_STYLE: Record<string, { color: string; text: string }> = {
  red: { color: "#e53935", text: "建议止损" },
  yellow: { color: "#fdd835", text: "观察期" },
  green: { color: "#43a047", text: "继续持有" },
};

export interface ScoreResult {
  scores: Record<(typeof DIMENSIONS)[number]["key"], number>;
  total_score: number;
  reasoning: string;
  verdict: "red" | "yellow" | "green";
  actions: string[];
}

export default function ResultDashboard({ result }: { result: ScoreResult }) {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current) return;
    const chart = echarts.init(chartRef.current);

    // 雷达图：indicator 顺序与 DIMENSIONS 严格对齐后端字段
    chart.setOption({
      radar: {
        indicator: DIMENSIONS.map((d) => ({ name: d.label, max: 100 })),
        radius: "65%",
      },
      series: [
        {
          type: "radar",
          data: [{ value: DIMENSIONS.map((d) => result.scores[d.key]), name: "五维得分" }],
          areaStyle: { opacity: 0.3 },
        },
      ],
    });
    return () => chart.dispose();
  }, [result]);

  const light = LIGHT_STYLE[result.verdict] ?? LIGHT_STYLE.yellow;

  return (
    <div className="dashboard">
      <div className="dashboard__light" style={{ background: light.color }}>
        {/* 正中央大圆点 + 裁决文案 */}
        <div className="dashboard__dot" />
        <span>{light.text}（{result.total_score}/100）</span>
      </div>
      <div ref={chartRef} style={{ width: "100%", height: 320 }} />
      <p className="dashboard__reason">{result.reasoning}</p>
      <ol className="dashboard__actions">
        {result.actions.map((a, i) => (
          <li key={i}>{a}</li>
        ))}
      </ol>
      {/* 固定免责声明 */}
      <footer className="dashboard__disclaimer">
        本建议仅供情感参考，不构成法律意见。
      </footer>
    </div>
  );
}
