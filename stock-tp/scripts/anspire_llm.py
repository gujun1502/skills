#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anspire_llm.py —— 可选的大模型综合层（OpenAI 兼容）

设计说明：
  在交互式运行本 skill 时，"综合分析 / 拆解预言 / 买卖结论"由 Claude 自己完成
  （Claude 就是大模型，质量更高、可追问）。本脚本只用于【无人值守 / loop / cron】
  场景，让流水线在没有 Claude 在场时也能自动产出一份初稿。

  Anspire 大模型走 OpenAI 兼容协议；因官方未公开统一 base_url，端点与模型名
  做成可配置（config.env）：
      ANSPIRE_LLM_BASE_URL=https://api.anspire.cn/v1   # 以你账号控制台为准
      ANSPIRE_LLM_MODEL=anspire-pro
      ANSPIRE_API_KEYS=sk-...                            # 同一 Key 复用
  也可指向任意 OpenAI 兼容服务（DeepSeek/Qwen/Kimi 等）做兜底。

用法：
  echo '{"system":"...","user":"..."}' | python anspire_llm.py
  python anspire_llm.py --probe        # 探活
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import common as C

DEFAULT_BASE = "https://api.anspire.cn/v1"
DEFAULT_MODEL = "anspire-pro"


def available() -> bool:
    return bool(C.anspire_keys()) and bool(C.get("ANSPIRE_LLM_BASE_URL", DEFAULT_BASE))


def chat(system: str, user: str, temperature: float = 0.3,
         max_tokens: int = 2400, timeout: int = 90) -> dict:
    keys = C.anspire_keys()
    if not keys:
        return {"status": "error", "note": "no ANSPIRE_API_KEYS"}
    base = C.get("ANSPIRE_LLM_BASE_URL", DEFAULT_BASE).rstrip("/")
    model = C.get("ANSPIRE_LLM_MODEL", DEFAULT_MODEL)
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {keys[0]}",
                 "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = json.loads(r.read().decode("utf-8", "ignore"))
        text = payload["choices"][0]["message"]["content"]
        return {"status": "ok", "model": model, "text": text}
    except Exception as e:
        return {"status": "error", "note": f"{type(e).__name__}: {e}",
                "hint": "检查 ANSPIRE_LLM_BASE_URL / ANSPIRE_LLM_MODEL 是否与控制台一致"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    a = ap.parse_args()
    if a.probe:
        C.print_json(chat("你是金融助手。", "回复两个字：在线", max_tokens=10))
        return
    raw = sys.stdin.read()
    try:
        msg = json.loads(raw)
    except Exception:
        msg = {"system": "你是资深A股/美股研究员。", "user": raw}
    C.print_json(chat(msg.get("system", ""), msg.get("user", ""),
                      temperature=msg.get("temperature", 0.3),
                      max_tokens=msg.get("max_tokens", 2400)))


if __name__ == "__main__":
    main()
