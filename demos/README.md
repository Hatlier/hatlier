# Hatlier demos（自動録画）

Playwright（Chromium）で操作を再現し、画面を録画してデモ動画にします。  
製品本体（`hatlier.html`）には依存を足しません。

生成AIが映像を作っているわけではありません。**台本（`STORY`）＋尺（`TIMING`）＋操作手順**を決めて、毎回同じ手順でブラウザ録画しています。

## 出力（PC / スマホ）

| ファイル | 用途 | 解像度 |
|---|---|---|
| `demos/out/core-edit-desktop.mp4` | PC・横型（YouTube / X など） | 1280×720 |
| `demos/out/core-edit-mobile.mp4` | スマホ縦型（Stories / Reels など） | 1080×1920 |
| `demos/out/core-edit.mp4` | desktop のエイリアス | 同上 |

## ストーリー

| Beat | 色 | 意味 |
|---|---|---|
| problem | 暖色ダーク | 悩み（日付と定員が違う） |
| solution | 緑ダーク | Hatlier の答え |
| editor | （本体UI） | 表のセルを直す／背景／部品追加 |
| end | インク＋金 | ブランド締め |
| howto | 同上 | 使い方3ステップ |

カード同士は **不透明な色面のまま文言だけ切替**。  
エディタへ入る／出るときは **黒ベール**（チュートリアル文書は出さない）。

起動時は `localStorage` にワークショップ文書を先入れしてから Hatlier を開くので、  
デフォルトのチュートリアルが一瞬チラつくことはありません。

## 調整のしかた

`demos/record_core_edit.py` 先頭付近:

| 変数 | 役割 |
|---|---|
| `TIMING` | カード滞在・タイピング・ベール・編集後の間 |
| `STORY` | 文言・編集内容・締め・導線 |
| `WORKSHOP_DOC` | 実演ページの中身 |
| `PROFILES` | desktop / mobile の解像度 |

落ち着いて見せたい → `TIMING` の秒を伸ばす。  
文言だけ直したい → `STORY` の `lines` / `sub` / `steps` を編集して再実行。  
（今は Python を直して焼き直す運用。将来は `scenario.json` を手編集して読み込む形にもできる）

## 実行

```bash
py -m pip install --user playwright imageio-ffmpeg
py -m playwright install chromium
py demos/record_core_edit.py
```

両方の mp4 をまとめて書き出します（1本あたり数十秒〜1分強の実時間）。

## 音声は？

無理ではない（edge-tts / Supertonic など）。いまの標準出力は映像のみ。

## このPCだけ？ Pagesに載せられる？

| やりたいこと | どこで動くか |
|---|---|
| **Playwrightで宣伝用mp4を焼く** | このPC、または GitHub Actions |
| **できたmp4をPagesで配信** | できる（ファイルを置く） |
| **訪問者がHatlier上で「シナリオ→動画」** | フロント完結は別途可能（MediaRecorder） |
