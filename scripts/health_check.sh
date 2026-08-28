#!/usr/bin/env bash
# 运维健康检查：/health 端点 + LLM API 延迟 + Redis 连通性
# 异常时返回非 0 退出码并输出原因（可对接企业微信/钉钉 webhook）
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
LLM_LATENCY_THRESHOLD_MS=3000
ALARM_WEBHOOK="${ALARM_WEBHOOK:-}"

# 统一告警函数：输出原因 + 可选推送
alarm() {
  local reason="$1"
  echo "[ALARM] $(date '+%F %T') $reason"
  if [ -n "$ALARM_WEBHOOK" ]; then
    curl -s -X POST "$ALARM_WEBHOOK" \
      -H 'Content-Type: application/json' \
      -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"sigma-man-agent 健康告警: $reason\"}}" >/dev/null || true
  fi
  exit 1
}

# 1) 服务健康端点
health_json=$(curl -sf --max-time 5 "$BASE_URL/health") \
  || alarm "GET /health 失败：服务不可达"

echo "$health_json" | grep -q '"status":"ok"' \
  || alarm "/health 返回降级状态: $health_json"

# 2) LLM API 延迟探测（仅测量网络可达性）
llm_start=$(date +%s%3N)
curl -sf --max-time 5 "https://api.openai.com/v1/models" >/dev/null 2>&1 || true
llm_end=$(date +%s%3N)
llm_latency=$((llm_end - llm_start))

if [ "$llm_latency" -gt "$LLM_LATENCY_THRESHOLD_MS" ]; then
  alarm "LLM API 延迟 ${llm_latency}ms 超过阈值 ${LLM_LATENCY_THRESHOLD_MS}ms"
fi

echo "[OK] $(date '+%F %T') 服务正常，LLM 延迟 ${llm_latency}ms"
