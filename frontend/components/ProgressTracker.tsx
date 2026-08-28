/**
 * 对话进度追踪：显示当前处于第几层追问（共 5 层）。
 * 用户超过 2 分钟未回复时，顶部出现弱提示。
 */
import { useEffect, useState } from "react";

/** 追问总层数（与后端追问树 depth 对齐） */
const TOTAL_DEPTH = 5;
/** 无响应弱提示阈值：2 分钟 */
const IDLE_TIMEOUT_MS = 2 * 60 * 1000;

interface Props {
  /** 当前追问层（0 表示尚未进入追问阶段） */
  depth: number;
  /** 用户最后活跃时间戳（发消息/收消息时更新） */
  lastActiveAt: number;
}

export default function ProgressTracker({ depth, lastActiveAt }: Props) {
  const [showIdleHint, setShowIdleHint] = useState(false);

  useEffect(() => {
    // 每 10 秒检查一次：距最后活跃是否超过 2 分钟
    const timer = setInterval(() => {
      setShowIdleHint(Date.now() - lastActiveAt > IDLE_TIMEOUT_MS);
    }, 10_000);
    return () => clearInterval(timer);
  }, [lastActiveAt]);

  // 进度百分比 = (当前层数 / 5) * 100，精确计算
  const percent = Math.round((depth / TOTAL_DEPTH) * 100);

  return (
    <div className="tracker">
      {showIdleHint && <div className="tracker__idle">是否要换个时间再聊？</div>}
      <div className="tracker__bar">
        <div className="tracker__fill" style={{ width: `${percent}%` }} />
      </div>
      <div className="tracker__label">
        {depth === 0 ? "准备中" : `追问进度 ${depth}/${TOTAL_DEPTH}（${percent}%）`}
      </div>
    </div>
  );
}
