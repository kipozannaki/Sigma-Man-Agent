/**
 * 场景选择门禁：用户必须从 7 张困局卡片中选 1 张才能开始对话。
 * 未选择时「开始咨询」按钮保持置灰。
 */
import { useState } from "react";

/** 七大困局卡片配置（与后端 ScenarioEnum 一一对应） */
const SCENARIOS = [
  { key: "FINANCE", icon: "💰", label: "财务围猎", desc: "彩礼 / 上交工资 / 经济吸血" },
  { key: "CHEATING", icon: "🔍", label: "出轨疑云", desc: "暧昧 / 实锤 / 信任崩塌" },
  { key: "COLD_VIOLENCE", icon: "🧊", label: "冷暴力", desc: "冷战 / 已读不回 / 内耗" },
  { key: "FAMILY_ORIGIN", icon: "🏠", label: "原生家庭", desc: "丈母娘 / 父母越界干涉" },
  { key: "REPRODUCTION", icon: "🍼", label: "生育博弈", desc: "丁克分歧 / 育儿主导权" },
  { key: "LOW_INTIMACY", icon: "🚪", label: "亲密缺失", desc: "无性 / 排斥 / 室友化" },
  { key: "REPUTATION", icon: "📢", label: "社死危机", desc: "公开处刑 / 职场干扰" },
] as const;

interface Props {
  /** 选定场景后回调（key 与后端 ScenarioEnum 对齐） */
  onConfirm: (scenario: string) => void;
}

export default function ScenarioSelector({ onConfirm }: Props) {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div className="selector">
      <h2>你现在身处哪个困局？</h2>
      <div className="cards">
        {SCENARIOS.map((s) => (
          <div
            key={s.key}
            className={`card ${selected === s.key ? "card--active" : ""}`}
            onClick={() => setSelected(s.key)}
            role="button"
            aria-pressed={selected === s.key}
          >
            <span className="card__icon">{s.icon}</span>
            <span className="card__label">{s.label}</span>
            <span className="card__desc">{s.desc}</span>
          </div>
        ))}
      </div>
      {/* 门禁逻辑：未选中场景时按钮禁用 */}
      <button disabled={!selected} onClick={() => selected && onConfirm(selected)}>
        开始咨询
      </button>
    </div>
  );
}
