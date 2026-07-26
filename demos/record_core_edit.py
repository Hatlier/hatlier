#!/usr/bin/env python3
"""
Hatlier demo recorder — polished motion template.

Design goals:
  - No Hatlier flash before story cards
  - Tight pacing (no long black / blur mush)
  - Reusable TIMING + STORY knobs

    py demos/record_core_edit.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

_PW_CACHE = Path(__file__).resolve().parent.parent / ".pw-browsers"
if _PW_CACHE.is_dir():
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(_PW_CACHE)

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = Path(__file__).resolve().parent / "out"
APP = (ROOT / "hatlier.html").resolve().as_uri()
BLANK = (
    "data:text/html;charset=utf-8,"
    "<!doctype html><meta charset=utf-8>"
    "<title>demo</title><style>html,body{margin:0;height:100%;background:#0b0d10}</style>"
    "<body></body>"
)
HERO_BG = (
    "https://images.unsplash.com/photo-1554068865-24cecd4e34b8"
    "?auto=format&fit=crop&w=1600&q=80"
)

# ---------------------------------------------------------------------------
# Motion template knobs — tweak here, not in scattered sleeps.
# Calm pacing on purpose (phone viewers → early-skip if rushed).
# ---------------------------------------------------------------------------
TIMING = {
    "card_hold": 4.8,          # ~5s per message beat
    "card_enter": 0.55,
    "card_exit": 0.42,
    "veil": 0.28,
    "editor_settle": 1.2,
    "type_ms": 0.045,
    "after_edit": 0.7,
    "bg_hold": 1.1,
    "chip_in": 0.28,
    "end_hold": 3.6,
    "howto_hold": 3.8,
    "cursor_steps": 22,
    "glide": 0.8,
    "nav_black": 0.4,
    "reveal_black": 0.55,
}

# Desktop (YouTube / X) and phone (Stories / Reels / 縦型)
PROFILES = [
    {
        "id": "desktop",
        "label": "PC",
        "width": 1280,
        "height": 720,
        "stem": "core-edit-desktop",
    },
    {
        "id": "mobile",
        "label": "スマホ",
        "width": 1080,
        "height": 1920,
        "stem": "core-edit-mobile",
        "is_mobile": True,
    },
]

STORY = {
    "id": "core-edit",
    "tagline": "AIが作る。あなたが仕上げる。",
    "beats": [
        # 0〜5秒 — 時代の前提
        {
            "kind": "card",
            "theme": "era",
            "kicker": "",
            "lines": ["AIでWebページを作る時代。"],
            "sub": "LPも、スライドも、ゲームも、HTMLなら数分で完成します。",
            "hold": 5.0,
        },
        # 5〜10秒 — 本当の困りごと
        {
            "kind": "card",
            "theme": "problem",
            "kicker": "",
            "lines": ["でも、本当に困るのは完成したあと。"],
            "sub": "「日付だけ変えたい」「画像だけ差し替えたい」「この文字だけ直したい」",
            "hold": 5.0,
        },
        # 10〜15秒 — 既存のやり方の面倒さ
        {
            "kind": "card",
            "theme": "friction",
            "kicker": "そのためだけに",
            "lines": ["AIへ指示し直す？", "コードを書く？"],
            "sub": "ちょっと面倒です。",
            "hold": 5.0,
        },
        # 15〜20秒 — Hatlier の答え（文言）
        {
            "kind": "card",
            "theme": "solution",
            "kicker": "H A T L I E R",
            "lines": ["HTMLをそのまま開いて編集。"],
            "sub": "AIが作る。あなたが仕上げる。",
            "hold": 4.8,
        },
        # 実演（短く：日付1つ＋背景）
        {
            "kind": "editor",
            "edits": [
                {"cell": "日程", "to": "9月6日・13日・20日・27日（毎週土曜）"},
            ],
            "hero_bg": HERO_BG,
        },
        {
            "kind": "end",
            "lines": ["AIが作る。", "あなたが仕上げる。"],
            "sub": "Hatlier — it's just HTML.",
            "hold": TIMING["end_hold"],
        },
        {
            "kind": "howto",
            "kicker": "はじめての使い方",
            "steps": [
                {"n": "01", "t": "生成AIに Hatlier用 Skill を渡す"},
                {"n": "02", "t": "出てきた HTML を開く／貼る"},
                {"n": "03", "t": "ダブルクリックで仕上げる"},
            ],
            "sub": "あとは Hatlier のページで、手を動かすだけ。",
            "hold": TIMING["howto_hold"],
        },
    ],
}

WORKSHOP_DOC = {
    "theme": "paper",
    "bg": "plain",
    "font": "elegant",
    "profile": "standard",
    "blocks": [
        {
            "id": "bhero",
            "type": "hero",
            "props": {
                "kicker": "アオゾラ・テニスクラブ",
                "title": "来月の練習予定と、新メンバー募集",
                "lede": "初心者歓迎。ラケットの貸し出しもあります。土曜の午前、基礎からのんびり打ちましょう。見学だけでも大歓迎です。",
            },
        },
        {
            "id": "bbadges",
            "type": "badges",
            "props": {"items": ["初心者歓迎", "新メンバー募集中", "ラケット貸出あり", "男女ミックス"]},
        },
        {
            "id": "btable",
            "type": "table",
            "props": {
                "head": ["項目", "内容"],
                "rows": [
                    ["日程", "8月2日・9日・16日・23日（毎週土曜）"],
                    ["時間", "9:00 – 12:00"],
                    ["会場", "市営中央テニスコート"],
                    ["参加費", "1回 500円（コート代・ボール込）"],
                ],
            },
        },
        {
            "id": "bnote",
            "type": "callout",
            "props": {
                "h": "特別連絡事項",
                "t": "8月16日は大会と重なるため、コートが半面のみになります。参加人数が多い場合は時間を分けます。",
            },
        },
        {
            "id": "bbtn",
            "type": "button",
            "props": {"label": "見学を申し込む", "url": "https://example.com/tennis"},
        },
        {
            "id": "bclosing",
            "type": "closing",
            "props": {
                "h": "まずは一度、見に来てください",
                "t": "お問い合わせ： aozora-tennis@example.com ／ 連絡は LINE でも受付中",
            },
        },
    ],
}

DEMO_CSS = """
#demo-veil {
  position: fixed; inset: 0; z-index: 2147483635;
  background: #0b0d10; opacity: 0; pointer-events: none;
  transition: opacity .18s ease;
}
#demo-veil.on { opacity: 1; }
#demo-stage {
  position: fixed; inset: 0; z-index: 2147483640;
  display: none; align-items: center; justify-content: center;
  color: #f7f3ea; pointer-events: none; overflow: hidden;
  font-family: "Segoe UI", "Hiragino Sans", "Noto Sans JP", system-ui, sans-serif;
  opacity: 1; transition: opacity .6s ease;
}
#demo-stage.on { display: flex; }
#demo-stage.hide { opacity: 0; }
#demo-stage::before {
  content: ""; position: absolute; inset: -20%;
  background:
    radial-gradient(closest-side at 30% 20%, rgba(255,255,255,.05), transparent 70%),
    radial-gradient(closest-side at 80% 75%, rgba(255,255,255,.04), transparent 65%);
  animation: demoDrift 14s ease-in-out infinite alternate;
  pointer-events: none;
}
@keyframes demoDrift {
  from { transform: translate3d(-1.5%, -1%, 0) scale(1.02); }
  to   { transform: translate3d(1.5%, 1%, 0) scale(1.06); }
}
#demo-stage[data-theme="era"] {
  background:
    radial-gradient(1000px 640px at 22% 10%, #2a3348 0%, transparent 55%),
    radial-gradient(800px 520px at 85% 80%, #1a2030 0%, transparent 50%),
    #10141c;
}
#demo-stage[data-theme="era"] .kicker { color: #a8b8d8; }
#demo-stage[data-theme="era"] .sub { color: #c5d0e4; }
#demo-stage[data-theme="era"] .accent { background: linear-gradient(90deg, transparent, #8aa4d4, transparent); }
#demo-stage[data-theme="problem"] {
  background:
    radial-gradient(1000px 640px at 18% 12%, #5a3428 0%, transparent 55%),
    radial-gradient(800px 520px at 88% 78%, #3a2218 0%, transparent 50%),
    #1c1410;
}
#demo-stage[data-theme="problem"] .kicker { color: #ffb48a; }
#demo-stage[data-theme="problem"] .sub { color: #f0c8b0; }
#demo-stage[data-theme="problem"] .accent { background: linear-gradient(90deg, transparent, #ff9b6a, transparent); }
#demo-stage[data-theme="friction"] {
  background:
    radial-gradient(1000px 640px at 20% 15%, #4a3038 0%, transparent 55%),
    radial-gradient(800px 520px at 90% 80%, #2a1c22 0%, transparent 50%),
    #161014;
}
#demo-stage[data-theme="friction"] .kicker { color: #e8a0b0; letter-spacing: .18em; }
#demo-stage[data-theme="friction"] .sub { color: #d8b0bc; }
#demo-stage[data-theme="friction"] .accent { background: linear-gradient(90deg, transparent, #d88098, transparent); }
#demo-stage[data-theme="solution"] {
  background:
    radial-gradient(1000px 640px at 20% 8%, #1d4a3c 0%, transparent 55%),
    radial-gradient(800px 520px at 90% 85%, #143028 0%, transparent 50%),
    #0d1f1a;
}
#demo-stage[data-theme="solution"] .kicker { color: #8fe0b8; letter-spacing: .34em; }
#demo-stage[data-theme="solution"] .sub { color: #b7e0ce; }
#demo-stage[data-theme="solution"] .accent { background: linear-gradient(90deg, transparent, #6fd6a6, transparent); }
#demo-stage[data-theme="end"],
#demo-stage[data-theme="howto"] {
  background:
    radial-gradient(1100px 700px at 50% 32%, #241f2b 0%, transparent 60%),
    #0c0a10;
}
#demo-stage[data-theme="end"] .sub,
#demo-stage[data-theme="howto"] .sub { color: #cbb894; }

#demo-stage .wrap {
  position: relative; z-index: 1; max-width: 980px; padding: 36px 52px; text-align: center;
  opacity: 0; transform: translateY(22px) scale(.96);
  transition: opacity .38s ease, transform .55s cubic-bezier(.16,1,.3,1);
}
#demo-stage .wrap.in { opacity: 1; transform: none; }
#demo-stage .wrap.out {
  opacity: 0; transform: translateY(-14px) scale(.985);
  transition: opacity .22s ease, transform .28s ease;
}
#demo-stage .kicker {
  font-size: 13px; letter-spacing: .22em; margin: 0 0 18px; font-weight: 700;
  opacity: 0; transform: translateY(8px);
  transition: opacity .35s ease, transform .45s cubic-bezier(.16,1,.3,1);
}
#demo-stage .wrap.in .kicker { opacity: 1; transform: none; transition-delay: .04s; }
#demo-stage .line {
  font-size: 40px; line-height: 1.32; font-weight: 750; margin: 0;
  opacity: 0; transform: translateY(16px);
  transition: opacity .4s ease, transform .55s cubic-bezier(.16,1,.3,1);
}
#demo-stage .line + .line { margin-top: 10px; }
#demo-stage .wrap.in .line:nth-of-type(1) { opacity: 1; transform: none; transition-delay: .1s; }
#demo-stage .wrap.in .line:nth-of-type(2) { opacity: 1; transform: none; transition-delay: .18s; }
#demo-stage .wrap.in .line:nth-of-type(3) { opacity: 1; transform: none; transition-delay: .26s; }
/* lines are after accent+kicker — use .line index */
#demo-stage .wrap.in .line { opacity: 1; transform: none; }
#demo-stage .wrap.in .line:nth-child(3) { transition-delay: .1s; }
#demo-stage .wrap.in .line:nth-child(4) { transition-delay: .18s; }
#demo-stage .wrap.in .line:nth-child(5) { transition-delay: .26s; }
#demo-stage .sub {
  margin: 26px 0 0; font-size: 18px; font-weight: 500; opacity: 0; transform: translateY(10px);
  transition: opacity .4s ease .28s, transform .5s cubic-bezier(.16,1,.3,1) .28s;
}
#demo-stage .wrap.in .sub { opacity: .92; transform: none; }
#demo-stage .accent {
  display: block; height: 2px; width: 0; margin: 0 auto 22px; opacity: .95;
  transition: width .55s cubic-bezier(.16,1,.3,1) .02s;
}
#demo-stage .wrap.in .accent { width: 64px; }

#demo-stage[data-theme="end"] .wrap { opacity: 1; transform: none; transition: none; }
#demo-stage .rule {
  display: block; height: 1px; width: 0; margin: 0 auto 30px;
  background: linear-gradient(90deg, transparent, #e8c48a, transparent);
  transition: width .9s cubic-bezier(.16,1,.3,1);
}
#demo-stage .rule.draw { width: 220px; }
#demo-stage .big { font-size: 52px; line-height: 1.28; font-weight: 800; margin: 0; }
#demo-stage .big + .big { margin-top: 4px; }
#demo-stage .big .w {
  display: inline-block; opacity: 0; transform: translateY(18px);
  transition: opacity .45s ease, transform .55s cubic-bezier(.16,1,.3,1);
}
#demo-stage .big .w.in { opacity: 1; transform: none; }
#demo-stage .big.accented .w.in { text-shadow: 0 0 24px rgba(232,196,138,.32); }
#demo-stage .endsub {
  margin: 32px 0 0; font-size: 17px; letter-spacing: .14em; font-weight: 500;
  color: #cbb894; opacity: 0; transform: translateY(8px);
  transition: opacity .55s ease, transform .55s ease;
}
#demo-stage .endsub.in { opacity: 1; transform: none; }
#demo-glow {
  position: absolute; left: 50%; top: 48%; width: 820px; height: 820px;
  transform: translate(-50%, -50%) scale(.7); pointer-events: none;
  background: radial-gradient(circle, rgba(232,196,138,.14) 0%, transparent 62%);
  opacity: 0; transition: opacity 1s ease, transform 1.8s ease;
}
#demo-glow.on { opacity: 1; transform: translate(-50%, -50%) scale(1); }

#demo-stage[data-theme="howto"] .wrap { opacity: 1; transform: none; max-width: 760px; }
#demo-stage .steps { margin: 24px 0 0; text-align: left; display: grid; gap: 12px; }
#demo-stage .step {
  display: grid; grid-template-columns: 52px 1fr; gap: 14px; align-items: center;
  padding: 14px 16px; border-radius: 14px;
  background: rgba(255,255,255,.045); border: 1px solid rgba(232,196,138,.2);
  opacity: 0; transform: translateY(14px);
  transition: opacity .4s ease, transform .5s cubic-bezier(.16,1,.3,1);
}
#demo-stage .step.in { opacity: 1; transform: none; }
#demo-stage .step .n { font: 800 16px/1 system-ui,sans-serif; color: #e8c48a; letter-spacing: .08em; }
#demo-stage .step .t { font-size: 20px; font-weight: 650; line-height: 1.35; }

#demo-chip {
  position: fixed; left: 50%; top: 58px; transform: translateX(-50%) translateY(-6px) scale(.96);
  z-index: 2147483644; padding: 9px 16px; border-radius: 999px;
  background: #127D63; color: #fff; font: 700 13px/1 "Segoe UI","Hiragino Sans",system-ui,sans-serif;
  letter-spacing: .05em; opacity: 0;
  transition: opacity .22s ease, transform .3s cubic-bezier(.16,1,.3,1);
  pointer-events: none; box-shadow: 0 10px 28px rgba(18,125,99,.38);
}
#demo-chip.on { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
#demo-cursor {
  position: fixed; z-index: 2147483646; width: 26px; height: 26px;
  margin-left: -2px; margin-top: -2px; pointer-events: none; opacity: 0;
  transition: opacity .15s ease;
  will-change: transform;
}
#demo-cursor.visible { opacity: 1; }
#demo-cursor svg { display: block; width: 26px; height: 26px; filter: drop-shadow(0 2px 3px rgba(0,0,0,.4)); }
#demo-ripple {
  position: fixed; z-index: 2147483645; width: 12px; height: 12px;
  border-radius: 50%; border: 2px solid #127D63; pointer-events: none;
  transform: translate(-50%, -50%) scale(1); opacity: 0;
}
#demo-ripple.on { animation: demoRipple .38s ease-out forwards; }
@keyframes demoRipple {
  0% { opacity: .9; transform: translate(-50%, -50%) scale(.5); }
  100% { opacity: 0; transform: translate(-50%, -50%) scale(2.2); }
}
.demo-fixed { animation: demoFixed 1.1s ease-out; border-radius: 6px; }
@keyframes demoFixed {
  0% { box-shadow: 0 0 0 0 rgba(18,125,99,.5); background: rgba(18,125,99,.14); }
  100% { box-shadow: 0 0 0 12px rgba(18,125,99,0); background: transparent; }
}
.b-hero { transition: filter .45s ease; }
.b-hero.demo-bg-flash { filter: brightness(1.06) saturate(1.08); }

/* ---- mobile (9:16) — large type for phone viewing ---- */
html[data-demo-profile="mobile"] #demo-stage .wrap {
  max-width: 100%; padding: 48px 40px; text-align: left;
}
html[data-demo-profile="mobile"] #demo-stage .accent {
  margin: 0 0 28px;
}
html[data-demo-profile="mobile"] #demo-stage .line {
  font-size: 44px; line-height: 1.38; letter-spacing: .01em;
}
html[data-demo-profile="mobile"] #demo-stage .kicker {
  font-size: 15px; letter-spacing: .28em; margin: 0 0 22px;
}
html[data-demo-profile="mobile"] #demo-stage .sub {
  font-size: 20px; line-height: 1.55; margin-top: 28px;
}
html[data-demo-profile="mobile"] #demo-stage .big {
  font-size: 48px; line-height: 1.35;
}
html[data-demo-profile="mobile"] #demo-stage .endsub {
  font-size: 18px; margin-top: 28px;
}
html[data-demo-profile="mobile"] #demo-stage .steps {
  max-width: 100%; margin: 28px 0 8px; gap: 18px;
}
html[data-demo-profile="mobile"] #demo-stage .step {
  grid-template-columns: 56px 1fr; gap: 16px; padding: 8px 0;
}
html[data-demo-profile="mobile"] #demo-stage .step .n {
  font-size: 20px;
}
html[data-demo-profile="mobile"] #demo-stage .step .t {
  font-size: 24px; line-height: 1.4;
}
html[data-demo-profile="mobile"] #demo-chip {
  left: 50%; right: auto; bottom: 64px; top: auto;
  padding: 12px 20px; font-size: 15px;
  transform: translateX(-50%) translateY(6px) scale(.96);
}
html[data-demo-profile="mobile"] #demo-chip.on {
  transform: translateX(-50%) translateY(0) scale(1);
}
"""

def init_hatlier_script(doc: dict) -> str:
    """Boot cover + seed workshop into localStorage so defaultDoc never paints."""
    doc_js = json.dumps(doc, ensure_ascii=False)
    return f"""
(() => {{
  try {{
    localStorage.setItem("hatlier.seen", "1");
    localStorage.setItem("hatlier.v1", JSON.stringify({doc_js}));
  }} catch (e) {{}}
  const paint = () => {{
    if (document.getElementById("demo-boot-cover")) return;
    const v = document.createElement("div");
    v.id = "demo-boot-cover";
    v.style.cssText = "position:fixed;inset:0;z-index:2147483632;background:#0b0d10;pointer-events:none;";
    (document.documentElement || document.body).appendChild(v);
  }};
  paint();
  document.addEventListener("DOMContentLoaded", paint);
}})();
"""


def demo_boot_js() -> str:
    """Overlay runtime. Sleeps follow TIMING so Python + CSS stay in sync."""
    t = TIMING
    ms = lambda k: int(round(t[k] * 1000))
    return f"""
(() => {{
  let boot = document.getElementById("demo-boot-cover");
  const veil = document.createElement("div");
  veil.id = "demo-veil";
  const stage = document.createElement("div");
  stage.id = "demo-stage";
  stage.innerHTML = '<div id="demo-glow"></div><div class="wrap"></div>';
  const chip = document.createElement("div");
  chip.id = "demo-chip";
  const cur = document.createElement("div");
  cur.id = "demo-cursor";
  cur.innerHTML =
    '<svg width="26" height="26" viewBox="0 0 24 24" fill="none">' +
    '<path d="M4 3l15 9.2-6.6 1.5L9.7 21 4 3z" fill="#111" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/>' +
    "</svg>";
  const rip = document.createElement("div");
  rip.id = "demo-ripple";
  document.body.append(veil, stage, chip, cur, rip);

  const wrap = () => stage.querySelector(".wrap");
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const chars = (s) => Array.from(s).map((c) => `<span class="w">${{c}}</span>`).join("");
  const ensureCover = () => {{
    let v = document.getElementById("demo-boot-cover");
    if (!v) {{
      v = document.createElement("div");
      v.id = "demo-boot-cover";
      (document.documentElement || document.body).appendChild(v);
    }}
    v.style.cssText =
      "position:fixed;inset:0;z-index:2147483632;background:#0b0d10;opacity:1;pointer-events:none;";
    boot = v;
    return v;
  }};
  ensureCover();

  window.__demo = {{
    ensureCover,
    async showCard({{ theme, kicker, lines, sub }}) {{
      const w = wrap();
      if (stage.classList.contains("on")) {{
        w.classList.remove("in");
        w.classList.add("out");
        await sleep({ms("card_exit")});
        veil.classList.add("on");
        await sleep({ms("veil")});
      }}
      stage.dataset.theme = theme || "problem";
      stage.classList.add("on");
      document.getElementById("demo-glow").classList.remove("on");
      const parts = ['<span class="accent"></span>'];
      if (kicker) parts.push(`<p class="kicker">${{kicker}}</p>`);
      for (const line of lines || []) parts.push(`<p class="line">${{line}}</p>`);
      if (sub) parts.push(`<p class="sub">${{sub}}</p>`);
      w.classList.remove("in", "out");
      w.innerHTML = parts.join("");
      void w.offsetWidth;
      veil.classList.remove("on");
      w.classList.add("in");
      if (boot) {{ boot.remove(); boot = null; }}
      await sleep({ms("card_enter")});
    }},

    async showEnd({{ lines, sub }}) {{
      stage.dataset.theme = "end";
      stage.classList.add("on");
      const w = wrap();
      w.classList.remove("out");
      w.innerHTML =
        '<span class="rule"></span>' +
        (lines || [])
          .map((l, i) => `<p class="big${{i === lines.length - 1 ? " accented" : ""}}">${{chars(l)}}</p>`)
          .join("") +
        (sub ? `<p class="endsub">${{sub}}</p>` : "");
      if (boot) {{ boot.remove(); boot = null; }}
      void w.offsetWidth;
      const glow = document.getElementById("demo-glow");
      await sleep(120);
      w.querySelector(".rule").classList.add("draw");
      glow.classList.add("on");
      await sleep(420);
      const words = [...w.querySelectorAll(".w")];
      for (let i = 0; i < words.length; i++) {{
        words[i].classList.add("in");
        await sleep(42);
      }}
      await sleep(260);
      w.querySelector(".endsub")?.classList.add("in");
    }},

    async showHowto({{ kicker, steps, sub }}) {{
      stage.dataset.theme = "howto";
      stage.classList.add("on");
      document.getElementById("demo-glow").classList.add("on");
      const w = wrap();
      w.classList.remove("out");
      w.innerHTML =
        '<span class="accent" style="width:64px"></span>' +
        (kicker ? `<p class="kicker" style="opacity:1;transform:none">${{kicker}}</p>` : "") +
        `<div class="steps">${{(steps || [])
          .map((s) => `<div class="step"><span class="n">${{s.n}}</span><span class="t">${{s.t}}</span></div>`)
          .join("")}}</div>` +
        (sub ? `<p class="sub" style="text-align:center;opacity:.92;transform:none">${{sub}}</p>` : "");
      void w.offsetWidth;
      w.classList.add("in");
      const list = [...w.querySelectorAll(".step")];
      for (let i = 0; i < list.length; i++) {{
        await sleep(280);
        list[i].classList.add("in");
      }}
    }},

    /* Single, simple reveal: the opaque stage fades away to show the editor.
       No page navigation, no veil flicker — one clean crossfade. */
    async revealEditor() {{
      if (boot) {{ boot.remove(); boot = null; }}
      const c = document.getElementById("demo-boot-cover");
      if (c) c.remove();
      stage.classList.add("hide");
      await sleep({ms("reveal_black") + 350});
      stage.classList.remove("on");
      const w = wrap();
      w.innerHTML = "";
      w.classList.remove("out", "in");
      stage.classList.remove("hide");
    }},

    async cutToEditor() {{ return window.__demo.revealEditor(); }},

    /* Editor → end: fade the opaque stage back in over the editor, then bloom. */
    async cutToEnd(payload) {{
      const w = wrap();
      stage.dataset.theme = "end";
      w.innerHTML = "";
      w.classList.remove("in", "out");
      stage.classList.add("hide");
      stage.classList.add("on");
      void stage.offsetWidth;
      stage.classList.remove("hide");
      await sleep({ms("reveal_black")});
      await window.__demo.showEnd(payload);
    }},

    /* end → howto: same dark backdrop, just swap the words (no flash). */
    async cutToHowto(payload) {{
      const w = wrap();
      w.classList.remove("in");
      w.classList.add("out");
      await sleep({ms("card_exit")});
      await window.__demo.showHowto(payload);
    }},
    chip(text, on) {{
      const el = document.getElementById("demo-chip");
      if (text) el.textContent = text;
      el.classList.toggle("on", !!on);
    }},
    async moveTo(x, y, steps = 24) {{
      const el = document.getElementById("demo-cursor");
      el.classList.add("visible");
      const from = el.getBoundingClientRect();
      let fx = from.left + 2, fy = from.top + 2;
      for (let i = 1; i <= steps; i++) {{
        const t = i / steps;
        const e = 1 - Math.pow(1 - t, 3);
        el.style.transform = `translate(${{fx + (x - fx) * e}}px, ${{fy + (y - fy) * e}}px)`;
        await new Promise((r) => requestAnimationFrame(r));
      }}
    }},
    clickFlash(x, y) {{
      const rip = document.getElementById("demo-ripple");
      rip.classList.remove("on");
      rip.style.left = x + "px";
      rip.style.top = y + "px";
      void rip.offsetWidth;
      rip.classList.add("on");
    }},
    markFixed(el) {{
      if (!el) return;
      el.classList.remove("demo-fixed");
      void el.offsetWidth;
      el.classList.add("demo-fixed");
    }},
  }};
}})()
"""


# Back-compat aliases used by older call sites in this file
INIT_COVER = init_hatlier_script(WORKSHOP_DOC)
DEMO_BOOT = demo_boot_js()


def find_ffmpeg() -> str | None:
    which = shutil.which("ffmpeg")
    if which:
        return which
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).is_file():
            return exe
    except Exception:
        pass
    return None


def encode_mp4(webm: Path, mp4: Path) -> Path | None:
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        print("[demo] ffmpeg not found — WebM only:", webm)
        return None
    # Slight contrast lift + ensure even frames; trim lead-in black if any via -ss 0.05
    args = [
        ffmpeg, "-y", "-ss", "0.15", "-i", str(webm),
        "-vf", "fps=30,format=yuv420p,eq=contrast=1.03:saturation=1.04",
        "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-an",
        "-movflags", "+faststart",
        str(mp4),
    ]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr)
        raise RuntimeError("ffmpeg failed")
    return mp4


def center_of(locator):
    box = locator.bounding_box()
    if not box:
        raise RuntimeError("target not visible")
    return box["x"] + box["width"] / 2, box["y"] + box["height"] * 0.5


def blur_quietly(page) -> None:
    page.keyboard.press("Escape")
    page.mouse.click(36, 100)


def glide_to(page, selector: str, settle: float | None = None) -> None:
    """Smoothly bring a block to center. Skips the scroll if it's already there
    so we don't nudge (which reads as flicker)."""
    if settle is None:
        settle = TIMING["glide"]
    page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          if (!el) return;
          const r = el.getBoundingClientRect();
          const mid = r.top + r.height / 2;
          const target = window.innerHeight / 2;
          if (Math.abs(mid - target) < 90) return;
          el.scrollIntoView({ block: 'center', behavior: 'smooth' });
        }""",
        selector,
    )
    time.sleep(settle)


def edit_cell(page, label: str, new_value: str, chip_text: str | None) -> None:
    row = page.locator(f'.b-table tbody tr:has(td:text-is("{label}"))')
    cell = row.locator("td").nth(1)
    if chip_text:
        page.evaluate("(t) => window.__demo.chip(t, true)", chip_text)
        time.sleep(TIMING["chip_in"])
    x, y = center_of(cell)
    page.evaluate(
        "(p) => window.__demo.moveTo(p.x, p.y, p.steps)",
        {"x": x, "y": y, "steps": TIMING["cursor_steps"]},
    )
    time.sleep(0.12)
    page.evaluate("(p) => window.__demo.clickFlash(p.x, p.y)", {"x": x, "y": y})
    cell.dblclick()
    time.sleep(0.18)
    page.keyboard.press("Control+A")
    time.sleep(0.06)
    for ch in new_value:
        page.keyboard.insert_text(ch)
        time.sleep(TIMING["type_ms"])
    time.sleep(0.18)
    blur_quietly(page)
    cell.evaluate("(el) => window.__demo.markFixed(el)")
    page.evaluate("() => window.__demo.chip('', false)")
    time.sleep(TIMING["after_edit"])


def set_hero_bg(page, url: str) -> None:
    hero = page.locator(".bw:has(.b-hero)")
    glide_to(page, ".b-hero")
    page.evaluate("(t) => window.__demo.chip(t, true)", "タイトル背景を差し替え")
    hero.locator(".b-hero").click(position={"x": 36, "y": 36})
    time.sleep(0.22)
    btn = hero.locator('[data-act="herobg"]')
    btn.wait_for(state="visible")
    x, y = center_of(btn)
    page.evaluate(
        "(p) => window.__demo.moveTo(p.x, p.y, p.steps)",
        {"x": x, "y": y, "steps": TIMING["cursor_steps"]},
    )
    time.sleep(0.1)
    page.evaluate("(p) => window.__demo.clickFlash(p.x, p.y)", {"x": x, "y": y})
    # Apply without waiting on flaky file dialog UI.
    page.evaluate(
        """(url) => {
          const H = window.__hatlier;
          const doc = JSON.parse(JSON.stringify(H.doc));
          const hero = doc.blocks.find(b => b.type === 'hero');
          if (hero) hero.props.bg = url;
          H.loadDoc(doc);
          const el = document.querySelector('.b-hero');
          if (el) {
            el.classList.add('demo-bg-flash');
            setTimeout(() => el.classList.remove('demo-bg-flash'), 700);
          }
        }""",
        url,
    )
    page.wait_for_function(
        "() => { const img = document.querySelector('.b-hero .hero-bg');"
        " return img && img.complete && img.naturalWidth > 0; }",
        timeout=15000,
    )
    time.sleep(TIMING["bg_hold"])
    page.evaluate("() => window.__demo.chip('', false)")


def insert_block_after(page, after_id: str, block_type: str) -> None:
    bw = page.locator(f'.bw[data-id="{after_id}"]')
    glide_to(page, f'.bw[data-id="{after_id}"]')
    page.evaluate("(t) => window.__demo.chip(t, true)", "＋ で部品を追加")
    plus = bw.locator(".ins .insbtn")
    x, y = center_of(plus)
    page.evaluate(
        "(p) => window.__demo.moveTo(p.x, p.y, p.steps)",
        {"x": x, "y": y, "steps": TIMING["cursor_steps"]},
    )
    time.sleep(0.1)
    page.evaluate("(p) => window.__demo.clickFlash(p.x, p.y)", {"x": x, "y": y})
    plus.click()
    time.sleep(0.35)
    pal = page.locator(f'.palette .pal-ic[data-type="{block_type}"]')
    pal.wait_for(state="visible")
    px, py = center_of(pal)
    page.evaluate(
        "(p) => window.__demo.moveTo(p.x, p.y, p.steps)",
        {"x": px, "y": py, "steps": 12},
    )
    time.sleep(0.1)
    page.evaluate("(p) => window.__demo.clickFlash(p.x, p.y)", {"x": px, "y": py})
    pal.click()
    time.sleep(0.45)
    page.evaluate("() => window.__demo.chip('', false)")


def edit_new_callout(page, text: str) -> None:
    body = page.locator('.b-callout [data-edit="t"]').last
    body.wait_for(state="visible")
    glide_to(page, ".b-callout")
    page.evaluate("(t) => window.__demo.chip(t, true)", "ここも手で直せる")
    x, y = center_of(body)
    page.evaluate(
        "(p) => window.__demo.moveTo(p.x, p.y, p.steps)",
        {"x": x, "y": y, "steps": TIMING["cursor_steps"]},
    )
    time.sleep(0.1)
    page.evaluate("(p) => window.__demo.clickFlash(p.x, p.y)", {"x": x, "y": y})
    body.dblclick()
    time.sleep(0.15)
    page.keyboard.press("Control+A")
    time.sleep(0.05)
    for ch in text:
        page.keyboard.insert_text(ch)
        time.sleep(TIMING["type_ms"])
    time.sleep(0.18)
    blur_quietly(page)
    body.evaluate("(el) => window.__demo.markFixed(el)")
    page.evaluate("() => window.__demo.chip('', false)")
    time.sleep(0.55)


def inject_demo(page, profile_id: str = "desktop") -> None:
    page.add_style_tag(content=DEMO_CSS)
    # Rebuild boot JS each time so TIMING edits without reimport still apply
    page.evaluate(demo_boot_js())
    page.evaluate(
        "(id) => document.documentElement.setAttribute('data-demo-profile', id)",
        profile_id,
    )


def play_intro(page) -> None:
    for beat in STORY["beats"]:
        if beat["kind"] != "card":
            break
        page.evaluate(
            "(b) => window.__demo.showCard(b)",
            {
                "theme": beat.get("theme", "problem"),
                "kicker": beat.get("kicker"),
                "lines": beat.get("lines", []),
                "sub": beat.get("sub"),
            },
        )
        time.sleep(beat.get("hold", TIMING["card_hold"]))


def play_editor(page, beat: dict) -> None:
    page.evaluate("() => window.__demo.revealEditor()")
    time.sleep(TIMING["editor_settle"])
    edits = beat.get("edits", [])
    if edits:
        glide_to(page, ".b-table")
        time.sleep(0.35)
    for i, ed in enumerate(edits):
        edit_cell(page, ed["cell"], ed["to"], "ダブルクリックで直せる" if i == 0 else None)
    if beat.get("hero_bg"):
        set_hero_bg(page, beat["hero_bg"])
    ins = beat.get("insert")
    if ins:
        insert_block_after(page, ins["after_block"], ins["type"])
        if ins.get("edit_to"):
            edit_new_callout(page, ins["edit_to"])
    # Payoff: hero with new background
    glide_to(page, ".b-hero", settle=TIMING["glide"] + 0.35)
    time.sleep(0.6)


def record_profile(browser, profile: dict) -> dict:
    """Record one viewport profile. Returns paths + meta."""
    w, h = profile["width"], profile["height"]
    stem = profile["stem"]
    profile_id = profile["id"]
    print(f"[demo] recording {profile['label']} ({w}x{h}) …")

    context = browser.new_context(
        viewport={"width": w, "height": h},
        device_scale_factor=1,
        is_mobile=bool(profile.get("is_mobile")),
        has_touch=bool(profile.get("is_mobile")),
        record_video_dir=str(OUT_DIR),
        record_video_size={"width": w, "height": h},
    )
    # Seed workshop + paint a solid cover BEFORE Hatlier's first paint,
    # so the default tutorial never shows. We load the app ONCE and never
    # navigate again during the video — that removes the mid-clip flash.
    context.add_init_script(init_hatlier_script(WORKSHOP_DOC))
    page = context.new_page()

    page.goto(APP)
    page.wait_for_function("() => !!window.__hatlier")
    # Force workshop in case of a storage race (cover is still up either way)
    page.evaluate("(doc) => window.__hatlier.loadDoc(doc)", WORKSHOP_DOC)
    page.wait_for_selector(".b-hero")
    page.wait_for_function(
        """() => {
          const t = document.querySelector('.b-hero h1');
          const text = (t && t.textContent) || '';
          return text.includes('新メンバー') || text.includes('練習予定');
        }"""
    )
    page.wait_for_selector(".b-table tbody tr")
    page.evaluate(
        """(url) => new Promise((resolve) => {
          const img = new Image();
          img.onload = () => resolve(true);
          img.onerror = () => resolve(false);
          img.src = url;
        })""",
        HERO_BG,
    )
    # Overlay lives on the SAME page as Hatlier (loaded under the cover).
    inject_demo(page, profile_id)
    page.evaluate("() => window.__demo.ensureCover()")
    time.sleep(0.2)

    # Intro cards play over the cover; first card removes the cover behind it.
    play_intro(page)

    editor = next(b for b in STORY["beats"] if b["kind"] == "editor")
    play_editor(page, editor)

    end = next(b for b in STORY["beats"] if b["kind"] == "end")
    page.evaluate(
        "(b) => window.__demo.cutToEnd(b)",
        {"lines": end.get("lines", []), "sub": end.get("sub")},
    )
    time.sleep(end.get("hold", TIMING["end_hold"]))

    howto = next(b for b in STORY["beats"] if b["kind"] == "howto")
    page.evaluate(
        "(b) => window.__demo.cutToHowto(b)",
        {
            "kicker": howto.get("kicker"),
            "steps": howto.get("steps", []),
            "sub": howto.get("sub"),
        },
    )
    time.sleep(howto.get("hold", TIMING["howto_hold"]))

    video = page.video
    context.close()
    raw = Path(video.path())

    webm = OUT_DIR / f"{stem}.webm"
    mp4 = OUT_DIR / f"{stem}.mp4"
    if raw.resolve() != webm.resolve():
        if webm.exists():
            webm.unlink()
        raw.rename(webm)

    encoded = encode_mp4(webm, mp4)
    print(f"[demo] {profile['label']} webm:", webm)
    if encoded:
        print(f"[demo] {profile['label']} mp4:", encoded)
    return {"profile": profile_id, "webm": str(webm), "mp4": str(encoded) if encoded else None}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.webm", "*.mp4"):
        for old in OUT_DIR.glob(pattern):
            old.unlink()

    results = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="msedge", headless=True, args=["--hide-scrollbars"])
        except Exception:
            browser = p.chromium.launch(headless=True, args=["--hide-scrollbars"])
        for profile in PROFILES:
            results.append(record_profile(browser, profile))
        browser.close()

    # Convenience aliases (desktop = default share link)
    desk_mp4 = OUT_DIR / "core-edit-desktop.mp4"
    alias = OUT_DIR / "core-edit.mp4"
    if desk_mp4.exists():
        if alias.exists():
            alias.unlink()
        try:
            alias.hardlink_to(desk_mp4)
        except Exception:
            shutil.copy2(desk_mp4, alias)

    print("[demo] done")
    (OUT_DIR / "core-edit.scenario.json").write_text(
        json.dumps(
            {"timing": TIMING, "story": STORY, "profiles": PROFILES, "results": results},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
