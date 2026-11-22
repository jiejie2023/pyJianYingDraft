#!/usr/bin/env python3
"""
Build a complete rough-cut + packaged JianYing 11.8 plaintext draft for
`261115书法生想上国美央美` using pyJianYingDraft.

Features (strictly following 海晞口播剪辑与包装标准模板.md):
  1. Stage 1 — Pre-cut base prep applied across all main talking-head clips:
     1.3x playback speed + +10 dB voice gain (volume=3.162278) + 17-item Haixi beauty preset.
  2. Stage 2 — Non-destructive rough cut (removes retakes, stutters, fillers, and long silences/breaths).
  3. Stage 3 — Packaging:
     - Subtitles: FontType.金陵体 (or 俊雅体), size 13.5, lower-middle (y=-0.56), #FFFFFF,
       NO border/stroke + black shadow 85% (alpha=0.85), exact 1.3x synced timing.
     - Persistent top two-line title: FontType.清刻本悦 (FZQKBYSJW.ttf),
       Line 1 larger + bold (#FFFFFF), Line 2 smaller + normal weight (#FFF29D),
       NO border/stroke + black shadow 85%, positioned cleanly in top headroom.
     - Emphasis keyword splits: FontType.仓耳丰黑 + #FFF29D, direct font_size 18-21 (scale=1.0),
       NO border/stroke + black shadow 85%, paired below <=10-char main subtitle with zero duplication.
     - Verified masked proof PiP cards on left/right edges + looped BGM (-10 dB) + sparse SFX.
     - 100% self-contained draft (assets/ copied locally) + verified local JianYing font cache paths.
"""
from __future__ import annotations

import copy
import json
import os
import re
import shutil
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyJianYingDraft as draft
from pyJianYingDraft import (
    AudioMaterial,
    AudioSegment,
    ClipSettings,
    DraftFolder,
    FontType,
    IntroType,
    KeyframeProperty,
    OutroType,
    TextIntro,
    TextSegment,
    TextShadow,
    TextStyle,
    Timerange,
    TrackSpec,
    TrackType,
    VideoMaterial,
    VideoSceneEffectType,
    VideoSegment,
)

# ---------------------------------------------------------------------------
# Paths & Constants
# ---------------------------------------------------------------------------
JIANYING_DRAFTS_ROOT = Path(r"D:\Software\剪映\JianyingPro Drafts")
NEW_DRAFT_NAME = "261115书法生想上国美央美_AI粗剪包装_v9"

RAW_VIDEO_PATH = Path(r"D:\Software\剪映\AI素材库\261115书法生想上国美央美_原片.mp4")
BLACK_FIELD_PATH = Path(r"D:\Software\剪映\AI素材库\黑场_1920x1080.png")
CAA_GATE_PATH = Path(
    r"D:\Jiely Life\projects\海晞文化-内容助理\02_resources\书法海海知识库\01_IP知识库\02_IP图片\03_风景场所\20260707_中国美术学院校门，绿植覆盖的楼体与“大脑花园”活动海报.JPG"
)
CAFA_GATE_PATH = Path(
    r"D:\Jiely Life\projects\海晞文化-内容助理\02_resources\书法海海知识库\03_一鱼九吃库\00_一鱼九吃\02_待洗稿\01_高考\V20260916-04_高一抢跑书法专业\01_公众号\素材\06_中央美术学院.jpg"
)
LINEAR_MASK_CACHE_PATH = (
    "C:/Users/jiely/AppData/Local/JianyingPro/User Data/Cache/effect/"
    "82432976/4c6a0ef5de6a844342d40330e00c59eb"
)
LINEAR_MASK_RESOURCE_ID = "7356933362960831003"
CIRCLE_MASK_CACHE_PATH = (
    "C:/Users/jiely/AppData/Local/JianyingPro/User Data/Cache/effect/"
    "82432977/3ab1c47350d987c8ad415497e020a38b"
)
CIRCLE_MASK_RESOURCE_ID = "7356934080102928946"
BLUR_EFFECT_CACHE_PATH = (
    "C:/Users/jiely/AppData/Local/JianyingPro/User Data/Cache/effect/"
    "7399495140399746304/abb0b0e8472b73a42e796086c708d216"
)
BLUR_EFFECT_RESOURCE_ID = "7399495140399746304"
VIGNETTE_EFFECT_CACHE_PATH = (
    "C:/Users/jiely/AppData/Local/JianyingPro/User Data/Cache/effect/"
    "7399495012515433728/ef7abad9671e2f3da7993b7673ece5fc"
)
VIGNETTE_EFFECT_RESOURCE_ID = "7399495012515433728"
BEAUTY_PRESET_PATH = Path(
    r"D:\Jiely Life\projects\剪映AI草稿工具\02_resources\haixi_beauty_preset.json"
)
ASR_JSON_PATH = Path(
    r"C:\Users\jiely\.gemini\antigravity\brain\66a1cadc-f2f0-47fd-890f-b411ed01293a"
    r"\scratch\asr_261115\逐字稿\IOS_ALBUM@C9E3502E-DB9B-44B4-840F-A96EB5C16179_L0_001@1794747834000.json"
)
SILENCE_LOG_PATH = Path(
    r"C:\Users\jiely\.gemini\antigravity\brain\66a1cadc-f2f0-47fd-890f-b411ed01293a"
    r"\scratch\silence_261115.log"
)
SCRATCH_OUT_DIR = Path(
    r"C:\Users\jiely\.gemini\antigravity\brain\66a1cadc-f2f0-47fd-890f-b411ed01293a\scratch"
)

DRAFT1_AUDIO_DIR = Path(
    r"D:\Software\剪映\JianyingPro Drafts\书法生380-450能上什么学校 (1)\materials\audio"
)
DRAFT1_VIDEO_DIR = Path(
    r"D:\Software\剪映\JianyingPro Drafts\书法生380-450能上什么学校 (1)\materials\video"
)
PROOF_ROOT_DIR = Path(
    r"D:\Jiely Life\projects\海晞文化-内容助理\02_resources\书法海海知识库\06_交付知识库\02_交付证明"
)
PROOF_GAOSAN_DIR = PROOF_ROOT_DIR / "07_成绩结果图" / "03_高三"

CANVAS_WIDTH = 1320
CANVAS_HEIGHT = 1760
DRAFT_FPS = 30
PLAYBACK_SPEED = 1.3
VOICE_GAIN_DB = 10.0
VOICE_VOLUME = round(10.0 ** (VOICE_GAIN_DB / 20.0), 6)  # +10 dB = 3.162278

# Exact local font cache paths verified on this PC (from Draft 1 TL0, TL1 & TL3)
LOCAL_FONT_CACHE = {
    FontType.金陵体.value.resource_id: (
        "C:/Users/jiely/AppData/Local/JianyingPro/User Data/Cache/effect/"
        "7086699209738424840/599831579b8aa5b5f0608d5e7d4ec5ce/FZCuJinLJW.ttf"
    ),
    FontType.俊雅体.value.resource_id: (
        "C:/Users/jiely/AppData/Local/JianyingPro/User Data/Cache/effect/"
        "7078971008769593887/4f96b92a0023d2da2a4c9cb4e09e9565/造字工房俊雅体.ttf"
    ),
    FontType.清刻本悦.value.resource_id: (
        "C:/Users/jiely/AppData/Local/JianyingPro/User Data/Cache/effect/"
        "7086429206543864350/2e70579a0538bde91edc1eaedc68c02f/FZQKBYSJW.ttf"
    ),
    FontType.仓耳丰黑.value.resource_id: (
        "C:/Users/jiely/AppData/Local/JianyingPro/User Data/Cache/effect/"
        "7423616269397545499/cf1448c24a214eb3c9eb97f0d9883cde/仓耳丰黑.ttf"
    ),
}

# Colors (RGB 0..1)
COLOR_WHITE = (1.0, 1.0, 1.0)
COLOR_YELLOW = (1.0, 0.949, 0.616)  # #FFF29D — Haixi standard highlight yellow

# Confirmed retakes / stutters / isolated fillers to remove (source video seconds)
EXPLICIT_DELETE_RANGES: list[tuple[float, float, str]] = [
    (0.00, 0.68, "片头静音"),
    (13.95, 16.44, "重录前句：注定小孩的未来也是不一样的"),
    (42.55, 45.20, "口误重复尾词：评分逻辑"),
    (111.55, 120.42, "重录前句：核心只有八个字 + 半句平实死守文化"),
    (144.20, 145.82, "起句口误：口语书法"),
    (152.40, 153.92, "结巴重录：有的省本"),
    (159.50, 162.18, "连续结巴：比如今年的，比如说近"),
    (187.80, 189.10, "独立语气词：啊喂"),
    (199.80, 211.15, "重录整句：哪些省份的家长知道要赶紧大大捡漏..."),
    (223.50, 225.35, "重复连接词：所以"),
]

# ASR homophone/typo corrections (display text only)
TEXT_CORRECTIONS: list[tuple[str, str]] = [
    ("口语书法各省的", "各省的"),
    ("有的省本，有的省本科线", "有的省本科线"),
    ("比如今年的，比如说近，比如近年的", "比如近年的"),
    ("平实死守文化", "平时死守文化"),
    ("钗头", "拆透"),
    ("大大简陋", "大大捡漏"),
    ("文化大简陋", "文化大捡漏"),
    ("化氏机构", "画室机构"),
    ("一级篆刻", "以及篆刻"),
    ("围住的时间内", "为主的时间内"),
    ("篆课", "篆刻"),
    ("背文中", "背文综"),
    ("那一年的真题", "历年的真题"),
    ("折头", "掉头"),
    ("从来不是的呢，", "从来不是等到"),
    ("才去突击的是", "才去突击的事"),
    ("双线并进的长针啊喂", "双线并进的长征"),
    ("内蒙。", "内蒙"),
    ("四百", "400"),
    ("一百分", "100分"),
    ("书法一百", "书法100"),
    ("篆刻一百", "篆刻100"),
]


@dataclass
class KeptClip:
    src_start: float
    src_end: float
    tl_start_us: int = 0
    tl_dur_us: int = 0
    scale: float = 1.0
    transform_y: float = 0.0


def sec_to_us(seconds: float) -> int:
    return max(0, int(round(seconds * 1_000_000)))


def load_silences(path: Path) -> list[tuple[float, float]]:
    raw = path.read_bytes()
    text = raw.decode("utf-16", errors="ignore") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", errors="ignore")
    out: list[tuple[float, float]] = []
    cur: float | None = None
    for line in text.splitlines():
        m1 = re.search(r"silence_start:\s*([0-9.]+)", line)
        m2 = re.search(r"silence_end:\s*([0-9.]+)", line)
        if m1:
            cur = float(m1.group(1))
        if m2 and cur is not None:
            out.append((cur, float(m2.group(1))))
            cur = None
    return out


def merge_intervals(intervals: list[tuple[float, float]], gap: float = 0.05) -> list[tuple[float, float]]:
    if not intervals:
        return []
    ordered = sorted((min(a, b), max(a, b)) for a, b in intervals if b > a)
    merged = [ordered[0]]
    for a, b in ordered[1:]:
        pa, pb = merged[-1]
        if a <= pb + gap:
            merged[-1] = (pa, max(pb, b))
        else:
            merged.append((a, b))
    return merged


def subtract_intervals(
    base: list[tuple[float, float]],
    cuts: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    result = list(base)
    for ca, cb in cuts:
        nxt: list[tuple[float, float]] = []
        for a, b in result:
            if cb <= a or ca >= b:
                nxt.append((a, b))
            else:
                if a < ca:
                    nxt.append((a, ca))
                if cb < b:
                    nxt.append((cb, b))
        result = nxt
    return result


def compute_kept_clips(
    sentences: list[dict[str, Any]],
    silences: list[tuple[float, float]],
    video_duration_s: float,
) -> list[KeptClip]:
    """Build tight, breath-trimmed, retake-free video clips with safe speech padding."""
    # Start right before first spoken word, end gently after last spoken word
    first_speech = max(0.0, sentences[0]["start"] / 1000.0 - 0.12)
    last_speech = min(video_duration_s - 0.05, sentences[-1]["end"] / 1000.0 + 0.35)

    # Combine explicit retake/stutter cuts + trimmed long silences (> 0.28s)
    cut_ranges: list[tuple[float, float]] = [(a, b) for a, b, _ in EXPLICIT_DELETE_RANGES]

    # For any acoustic silence >= 0.30s, trim the middle while leaving 0.08s tail after speech
    # and 0.06s lead-in before next speech (natural breathing room, zero syllable clipping).
    for sa, sb in silences:
        dur = sb - sa
        if dur >= 0.30:
            trim_start = sa + 0.08
            trim_end = sb - 0.06
            if trim_end - trim_start >= 0.14:
                cut_ranges.append((trim_start, trim_end))

    # Also cut any inter-sentence gap >= 0.45s even if low room noise prevented -33dB trigger
    for prev_s, next_s in zip(sentences, sentences[1:]):
        g_start = prev_s["end"] / 1000.0
        g_end = next_s["start"] / 1000.0
        if g_end - g_start >= 0.45:
            trim_start = g_start + 0.10
            trim_end = g_end - 0.08
            if trim_end - trim_start >= 0.20:
                cut_ranges.append((trim_start, trim_end))

    merged_cuts = merge_intervals(cut_ranges, gap=0.05)
    raw_kept = subtract_intervals([(first_speech, last_speech)], merged_cuts)

    # Drop tiny noise blips (< 0.22s) that contain no ASR sentence overlap
    speech_spans = [(s["start"] / 1000.0, s["end"] / 1000.0) for s in sentences]

    def has_speech(a: float, b: float) -> bool:
        for sa, sb in speech_spans:
            if min(b, sb) - max(a, sa) >= 0.08:
                return True
        return False

    cleaned = [(a, b) for a, b in raw_kept if (b - a) >= 0.14 and has_speech(a, b)]
    # Ensure no non-deleted ASR sentence is accidentally lost by silence trimming
    for s in sentences:
        sa, sb = s["start"] / 1000.0, s["end"] / 1000.0
        if is_deleted_source(sa, sb):
            continue
        if not any(min(b, sb) - max(a, sa) >= 0.05 for a, b in cleaned):
            cleaned.append((max(first_speech, sa - 0.06), min(last_speech, sb + 0.08)))
    # Re-merge tiny gaps < 0.10s to avoid micro-cuts
    cleaned = merge_intervals(cleaned, gap=0.10)

    # Subtle punch-in rhythm at major semantic chapter breaks (keeps top headroom intact!)
    chapter_punch_starts = [36.0, 93.0, 130.0, 230.0, 325.0, 375.0, 439.0, 464.0]
    clips: list[KeptClip] = []
    cursor_us = 0
    for a, b in cleaned:
        src_start_us = sec_to_us(a)
        src_dur_us = sec_to_us(b - a)
        if src_dur_us < 100_000:
            continue
        tl_dur_us = round(src_dur_us / PLAYBACK_SPEED)
        # Alternate subtle 1.00 / 1.06 punch-in on chapter transitions
        chapter_idx = sum(1 for t in chapter_punch_starts if a >= t)
        punch = (chapter_idx % 2 == 1)
        clips.append(
            KeptClip(
                src_start=src_start_us / 1_000_000.0,
                src_end=(src_start_us + src_dur_us) / 1_000_000.0,
                tl_start_us=cursor_us,
                tl_dur_us=tl_dur_us,
                scale=1.06 if punch else 1.00,
                transform_y=-0.02 if punch else 0.00,
            )
        )
        cursor_us += tl_dur_us
    return clips


def map_src_to_tl_us(src_s: float, clips: list[KeptClip], *, prefer_end: bool = False) -> int | None:
    """Map a source-video timestamp (seconds) onto the 1.3x timeline (microseconds)."""
    for c in clips:
        if c.src_start <= src_s <= c.src_end:
            offset_us = round(((src_s - c.src_start) * 1_000_000.0) / PLAYBACK_SPEED)
            return c.tl_start_us + min(offset_us, c.tl_dur_us)
    # Snap gently if within 0.25s of a kept clip boundary
    best: tuple[float, int] | None = None
    for c in clips:
        if prefer_end:
            dist = abs(src_s - c.src_end)
            cand = c.tl_start_us + c.tl_dur_us
        else:
            dist = abs(src_s - c.src_start)
            cand = c.tl_start_us
        if dist <= 0.30 and (best is None or dist < best[0]):
            best = (dist, cand)
    return best[1] if best is not None else None


def is_deleted_source(a: float, b: float) -> bool:
    mid = (a + b) / 2.0
    for da, db, _ in EXPLICIT_DELETE_RANGES:
        if da <= mid <= db:
            return True
    return False


def clean_subtitle_text(text: str) -> str:
    s = text.strip()
    for wrong, right in TEXT_CORRECTIONS:
        s = s.replace(wrong, right)
    # Remove stray leading/trailing Chinese punctuation for crisp Douyin/XHS subtitle aesthetic
    s = re.sub(r"^[，。、！？；：,.!?;:\s]+", "", s)
    s = re.sub(r"[，。、；：,.;:\s]+$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _smart_chinese_split(chunk: str, max_chars: int) -> list[str]:
    """Recursively split a Chinese clause at natural semantic boundaries so EVERY part <= max_chars."""
    chunk = chunk.strip()
    if len(chunk) <= max_chars:
        return [chunk] if chunk else []
    # Preferred natural break tokens (break BEFORE these words)
    break_before = [
        "以及", "而且", "但是", "或者", "并且", "就是", "其实", "最后", "同时",
        "然后", "直接", "利用", "能够", "已经", "如果", "因为", "所以", "比如",
        "到底", "如何", "怎么", "绝不要", "不要", "可以", "应该", "还是", "或者",
        "全国", "各省", "书法", "文化", "专业", "国美", "央美", "和", "给", "把", "去", "在", "到",
    ]
    # Preferred break AFTER these tokens
    break_after = ["的", "了", "啊", "呢", "吧", "上", "中", "里", "后", "前", "是", "有"]
    mid = len(chunk) // 2
    min_left = max(2, len(chunk) - max_chars)
    max_left = min(len(chunk) - 2, max_chars)
    best_idx = None
    best_dist = 999

    # Prefer whitespace boundary first if present within valid range
    for m in re.finditer(r"\s+", chunk):
        pos = m.start()
        if min_left <= pos <= max_left and abs(pos - mid) < best_dist:
            best_dist = abs(pos - mid)
            best_idx = pos

    if best_idx is None:
        for tok in break_before:
            start_search = max(2, min_left)
            pos = chunk.find(tok, start_search)
            while pos != -1 and pos <= max_left:
                if abs(pos - mid) < best_dist:
                    best_dist = abs(pos - mid)
                    best_idx = pos
                pos = chunk.find(tok, pos + 1)

    if best_idx is None or best_dist > 4:
        for tok in break_after:
            pos = chunk.find(tok, 1)
            while pos != -1:
                cand = pos + len(tok)
                if min_left <= cand <= max_left and abs(cand - mid) < best_dist:
                    best_dist = abs(cand - mid)
                    best_idx = cand
                pos = chunk.find(tok, pos + 1)

    if best_idx is None:
        best_idx = min(max_left, max(min_left, mid))

    left = chunk[:best_idx].strip()
    right = chunk[best_idx:].strip()
    out: list[str] = []
    if left:
        out.extend(_smart_chinese_split(left, max_chars))
    if right:
        out.extend(_smart_chinese_split(right, max_chars))
    return out


# Paired emphasis-split rules (SOP: main subtitle <= 10 chars on top + highlighted keyword split below, ZERO duplication!)
# All emphasis keywords use FontType.仓耳丰黑 + COLOR_YELLOW (#FFF29D) + direct font_size (18-21, scale=1.0).
# Format: (match_text, main_text_le_10, kw_text, kw_font_size, kw_anim, sfx_name, sfx_vol)
KEYWORD_SPLIT_RULES: list[tuple[str, str, str, float, TextIntro, str, float]] = [
    ("书法生想上国美央美", "书法生想上", "国美央美", 21.0, TextIntro.向上弹入, "ding", 0.45),
    ("应该给孩子如何规划", "应该给孩子", "如何规划？", 20.5, TextIntro.向上弹入, "drop", 0.45),
    ("从本科读到硕士 一共七年", "从本科读到硕士", "一共七年", 20.0, TextIntro.向上弹入, "drop", 0.45),
    ("每年很多孩子拿到了国央的合格证", "每年很多孩子拿到了", "国央的合格证", 19.0, TextIntro.向上弹入, "ding", 0.48),
    ("很多孩子拿到了国央的合格证", "每年很多孩子拿到了", "国央的合格证", 19.0, TextIntro.向上弹入, "ding", 0.48),
    ("最后都硬生生的折在了文化分上", "最后都硬生生的", "折在了文化分上", 18.5, TextIntro.缩小, "dong", 0.42),
    ("平时死守文化课", "平时死守", "文化课", 21.0, TextIntro.向上弹入, "ding", 0.46),
    ("就一个 不低于本省的本科线", "就一个", "不低于本省本科线", 18.0, TextIntro.左移弹动, "drop", 0.45),
    ("竟然可以悬殊100分", "竟然可以", "悬殊100分!", 20.0, TextIntro.缩小, "stamp", 0.46),
    ("去画室机构烧钱集训", "去画室机构", "烧钱集训", 20.0, TextIntro.向上弹入, "dong", 0.40),
    ("就可以让小孩尽早接触篆刻科目啦", "就可以让小孩尽早接触", "篆刻科目", 20.0, TextIntro.左移弹动, "ding", 0.48),
    ("校考科目有大半的分数都在篆刻", "校考科目有大半的分数", "都在篆刻", 20.0, TextIntro.缩小, "stamp", 0.46),
    ("直接占了分数的大半壁江山", "直接占了分数的", "大半壁江山", 19.5, TextIntro.向上弹入, "drop", 0.45),
    ("绝不要彻底丢掉文化课", "绝不要彻底丢掉", "文化课", 21.0, TextIntro.缩小, "dong", 0.42),
    ("那么可以留下书法艺考", "那么可以留下", "书法艺考", 20.0, TextIntro.向上弹入, "ding", 0.50),
]


def _match_keyword_split(text: str) -> tuple[str, str, float, TextIntro, str, float] | None:
    norm = re.sub(r"\s+", " ", text).strip()
    norm_compact = norm.replace(" ", "")
    for pat, main_t, kw_t, kw_sz, anim, sfx_k, sfx_v in KEYWORD_SPLIT_RULES:
        pat_compact = pat.replace(" ", "")
        # Require near-exact match so an extra clause before/after pat is NEVER silently swallowed!
        if norm_compact == pat_compact or (pat_compact in norm_compact and abs(len(norm_compact) - len(pat_compact)) <= 2):
            return (main_t, kw_t, kw_sz, anim, sfx_k, sfx_v)
    return None


def split_long_cue(text: str, start_us: int, end_us: int, max_chars: int = 10) -> list[tuple[int, int, str]]:
    """Split a subtitle sentence cleanly so EVERY regular subtitle cue <= max_chars (10 chars)."""
    dur = end_us - start_us
    # If this sentence matches an explicit keyword-split rule, keep intact for paired main+keyword splitting!
    if _match_keyword_split(re.sub(r"[，。、；：,]+", " ", text).strip()) is not None:
        return [(start_us, end_us, re.sub(r"[，。、；：,]+", " ", text).strip())]

    clean_single = re.sub(r"[，。、；：,]+", " ", text).strip()
    if len(clean_single) <= max_chars:
        return [(start_us, end_us, clean_single)]

    # Split on strong & soft punctuation first
    parts = [p.strip() for p in re.split(r"[，。！？、；：,]", text) if p.strip()]
    merged: list[str] = []
    for part in parts:
        # Don't merge a trailing province fragment ("内蒙") onto a digit-ending score ("吉林340")
        if merged and merged[-1][-1].isdigit() and part == "内蒙":
            merged.append(part)
        elif merged and len(merged[-1]) + 1 + len(part) <= max_chars:
            merged[-1] = merged[-1] + " " + part
        elif merged and len(part) <= 2 and len(merged[-1]) + len(part) <= max_chars:
            merged[-1] = merged[-1] + part
        else:
            merged.append(part)

    final_parts: list[str] = []
    for chunk in merged:
        if len(chunk) <= max_chars:
            final_parts.append(chunk)
        else:
            final_parts.extend(_smart_chinese_split(chunk, max_chars))

    total_chars = max(1, sum(len(p) for p in final_parts))
    cues: list[tuple[int, int, str]] = []
    cur = start_us
    for i, part in enumerate(final_parts):
        if i == len(final_parts) - 1:
            nxt = end_us
        else:
            share = round(dur * len(part) / total_chars)
            nxt = min(end_us - 100_000, cur + max(200_000, share))
        if nxt > cur:
            cues.append((cur, nxt, part))
            cur = nxt
    return cues


def build_subtitle_cues(sentences: list[dict[str, Any]], clips: list[KeptClip]) -> list[tuple[int, int, str]]:
    """Convert ASR sentences into clean, non-overlapping 1.3x timeline subtitle cues (<= 10 chars unless keyword-split)."""
    raw_cues: list[tuple[int, int, str, bool]] = []  # (start_us, end_us, text, ends_sentence)

    for sent in sentences:
        sa = sent["start"] / 1000.0
        sb = sent["end"] / 1000.0
        txt = str(sent.get("sentence", ""))

        # Handle opening boundary ("书法生想上国美、" + "央美，高中三年...") and trimmed prefix deletions
        if abs(sa - 0.78) < 0.2:
            sb = 2.75
            txt = "书法生想上国美央美"
        elif abs(sa - 2.34) < 0.2:
            sa = 2.75
            txt = "高中三年到底应该给孩子如何规划？"
        elif abs(sa - 144.44) < 0.2:
            sa = 145.90
            txt = "各省的书法生家长注意了哈"
        elif abs(sa - 152.66) < 0.2:
            sa = 154.00
            txt = "有的省本科线很高啊"
        elif abs(sa - 159.85) < 0.2:
            sa = 162.20
            txt = "比如近年的本科线啊，浙江省490，江苏省480，河南460，山东440"
        elif abs(sa - 37.61) < 0.2:
            sb = 42.50
            txt = "太清楚书法校考以及全国各省统考的评分逻辑是怎么样的"
        elif abs(sa - 173.95) < 0.2:
            # Keep 内蒙 open so it merges cleanly with next "400" cue
            txt = "而我们再来看一些北方城市，黑龙江380，吉林340，内蒙"

        if is_deleted_source(sa, sb):
            continue

        overlapping_clips = [c for c in clips if min(sb, c.src_end) - max(sa, c.src_start) >= 0.05]
        if not overlapping_clips:
            continue

        ends_sentence = txt.strip().endswith(("。", "！", "？"))
        clean_txt = clean_subtitle_text(txt)
        if not clean_txt:
            continue

        t0 = map_src_to_tl_us(max(sa, overlapping_clips[0].src_start), clips, prefer_end=False)
        t1 = map_src_to_tl_us(min(sb, overlapping_clips[-1].src_end), clips, prefer_end=True)
        if t0 is None or t1 is None or t1 - t0 < 120_000:
            continue

        sub_parts = split_long_cue(clean_txt, t0, t1, max_chars=10)
        for idx_p, (pst, ped, ptxt) in enumerate(sub_parts):
            raw_cues.append((pst, ped, ptxt, ends_sentence and idx_p == len(sub_parts) - 1))

    # Merge tiny fragments cleanly without exceeding 10 chars (except explicit keyword-split sentences!)
    merged_cues: list[tuple[int, int, str, bool]] = []
    for st, ed, txt, ends_s in sorted(raw_cues, key=lambda x: x[0]):
        if merged_cues:
            pst, ped, ptxt, p_ends = merged_cues[-1]
            if st < ped:
                st = ped
            if ed <= st + 90_000:
                continue
            # Special merge: "每年" + "很多孩子拿到了国央的合格证" -> full keyword-split sentence
            if ptxt == "每年" and "很多孩子拿到了" in txt:
                merged_cues[-1] = (pst, ed, ptxt + txt, ends_s)
                continue
            # Special merge: "内蒙" + "400" -> "内蒙400"
            if ptxt == "内蒙" and txt == "400":
                merged_cues[-1] = (pst, ed, "内蒙400", True)
                continue
            # Merge short fragment ONLY if result stays <= 10 chars and doesn't cross sentence boundary
            if (
                not p_ends
                and _match_keyword_split(ptxt) is None
                and _match_keyword_split(txt) is None
                and (st - ped) <= 400_000
            ):
                if len(ptxt) <= 3 and len(ptxt) + len(txt) <= 10:
                    sep = " " if (ptxt[-1].isdigit() or txt[0].isdigit()) else ""
                    if len(ptxt) + len(sep) + len(txt) <= 10:
                        merged_cues[-1] = (pst, ed, ptxt + sep + txt, ends_s)
                        continue
                if len(txt) <= 3 and len(ptxt) + len(txt) <= 10:
                    merged_cues[-1] = (pst, ed, ptxt + txt, ends_s)
                    continue
        merged_cues.append((st, ed, txt, ends_s))

    # Final pass: guarantee any cue not matched by a keyword-split rule is strictly <= 10 chars
    #             AND split "高中三年到底应该给孩子如何规划" into "高中三年到底" + "应该给孩子如何规划"
    final_cues: list[tuple[int, int, str]] = []
    for st, ed, txt, _ in merged_cues:
        if txt == "高中三年到底应该给孩子如何规划？" or txt == "高中三年到底应该给孩子如何规划":
            mid = st + round((ed - st) * 6 / 15)
            final_cues.append((st, mid, "高中三年到底"))
            final_cues.append((mid, ed, "应该给孩子如何规划"))
        elif _match_keyword_split(txt) is not None or len(txt) <= 10:
            final_cues.append((st, ed, txt))
        else:
            final_cues.extend(split_long_cue(txt, st, ed, max_chars=10))
    return final_cues


def find_cue_range(cues: list[tuple[int, int, str]], keyword: str, after_us: int = 0) -> tuple[int, int] | None:
    for st, ed, txt in cues:
        if st >= after_us and keyword in txt:
            return st, ed
    return None


def copy_asset(src: Path, dest_dir: Path, short_name: str) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dst = dest_dir / short_name
    shutil.copy2(src, dst)
    return dst


def patch_draft_postprocess(
    draft_dir: Path,
    draft_name: str,
    total_duration_us: int,
    vignette_ranges: list[tuple[int, int]] | None = None,
) -> None:
    """Post-process draft_content.json & draft_meta_info.json:
    1. Inject Haixi 17-item beauty preset onto every main talking-head clip (and circular PiP)
       and mirror +10 dB gain into last_nonzero_volume.
    2. Attach native JianYing 11.8 linear mask on top gradient shadow & circular mask on speaker PiP.
    3. Inject restrained TL0 vignette (`暗角`) effect track at key emphasis beats.
    4. Inject verified local JianYing font cache paths, sync bold_width & shadow
       properties, and enforce zero stroke/border when strokes is empty.
    """
    content_path = draft_dir / "draft_content.json"
    data = json.loads(content_path.read_text(encoding="utf-8"))

    # 1. Inject beauty preset + mirror volume into last_nonzero_volume on main video track
    beauty_templates: list[dict[str, Any]] = []
    if BEAUTY_PRESET_PATH.exists():
        beauty_cfg = json.loads(BEAUTY_PRESET_PATH.read_text(encoding="utf-8"))
        beauty_templates = list(beauty_cfg.get("effects") or [])

    effects_list = data.setdefault("materials", {}).setdefault("effects", [])
    masks_list = data.setdefault("materials", {}).setdefault("common_mask", [])
    vfx_list = data.setdefault("materials", {}).setdefault("video_effects", [])
    beauty_clips = 0
    beauty_refs_total = 0
    top_shadow_masks = 0
    circle_pip_masks = 0
    for tr in data.get("tracks", []):
        if tr.get("type") == "video" and tr.get("name") == "主视频_1.3x粗剪":
            for seg in tr.get("segments", []):
                seg["volume"] = VOICE_VOLUME
                seg["last_nonzero_volume"] = VOICE_VOLUME
                if beauty_templates:
                    extra_refs = seg.setdefault("extra_material_refs", [])
                    for tmpl in beauty_templates:
                        eff = copy.deepcopy(tmpl)
                        eff_id = str(uuid.uuid4()).upper()
                        eff["id"] = eff_id
                        effects_list.append(eff)
                        extra_refs.append(eff_id)
                        beauty_refs_total += 1
                    beauty_clips += 1
        elif tr.get("type") == "video" and tr.get("name") == "圆形画中画_海老师":
            for seg in tr.get("segments", []):
                seg["volume"] = 0.0
                seg["last_nonzero_volume"] = 0.0
                extra_refs = seg.setdefault("extra_material_refs", [])
                # Exact 1:1 pixel circle on 1320x1760 (0.58*1320 == 0.435*1760 == 765.6px)
                cmask_id = str(uuid.uuid4()).upper()
                cmask_obj = {
                    "id": cmask_id,
                    "constant_material_id": str(uuid.uuid4()).upper(),
                    "name": "圆形",
                    "type": "mask",
                    "category": "video",
                    "category_id": "jichu",
                    "category_name": "基础",
                    "resource_type": "circle",
                    "resource_id": CIRCLE_MASK_RESOURCE_ID,
                    "path": CIRCLE_MASK_CACHE_PATH,
                    "text_config": {"align_type": 15},
                    "config": {
                        "aspectRatio": 1.0,
                        "centerX": 0.0,
                        "centerY": 0.14,
                        "feather": 0.1732,  # Exact user hand-tuned soft circular feather from v8!
                        "height": 0.435,
                        "invert": False,
                        "rotation": 0.0,
                        "roundCorner": 0.0,
                        "width": 0.58,
                    },
                }
                masks_list.append(cmask_obj)
                extra_refs.append(cmask_id)
                circle_pip_masks += 1
                if beauty_templates:
                    for tmpl in beauty_templates:
                        eff = copy.deepcopy(tmpl)
                        eff_id = str(uuid.uuid4()).upper()
                        eff["id"] = eff_id
                        effects_list.append(eff)
                        extra_refs.append(eff_id)
                        beauty_refs_total += 1
        elif tr.get("type") == "video" and tr.get("name") == "顶部渐变阴影_黑场":
            for seg in tr.get("segments", []):
                mask_id = str(uuid.uuid4()).upper()
                mask_obj = {
                    "id": mask_id,
                    "constant_material_id": str(uuid.uuid4()).upper(),
                    "name": "线性",
                    "type": "mask",
                    "category": "video",
                    "category_id": "jichu",
                    "category_name": "基础",
                    "resource_type": "line",
                    "resource_id": LINEAR_MASK_RESOURCE_ID,
                    "path": LINEAR_MASK_CACHE_PATH,
                    "text_config": {"align_type": 15},
                    "config": {
                        "aspectRatio": 1.0,
                        "centerX": 0.0,
                        "centerY": 0.316,
                        "feather": 1.0,
                        "height": 0.5,
                        "invert": False,
                        "rotation": 0.0,
                        "roundCorner": 0.0,
                        "width": 0.28,
                    },
                }
                masks_list.append(mask_obj)
                seg.setdefault("extra_material_refs", []).append(mask_id)
                top_shadow_masks += 1

    # 2. Patch segment-level `模糊` video effects on Track 0 to verified local 11.8 cache & apply_target_type=0
    #    (STRICTLY main-video-only so Track 0 blur NEVER bleeds onto semi-transparent black bars or circular speaker PiP!)
    patched_blurs = 0
    for ve in vfx_list:
        if ve.get("name") == "模糊":
            ve["apply_target_type"] = 0
            ve["resource_id"] = BLUR_EFFECT_RESOURCE_ID
            ve["effect_id"] = BLUR_EFFECT_RESOURCE_ID
            ve["path"] = BLUR_EFFECT_CACHE_PATH
            ve["category_id"] = "39654"
            ve["category_name"] = "热门"
            ve["source_platform"] = 1
            patched_blurs += 1

    # 2b. Inject restrained TL0 `暗角` video effect track (non-gimmicky, manual-edit taste)
    vignette_added = 0
    if vignette_ranges:
        eff_segments: list[dict[str, Any]] = []
        for idx_v, (vst, vdur) in enumerate(vignette_ranges):
            if vdur <= 0:
                continue
            mat_id = str(uuid.uuid4()).upper()
            vfx_list.append(
                {
                    "apply_target_type": 2,
                    "path": VIGNETTE_EFFECT_CACHE_PATH,
                    "category_name": "热门",
                    "id": mat_id,
                    "category_id": "39654",
                    "resource_id": VIGNETTE_EFFECT_RESOURCE_ID,
                    "effect_id": VIGNETTE_EFFECT_RESOURCE_ID,
                    "name": "暗角",
                    "type": "video_effect",
                    "value": 1,
                    "source_platform": 1,
                    "adjust_params": [
                        {"default_value": 1, "name": "effects_adjust_texture", "value": 1}
                    ],
                }
            )
            eff_segments.append(
                {
                    "id": str(uuid.uuid4()).upper(),
                    "material_id": mat_id,
                    "source": "segmentsourcenormal",
                    "target_timerange": {"start": vst, "duration": vdur},
                    "render_index": 11001 + idx_v,
                    "enable_adjust": False,
                    "enable_adjust_mask": False,
                    "enable_hsl": False,
                    "enable_lut": False,
                    "responsive_layout": {},
                    "render_timerange": {},
                    "extra_material_refs": [],
                    "common_keyframes": [],
                }
            )
            vignette_added += 1
        if eff_segments:
            data.setdefault("tracks", []).append(
                {
                    "attribute": 0,
                    "flag": 0,
                    "id": str(uuid.uuid4()).upper(),
                    "is_default_name": False,
                    "name": "画面特效_克制暗角",
                    "segments": eff_segments,
                    "type": "effect",
                }
            )

    # 2. Patch text materials (local font path, shadow, bold_width, zero-stroke check)
    patched_fonts = 0
    for mat in data.get("materials", {}).get("texts", []):
        raw_content = mat.get("content", "")
        if not isinstance(raw_content, str) or not raw_content.lstrip().startswith("{"):
            continue
        cjson = json.loads(raw_content)
        styles = cjson.get("styles") or []
        if styles and isinstance(styles[0], dict):
            st0 = styles[0]
            if "size" in st0:
                mat["font_size"] = st0["size"]
            is_bold = bool(st0.get("bold", False))
            mat["bold_width"] = 0.008 if is_bold else 0.0

            strokes = st0.get("strokes") or []
            if strokes and isinstance(strokes[0], dict):
                mat["border_width"] = strokes[0].get("width", 0.08)
            else:
                # Explicitly ensure no border/stroke flag (bit 8) is active
                mat["check_flag"] = int(mat.get("check_flag", 39)) & ~8
                mat.pop("border_width", None)

            shadows = st0.get("shadows") or []
            if shadows and isinstance(shadows[0], dict):
                mat["has_shadow"] = True
                mat["shadow_color"] = "#000000"
                mat["shadow_alpha"] = shadows[0].get("alpha", 0.85)
                mat["shadow_distance"] = shadows[0].get("distance", 5.0)
                mat["shadow_angle"] = shadows[0].get("angle", -45.0)
            font_obj = st0.get("font")
            if isinstance(font_obj, dict):
                fid = str(font_obj.get("id") or "")
                local_ttf = LOCAL_FONT_CACHE.get(fid)
                if local_ttf and Path(local_ttf).exists():
                    font_obj["path"] = local_ttf
                    mat["font_path"] = local_ttf
                    mat["font_resource_id"] = fid
                    mat["content"] = json.dumps(cjson, ensure_ascii=False)
                    patched_fonts += 1

    content_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3. Update draft_meta_info.json with proper name & duration
    meta_path = draft_dir / "draft_meta_info.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["draft_name"] = draft_name
        meta["draft_fold_path"] = str(draft_dir).replace("\\", "/")
        meta["draft_root_path"] = str(draft_dir.parent).replace("\\", "/")
        meta["tm_duration"] = total_duration_us
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"[patch] beauty preset attached to {beauty_clips} main clips (+{circle_pip_masks} circular PiP clips, {beauty_refs_total} effect refs); "
        f"linear masks={top_shadow_masks}, main-only segment blurs={patched_blurs}, restrained vignettes={vignette_added}; "
        f"verified local fonts injected on {patched_fonts} text materials"
    )


def write_srt(cues: list[tuple[int, int, str]], out_path: Path) -> None:
    def fmt(us: int) -> str:
        ms = max(0, us // 1000)
        h, rem = divmod(ms, 3_600_000)
        m, rem = divmod(rem, 60_000)
        s, ms = divmod(rem, 1_000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    blocks = []
    for i, (st, ed, txt) in enumerate(cues, start=1):
        blocks.append(f"{i}\n{fmt(st)} --> {fmt(ed)}\n{txt}\n")
    out_path.write_text("\n".join(blocks), encoding="utf-8")


def main() -> int:
    # 1. Load ASR + acoustic silence map
    asr_raw = json.loads(ASR_JSON_PATH.read_text(encoding="utf-8"))
    if isinstance(asr_raw, list):
        asr_raw = asr_raw[0]
    sentences: list[dict[str, Any]] = asr_raw["sentence_info"]
    silences = load_silences(SILENCE_LOG_PATH)

    raw_mat = VideoMaterial(str(RAW_VIDEO_PATH))
    video_dur_s = raw_mat.duration / 1_000_000.0
    print(f"[source] {RAW_VIDEO_PATH.name} ({raw_mat.width}x{raw_mat.height}, {video_dur_s:.2f}s)")

    # 2. Compute rough-cut kept clips & synced 1.3x subtitle cues
    clips = compute_kept_clips(sentences, silences, video_dur_s)
    total_src_kept_s = sum(c.src_end - c.src_start for c in clips)
    total_tl_us = clips[-1].tl_start_us + clips[-1].tl_dur_us
    total_tl_s = total_tl_us / 1_000_000.0
    cues = build_subtitle_cues(sentences, clips)

    print(f"[rough-cut] {len(clips)} kept clips | raw {video_dur_s:.1f}s -> kept {total_src_kept_s:.1f}s -> @1.3x = {total_tl_s:.2f}s")
    print(f"[subtitles] {len(cues)} synced cues")

    # Save audit artifacts to scratch
    SCRATCH_OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_srt(cues, SCRATCH_OUT_DIR / "261115_1.3x_synced.srt")
    (SCRATCH_OUT_DIR / "261115_cut_plan.json").write_text(
        json.dumps(
            {
                "raw_duration_s": round(video_dur_s, 2),
                "kept_1x_duration_s": round(total_src_kept_s, 2),
                "timeline_1_3x_duration_s": round(total_tl_s, 2),
                "playback_speed": PLAYBACK_SPEED,
                "explicit_deletes": EXPLICIT_DELETE_RANGES,
                "clips": [c.__dict__ for c in clips],
                "subtitles": [{"start_s": round(a / 1e6, 2), "end_s": round(b / 1e6, 2), "text": t} for a, b, t in cues],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # 3. Create brand-new JianYing draft (never touches the original raw draft!)
    folder = DraftFolder(str(JIANYING_DRAFTS_ROOT))
    script = folder.create_draft(
        NEW_DRAFT_NAME,
        CANVAS_WIDTH,
        CANVAS_HEIGHT,
        fps=DRAFT_FPS,
        maintrack_adsorb=False,
        allow_replace=True,
    )
    draft_dir = JIANYING_DRAFTS_ROOT / NEW_DRAFT_NAME
    asset_vid_dir = draft_dir / "assets" / "video"
    asset_img_dir = draft_dir / "assets" / "images"
    asset_aud_dir = draft_dir / "assets" / "audio"

    # Copy raw video into draft's own assets/video/ so the draft is 100% self-contained
    self_contained_vid = copy_asset(RAW_VIDEO_PATH, asset_vid_dir, "261115_raw.mp4")
    raw_mat = VideoMaterial(str(self_contained_vid))

    # Copy self-contained BGM, SFX, and verified proof images into new draft folder
    bgm_path = copy_asset(DRAFT1_AUDIO_DIR / "55c164ff20b76d77a0d845b1ad74522f.mp3", asset_aud_dir, "bgm_chinese_zither.mp3")
    sfx_drop = copy_asset(DRAFT1_AUDIO_DIR / "fd8b75a140bba2a6bad77df92e6598dd.mp3", asset_aud_dir, "sfx_water_drop.mp3")
    sfx_dong = copy_asset(DRAFT1_AUDIO_DIR / "4c4801715dbe9272b61a6d0fa1f4d6f6.mp3", asset_aud_dir, "sfx_dong.mp3")
    sfx_ding = copy_asset(DRAFT1_AUDIO_DIR / "26fac03104a2059d7c1bb4ecd0eccb4d.mp3", asset_aud_dir, "sfx_dingdong.mp3")
    sfx_whoosh = copy_asset(DRAFT1_AUDIO_DIR / "0291b72047769e085e7595ce5d65dbd2.mp3", asset_aud_dir, "sfx_whoosh.mp3")
    sfx_stamp = copy_asset(DRAFT1_AUDIO_DIR / "f2c28329e88e189b89fa16f59fc65464.mp3", asset_aud_dir, "sfx_stamp.mp3")
    sfx_page = copy_asset(DRAFT1_AUDIO_DIR / "bcebdd78f3173216cb1aaae12f7dd291.mp3", asset_aud_dir, "sfx_page.mp3")

    img_caa_gate = copy_asset(CAA_GATE_PATH, asset_img_dir, "00_中国美术学院校门头.jpg")
    img_cafa_gate = copy_asset(CAFA_GATE_PATH, asset_img_dir, "00_中央美术学院校门头.jpg")
    img_gm_2nd = copy_asset(
        PROOF_GAOSAN_DIR / "008_展示一名书法考生从复读到国美全国第二的录取成果，含分数、名次及录取喜报.jpg",
        asset_img_dir,
        "01_国美全国第二.jpg",
    )
    img_gm_xibao = copy_asset(
        PROOF_GAOSAN_DIR / "283_红底喜报图，展示中国美术学院2025年书法学复试合格截图，含分数、名次及“合格”字样.jpg",
        asset_img_dir,
        "02_国美喜报.jpg",
    )
    img_ym_notice = copy_asset(
        PROOF_GAOSAN_DIR / "20261104_中央美术学院录取通知书与入学手册（姓名贴纸打码版）.png",
        asset_img_dir,
        "03_央美录取通知书打码版.png",
    )
    img_rank1 = copy_asset(
        DRAFT1_VIDEO_DIR / "286_展示全省统考第一的成绩截图、聊天记录及学生反馈，含“全省状元”“总分267.0”字样.jpg",
        asset_img_dir,
        "04_省统考第1名.jpg",
    )
    img_rank3 = copy_asset(
        DRAFT1_VIDEO_DIR / "294_展示2026年吉林省统考成绩截图及微信聊天记录，明确显示总分265分、全省第3名.jpg",
        asset_img_dir,
        "05_省统考第3名.jpg",
    )
    img_rank7 = copy_asset(
        DRAFT1_VIDEO_DIR / "300_展示学生书法统考成绩268.8000分及全省第7名的喜报截图.jpg",
        asset_img_dir,
        "06_省统考第7名.jpg",
    )
    img_online_class = copy_asset(DRAFT1_VIDEO_DIR / "01_高一全程线上.jpg", asset_img_dir, "07_高一全程线上.jpg")
    img_1v1 = copy_asset(DRAFT1_VIDEO_DIR / "05_1v1讲评_v3.png", asset_img_dir, "08_1v1讲评.png")
    img_ym_zhuanke = copy_asset(
        PROOF_GAOSAN_DIR / "1060_央美篆刻状元喜报，标注篆刻92全国最高分与线上全程班.jpg",
        asset_img_dir,
        "09_央美篆刻92分全国最高.jpg",
    )
    # Personal credential full-screen B-roll (国美本硕7年)
    img_haixi_609 = copy_asset(
        DRAFT1_VIDEO_DIR / "1164_穿校服的女生在校园树下留影，下方展板写着“海晞（609.5分）年级排名8 中国美术学院”.jpg",
        asset_img_dir,
        "10_海晞609分国美校园.jpg",
    )
    img_gm_diploma = copy_asset(
        DRAFT1_VIDEO_DIR / "03_中国美术学院毕业证书封皮.jpg",
        asset_img_dir,
        "11_国美毕业证封皮.jpg",
    )
    img_gm_master = copy_asset(
        DRAFT1_VIDEO_DIR / "02_国美硕士毕业_蓝色硕士服红立柱.jpg",
        asset_img_dir,
        "12_国美硕士毕业照.jpg",
    )
    # Grade 1/2/3 planning, seal-carving (篆刻), ancient Chinese (古汉语), and end service-value proof assets
    img_plan_g1 = copy_asset(
        PROOF_ROOT_DIR / "01_学生规划图/01_高一/001_这是一张宣传海报，主体为“书法海海线上教育”的“高一”课程推广。画面包含两份微信聊天记录截图，内容涉及书法学习规划、隶书课程资料及作业安排，.jpg",
        asset_img_dir,
        "13_高一学习规划海报.jpg",
    )
    img_g1_lishu_prog = copy_asset(
        PROOF_ROOT_DIR / "05_进步对比图/01_高一/108_展示高一学生隶书创作“前”后对比，画面包含“书法海海线上特训营”、“2V1精品辅导”及“15天效果”字样.jpg",
        asset_img_dir,
        "14_高一隶书15天前后对比.jpg",
    )
    img_g2_zhuanke_20d = copy_asset(
        PROOF_ROOT_DIR / "05_进步对比图/02_高二/144_展示高二同学篆刻作品20天效果对比，左侧为前，右侧为后，标注日期26.2.25.jpg",
        asset_img_dir,
        "15_高二国央篆刻20天对比.jpg",
    )
    img_zk_compare_1002 = copy_asset(
        PROOF_ROOT_DIR / "05_进步对比图/03_高三/1002_线上篆刻（国美_央美校考）2V1精品辅导前后对比，标注“篆刻状元”“篆刻92 全国最高分”.jpg",
        asset_img_dir,
        "16_线上篆刻国央校考前后对比.jpg",
    )
    img_zk_compare_1007 = copy_asset(
        PROOF_ROOT_DIR / "05_进步对比图/03_高三/1007_这是一张宣传海报，主体为“线上篆刻”及“国美·央美校考2V1精品辅导”大字标题，下方展示多组篆刻作品对比图（含“前”“后”字样）及聊天记录截.jpg",
        asset_img_dir,
        "17_线上篆刻多组作品对比.jpg",
    )
    img_guhanyu_100 = copy_asset(
        PROOF_ROOT_DIR / "01_学生规划图/03_高三/241_一张“考前国美古汉语5节突击课程”的宣传图，列出了周一到周五的课程表及内容，强调价值100分.jpg",
        asset_img_dir,
        "18_国美古汉语5节突击100分.jpg",
    )
    img_xiaokao_plan = copy_asset(
        PROOF_ROOT_DIR / "01_学生规划图/03_高三/189_一张带有“进击校考小圈”标题的图文卡片，内容包含“线上特训实况”、“领篆刻任务”及备考规划文字.jpg",
        asset_img_dir,
        "19_进击校考小圈规划.jpg",
    )
    img_xiaokao_subjects = copy_asset(
        PROOF_ROOT_DIR / "02_上课讲评图/03_高三/371_2025校考集训海报，列出国美、央美等院校四体创作、篆刻、古汉语等备考科目.jpg",
        asset_img_dir,
        "20_国美央美校考备考科目.jpg",
    )
    img_plan_g2_excel = copy_asset(
        PROOF_ROOT_DIR / "01_学生规划图/02_高二/019_这是一张宣传海报，主体为“高二书法线上全程”学习规划。画面包含微信聊天截图与Excel表格预览，聊天中提及“吴让之小篆作品《庾慎之谢东宫责米.png",
        asset_img_dir,
        "21_高二线上全程规划表.png",
    )
    img_plan_g2_duxue = copy_asset(
        PROOF_ROOT_DIR / "01_学生规划图/02_高二/020_这是一张宣传海报，主体为“高二线上全程”书法辅导服务。画面包含微信聊天记录截图与文档资料预览，文字内容涉及“清篆基础”、“督学计划表”、“专.jpg",
        asset_img_dir,
        "22_高二定制规划与督学.jpg",
    )
    img_plan_doc_036 = copy_asset(
        PROOF_ROOT_DIR / "01_学生规划图/07_通用/036_海老师给学员“桐桐”制定的学习计划文档，包含每日基础任务、视频学习、书写练习及月度考核安排.png",
        asset_img_dir,
        "23_定制个人学习计划文档.png",
    )
    img_group_critique = copy_asset(
        DRAFT1_VIDEO_DIR / "11_专属学习群逐字讲评海报_红黄绿线标注示范.jpg",
        asset_img_dir,
        "24_专属学习群逐字讲评.jpg",
    )
    img_duxue_14 = copy_asset(
        DRAFT1_VIDEO_DIR / "14_专属督学海报_不止督促作业更关心练习状态.jpeg",
        asset_img_dir,
        "25_专属日常督学海报.jpeg",
    )
    img_parent_thanks = copy_asset(
        DRAFT1_VIDEO_DIR / "28_喜报海报_分数比预期高_家长致谢不走弯路.png",
        asset_img_dir,
        "26_家长致谢不走弯路喜报.png",
    )

    img_black_field = copy_asset(BLACK_FIELD_PATH, asset_img_dir, "top_shadow_black.png")

    # 4. Declare tracks in clean z-order:
    #    Track 0: Main video (carries segment-level main-only blur on chapter/data windows!)
    #    Track 1: Chapter & data dark backdrop (crisp black bars/veils — NEVER affected by Track 0 blur!)
    #    Track 2: Full-screen credential B-roll
    #    Track 3: Circular crisp speaker PiP (NEVER affected by Track 0 blur!)
    #    Track 4-6: Left/Center/Right PiP images
    #    Track 7: Top gradient shadow (black field + linear mask, auto-cut around B-roll & chapter dividers)
    #    Track 8-13: Text tracks
    script.append_track(TrackSpec(TrackType.video, name="主视频_1.3x粗剪"))
    script.append_track(TrackSpec(TrackType.video, name="章节与数据暗底_黑场"))
    script.append_track(TrackSpec(TrackType.video, name="全屏背书_Broll"))
    script.append_track(TrackSpec(TrackType.video, name="圆形画中画_海老师"))
    script.append_track(TrackSpec(TrackType.video, name="画中画_左"))
    script.append_track(TrackSpec(TrackType.video, name="画中画_中"))
    script.append_track(TrackSpec(TrackType.video, name="画中画_右"))
    script.append_track(TrackSpec(TrackType.video, name="顶部渐变阴影_黑场"))

    script.append_track(TrackSpec(TrackType.text, name="字幕_金陵体"))
    script.append_track(TrackSpec(TrackType.text, name="重点大字包装"))
    script.append_track(TrackSpec(TrackType.text, name="侧边原生文字_左"))
    script.append_track(TrackSpec(TrackType.text, name="侧边原生文字_右"))
    script.append_track(TrackSpec(TrackType.text, name="顶部常驻标题_上行"))
    script.append_track(TrackSpec(TrackType.text, name="顶部常驻标题_下行"))

    script.append_track(TrackSpec(TrackType.audio, name="BGM_古筝轻音乐"))
    script.append_track(TrackSpec(TrackType.audio, name="音效点缀"))

    # Helper to look up cue boundaries cleanly
    def cue_st(kw: str, fallback_s: float) -> int:
        hit = find_cue_range(cues, kw)
        return hit[0] if hit else sec_to_us(fallback_s)

    # Define the 3 chapter-divider windows (user v8 exact style: Track-0-only blur + crisp black bar + centered 25pt title)
    # and the 2 data-separation windows (Track-0-only blur + dark veil + circular crisp speaker PiP + clean data)
    chapter_windows: list[tuple[int, int, str]] = [
        (81_170_000, 83_670_000, "高一阶段\n文化+打底"),
        (93_530_000, 96_770_000, "高二阶段\n抢跑篆刻"),
        (119_330_000, 123_070_000, "高三阶段\n真题+冲文化"),
    ]
    data_sep_windows: list[tuple[int, int, float, float, float]] = [
        # (start_us, end_us, blur_pct, veil_alpha, speaker_y)
        (cue_st("浙江省490", 55.93), 65_500_000, 45.0, 0.42, 0.34),
        (103_900_000, 111_850_000, 42.0, 0.38, 0.36),
    ]
    blur_windows: list[tuple[int, int, float]] = [
        (st, ed, 50.0) for st, ed, _ in chapter_windows
    ] + [
        (st, ed, bp) for st, ed, bp, _, _ in data_sep_windows
    ]
    blur_boundaries = sorted(set(t for st, ed, _ in blur_windows for t in (st, ed)))

    def blur_strength_for(mid_us: int) -> float | None:
        for st, ed, bp in blur_windows:
            if st <= mid_us <= ed:
                return bp
        return None

    # 5. Stage 1 + 2: Add main rough-cut video track at 1.3x speed & +10 dB voice gain
    #    - Cleanly split clips at blur_boundaries so segment-level `模糊` (apply_target_type=0)
    #      starts/ends frame-accurately on Track 0 ONLY (ZERO blur bleed onto black bars or circular PiP!)
    #    - Opening 0-4.2s smooth push-in keyframe (1.00 -> 1.08)
    for clip in clips:
        c_st = clip.tl_start_us
        c_ed = clip.tl_start_us + clip.tl_dur_us
        cuts = [c_st] + [b for b in blur_boundaries if c_st + 40_000 < b < c_ed - 40_000] + [c_ed]
        for sub_st, sub_ed in zip(cuts, cuts[1:]):
            sub_dur = sub_ed - sub_st
            if sub_dur < 30_000:
                continue
            tl_off = sub_st - c_st
            src_off = round(tl_off * PLAYBACK_SPEED)
            src_sub_dur = round(sub_dur * PLAYBACK_SPEED)
            src_tr = Timerange(sec_to_us(clip.src_start) + src_off, src_sub_dur)
            tgt_tr = Timerange(sub_st, sub_dur)
            vseg = VideoSegment(
                raw_mat,
                tgt_tr,
                source_timerange=src_tr,
                speed=PLAYBACK_SPEED,
                volume=VOICE_VOLUME,
                clip_settings=ClipSettings(
                    scale_x=clip.scale,
                    scale_y=clip.scale,
                    transform_y=clip.transform_y,
                ),
            )
            if sub_st < 4_200_000 and sub_dur >= 400_000:
                p0 = min(1.0, sub_st / 4_200_000.0)
                p1 = min(1.0, sub_ed / 4_200_000.0)
                sc0 = round(1.00 + 0.08 * p0, 4)
                sc1 = round(1.00 + 0.08 * p1, 4)
                vseg.add_keyframe(KeyframeProperty.scale_x, 0, sc0)
                vseg.add_keyframe(KeyframeProperty.scale_x, sub_dur, sc1)
                vseg.add_keyframe(KeyframeProperty.scale_y, 0, sc0)
                vseg.add_keyframe(KeyframeProperty.scale_y, sub_dur, sc1)
            bp = blur_strength_for((sub_st + sub_ed) // 2)
            if bp is not None:
                vseg.add_effect(VideoSceneEffectType.模糊, params=[bp])
            script.add_segment(vseg, "主视频_1.3x粗剪")

    # Helper to add muted circular crisp speaker PiP clips on `圆形画中画_海老师` for any [win_st, win_ed]
    def add_circular_speaker_pip(win_st: int, win_ed: int, px: float, py: float, pscale: float) -> int:
        added = 0
        for clip in clips:
            ov_st = max(clip.tl_start_us, win_st)
            ov_ed = min(clip.tl_start_us + clip.tl_dur_us, win_ed)
            if ov_ed - ov_st < 80_000:
                continue
            tl_off_us = ov_st - clip.tl_start_us
            src_off_us = round(tl_off_us * PLAYBACK_SPEED)
            src_sub_dur = round((ov_ed - ov_st) * PLAYBACK_SPEED)
            src_tr = Timerange(sec_to_us(clip.src_start) + src_off_us, src_sub_dur)
            tgt_tr = Timerange(ov_st, ov_ed - ov_st)
            cseg = VideoSegment(
                raw_mat,
                tgt_tr,
                source_timerange=src_tr,
                speed=PLAYBACK_SPEED,
                volume=0.0,  # Muted — Track 0 carries +10 dB audio!
                clip_settings=ClipSettings(transform_x=px, transform_y=py, scale_x=pscale, scale_y=pscale),
            )
            script.add_segment(cseg, "圆形画中画_海老师")
            added += 1
        return added

    # 5a. Add crisp semi-transparent black bars (chapter dividers) & dark veils (data screens) on Track 1
    #     Because blur is segment-level on Track 0 ONLY, these bars stay 100% crisp and unblurred!
    black_mat = VideoMaterial(str(img_black_field), material_name="黑场")
    for ch_st, ch_ed, _ in chapter_windows:
        bar_seg = VideoSegment(
            black_mat,
            Timerange(ch_st, ch_ed - ch_st),
            # Exact user hand-tuned horizontal dark banner from v8 Track 8!
            clip_settings=ClipSettings(transform_x=0.0, transform_y=-0.069, scale_x=1.0, scale_y=0.827, alpha=0.50),
        )
        bar_seg.add_animation(IntroType.渐显, "0.25s")
        bar_seg.add_animation(OutroType.渐隐, "0.22s")
        script.add_segment(bar_seg, "章节与数据暗底_黑场")

    data_cpip_total = 0
    for ds_st, ds_ed, _, veil_alpha, sp_y in data_sep_windows:
        veil_seg = VideoSegment(
            black_mat,
            Timerange(ds_st, ds_ed - ds_st),
            # Full-frame subtle dark veil so yellow data pops cleanly off blurred background
            clip_settings=ClipSettings(transform_x=0.0, transform_y=0.0, scale_x=2.4, scale_y=2.4, alpha=veil_alpha),
        )
        veil_seg.add_animation(IntroType.渐显, "0.25s")
        veil_seg.add_animation(OutroType.渐隐, "0.25s")
        script.add_segment(veil_seg, "章节与数据暗底_黑场")
        # Separate clear circular speaker PiP cleanly below top title & above data!
        data_cpip_total += add_circular_speaker_pip(ds_st, ds_ed, px=0.0, py=sp_y, pscale=0.40)
    print(f"[chapter+data] added 3 crisp blurred-bg chapter dividers + 2 data-separated screens ({data_cpip_total} circular speaker clips)")

    # 5b. Full-screen credential B-roll + circular muted speaker PiP during "中国美术学院书法专业，从本科读到硕士一共七年"
    #     Uses user's exact v8 hand-tuned top-right circular PiP placement (x=0.523, y=0.580, scale=0.50, feather=0.173)!
    broll_hit_start = find_cue_range(cues, "中国美术学院")
    broll_hit_end = find_cue_range(cues, "一共七年")
    broll_window: tuple[int, int] | None = None
    if broll_hit_start and broll_hit_end and broll_hit_end[1] > broll_hit_start[0] + 1_500_000:
        b_st = broll_hit_start[0]
        b_ed = broll_hit_end[1]
        b_dur = b_ed - b_st
        broll_window = (b_st, b_ed)
        d1 = round(b_dur * 0.34)
        d2 = round(b_dur * 0.31)
        d3 = b_dur - d1 - d2
        broll_photos = [
            (img_haixi_609, b_st, d1, 1.04, 1.10, 0.02),
            (img_gm_diploma, b_st + d1, d2, 1.48, 1.56, 0.00),
            (img_gm_master, b_st + d1 + d2, d3, 1.15, 1.22, -0.02),
        ]
        for bimg, pst, pdur, sc0, sc1, by in broll_photos:
            bmat = VideoMaterial(str(bimg))
            bseg = VideoSegment(
                bmat,
                Timerange(pst, pdur),
                clip_settings=ClipSettings(transform_x=0.0, transform_y=by, scale_x=sc0, scale_y=sc0),
            )
            bseg.add_keyframe(KeyframeProperty.scale_x, 0, sc0)
            bseg.add_keyframe(KeyframeProperty.scale_x, pdur, sc1)
            bseg.add_keyframe(KeyframeProperty.scale_y, 0, sc0)
            bseg.add_keyframe(KeyframeProperty.scale_y, pdur, sc1)
            script.add_segment(bseg, "全屏背书_Broll")

        add_circular_speaker_pip(b_st, b_ed, px=0.523, py=0.580, pscale=0.50)
        print(f"[broll] added 3 full-screen 国美 credential photos + v8 top-right circular PiP ({b_st/1e6:.2f}s-{b_ed/1e6:.2f}s)")

    # 6. Add top-title dark gradient shadow layer (黑场 + 线性蒙版 100% 羽化) & top two-line title
    #    Smartly cut out around full-screen B-roll AND all 3 chapter dividers (matching user's v8 cutout!)
    cutout_windows: list[tuple[int, int]] = []
    if broll_window is not None:
        cutout_windows.append(broll_window)
    for ch_st, ch_ed, _ in chapter_windows:
        cutout_windows.append((ch_st, ch_ed))
    cutout_windows.sort()
    top_spans: list[tuple[int, int]] = []
    cur_t = 0
    for cw_st, cw_ed in cutout_windows:
        if cw_st > cur_t + 300_000:
            top_spans.append((cur_t, cw_st))
        cur_t = max(cur_t, cw_ed)
    if total_tl_us > cur_t + 300_000:
        top_spans.append((cur_t, total_tl_us))

    title_shadow = TextShadow(alpha=0.85, color=(0.0, 0.0, 0.0), diffuse=10.0, distance=5.0, angle=-45.0)
    for span_idx, (sp_st, sp_ed) in enumerate(top_spans):
        sp_dur = sp_ed - sp_st
        if sp_dur < 300_000:
            continue
        top_shadow_seg = VideoSegment(
            black_mat,
            Timerange(sp_st, sp_dur),
            clip_settings=ClipSettings(transform_x=0.0, transform_y=0.636, scale_x=1.0, scale_y=1.0, alpha=1.0),
        )
        script.add_segment(top_shadow_seg, "顶部渐变阴影_黑场")

        top_line1 = TextSegment(
            "书法生想上国美央美",
            Timerange(sp_st, sp_dur),
            font=FontType.清刻本悦,
            style=TextStyle(size=13.0, color=COLOR_WHITE, align=1, bold=True, letter_spacing=1),
            clip_settings=ClipSettings(transform_x=0.0, transform_y=0.840, scale_x=1.26, scale_y=1.26),
            border=None,
            shadow=title_shadow,
        )
        if span_idx == 0:
            top_line1.add_animation(TextIntro.向上弹入, "0.35s")
        script.add_segment(top_line1, "顶部常驻标题_上行")

        top_line2 = TextSegment(
            "高中三年怎么规划？",
            Timerange(sp_st, sp_dur),
            font=FontType.清刻本悦,
            style=TextStyle(size=10.5, color=COLOR_YELLOW, align=1, bold=False, letter_spacing=1),
            clip_settings=ClipSettings(transform_x=0.0, transform_y=0.670, scale_x=1.26, scale_y=1.26),
            border=None,
            shadow=title_shadow,
        )
        if span_idx == 0:
            top_line2.add_animation(TextIntro.向上弹入, "0.35s")
        script.add_segment(top_line2, "顶部常驻标题_下行")

    # 7 & 8. Add single-line subtitles (STRICTLY <= 10 chars!) + paired keyword-split highlights
    #        - Regular cue: 金陵体 size 13.5, y=-0.56, #FFFFFF, NO stroke, 85% shadow
    #        - Paired keyword-split cue (SOP):
    #            * Main track: <=10-char prefix at y=-0.49 (full sentence duration)
    #            * Emphasis track: trailing core keyword at y=-0.69 (#FFF29D / #FF619D, scaled up,
    #              enters when spoken and exits synchronized with main subtitle — ZERO duplication!)
    sub_style = TextStyle(
        size=13.5,
        color=COLOR_WHITE,
        align=1,
        auto_wrapping=True,
        max_line_width=0.90,
    )
    sub_clip_normal = ClipSettings(transform_x=0.0, transform_y=-0.56, scale_x=1.0, scale_y=1.0)
    sub_clip_paired = ClipSettings(transform_x=0.0, transform_y=-0.49, scale_x=1.0, scale_y=1.0)
    sub_shadow = TextShadow(alpha=0.85, color=(0.0, 0.0, 0.0), diffuse=10.0, distance=5.0, angle=-45.0)
    kw_shadow = TextShadow(alpha=0.88, color=(0.0, 0.0, 0.0), diffuse=10.0, distance=5.0, angle=-45.0)

    sfx_map = {
        "drop": sfx_drop,
        "dong": sfx_dong,
        "ding": sfx_ding,
        "whoosh": sfx_whoosh,
        "stamp": sfx_stamp,
        "page": sfx_page,
    }
    sfx_events: list[tuple[int, Path, float]] = []
    used_kw_rules: set[str] = set()
    last_kw_end = 0
    popup_count = 0
    sub_count = 0

    for st, ed, txt in cues:
        hit_kw = _match_keyword_split(txt)
        rule_key = f"{hit_kw[0]}|{hit_kw[1]}" if hit_kw is not None else ""
        if hit_kw is not None and rule_key not in used_kw_rules and (ed - st) >= 650_000:
            main_t, kw_t, kw_sz, kw_anim, sfx_k, sfx_v = hit_kw
            used_kw_rules.add(rule_key)
            # Main subtitle: <= 10-char prefix lifted gently to y=-0.49
            tseg = TextSegment(
                main_t,
                Timerange(st, ed - st),
                font=FontType.金陵体,
                style=sub_style,
                clip_settings=sub_clip_paired,
                border=None,
                shadow=sub_shadow,
            )
            script.add_segment(tseg, "字幕_金陵体")
            sub_count += 1

            # Paired keyword highlight right below at y=-0.69:
            # FontType.仓耳丰黑 + COLOR_YELLOW (#FFF29D) + direct font_size (18-21, scale=1.0)
            total_len = max(1, len(main_t) + len(kw_t))
            ratio = len(main_t) / total_len
            kw_st = st + int((ed - st) * ratio) - 80_000
            kw_st = max(st + 180_000, min(ed - 420_000, kw_st))
            if kw_st < last_kw_end + 80_000:
                kw_st = last_kw_end + 80_000
            kw_dur = ed - kw_st
            if kw_dur >= 350_000:
                kseg = TextSegment(
                    kw_t,
                    Timerange(kw_st, kw_dur),
                    font=FontType.仓耳丰黑,
                    style=TextStyle(size=kw_sz, color=COLOR_YELLOW, align=1, bold=False),
                    clip_settings=ClipSettings(transform_x=0.0, transform_y=-0.69, scale_x=1.0, scale_y=1.0),
                    border=None,
                    shadow=kw_shadow,
                )
                kseg.add_animation(kw_anim, "0.3s")
                script.add_segment(kseg, "重点大字包装")
                sfx_events.append((kw_st, sfx_map[sfx_k], sfx_v))
                last_kw_end = ed
                popup_count += 1
        else:
            tseg = TextSegment(
                txt,
                Timerange(st, ed - st),
                font=FontType.金陵体,
                style=sub_style,
                clip_settings=sub_clip_normal,
                border=None,
                shadow=sub_shadow,
            )
            script.add_segment(tseg, "字幕_金陵体")
            sub_count += 1

    print(f"[subtitles] placed {sub_count} single-line main cues (<=10 chars) + {popup_count} paired keyword highlights")

    # 9 & 9a. 100% Collision-Free Choreography of Real 交付知识库 PiPs + Native Animated Side Callouts
    #         IRON RULE: At any instant t, LEFT / CENTER / RIGHT zone may hold AT MOST ONE item
    #         (either a PiP image OR a native side text, NEVER both stacked on top of each other!).
    #         And all PiPs sit at y=+0.08..+0.14 with plenty of headroom above subtitles (y=-0.49/-0.56).
    # Scheduled real PiP items: (zone, track_name, img_path, x, y, scale, start_us, end_us, anim, sfx_or_None)
    pip_plan: list[tuple[str, str, Path, float, float, float, int, int, IntroType, Path | None]] = [
        # --- 黄金前3秒开场校门头 (0.30s-2.20s): 国美校门头 + 央美校门头（绝不与后文喜报/通知书重复！） ---
        ("LEFT",  "画中画_左", img_caa_gate,       -0.58, 0.08, 0.38, 300_000,   2_200_000, IntroType.向右滑动, sfx_whoosh),
        ("RIGHT", "画中画_右", img_cafa_gate,       0.58, 0.08, 0.38, 450_000,   2_200_000, IntroType.向左滑动, None),

        # --- 成果背书段 (18.7s-23.6s): 国美全国第二/喜报 + 央美打码录取通知书 -> 省统考第1/3/7 ---
        ("LEFT",   "画中画_左", img_gm_2nd,         -0.63, 0.08, 0.33, 18_700_000, 20_600_000, IntroType.向右滑动, sfx_whoosh),
        ("RIGHT",  "画中画_右", img_ym_notice,       0.63, 0.08, 0.33, 18_950_000, 20_600_000, IntroType.向左滑动, None),
        ("LEFT",   "画中画_左", img_rank1,          -0.64, 0.14, 0.30, 20_800_000, 23_600_000, IntroType.向上滑动, sfx_page),
        ("CENTER", "画中画_中", img_rank3,           0.00, 0.16, 0.28, 21_400_000, 23_600_000, IntroType.向上滑动, None),
        ("RIGHT",  "画中画_右", img_rank7,           0.64, 0.14, 0.30, 21_400_000, 23_600_000, IntroType.向上滑动, None),

        # --- 高一规划打底段 (83.8s-91.2s): 严格在「高一阶段」章节分段退场后切入，零重叠 ---
        ("LEFT",  "画中画_左", img_plan_g1,         -0.62, 0.08, 0.34, 83_850_000, 87_300_000, IntroType.向右滑动, sfx_page),
        ("RIGHT", "画中画_右", img_online_class,     0.62, 0.08, 0.34, 84_100_000, 87_300_000, IntroType.向左滑动, None),
        ("LEFT",  "画中画_左", img_1v1,             -0.62, 0.08, 0.35, 87_500_000, 91_200_000, IntroType.向右滑动, sfx_whoosh),
        ("RIGHT", "画中画_右", img_g1_lishu_prog,    0.62, 0.08, 0.34, 87_800_000, 91_200_000, IntroType.向左滑动, None),

        # --- 高二篆刻抢跑段 (97.2s-103.7s): 严格在「高二阶段」章节分段退场后切入，零重叠 ---
        ("LEFT",  "画中画_左", img_g2_zhuanke_20d,  -0.61, 0.08, 0.36, cue_st("尽早接触", 97.21),   101_000_000, IntroType.向右滑动, sfx_whoosh),
        ("RIGHT", "画中画_右", img_zk_compare_1002,  0.61, 0.08, 0.36, cue_st("大半的分数", 101.23), 103_700_000, IntroType.向左滑动, sfx_page),

        # --- 国美 vs 央美科目分值数据分离段 (103.9s-111.85s): 上方圆形清晰人物 + 左文右图错位，零叠字 ---
        ("RIGHT", "画中画_右", img_guhanyu_100,      0.54, -0.10, 0.34, 105_500_000, 107_850_000, IntroType.向左滑动, sfx_drop),
        ("RIGHT", "画中画_右", img_zk_compare_1007,  0.54, -0.10, 0.34, 108_100_000, 111_850_000, IntroType.向左滑动, sfx_page),
        # 补课提醒段: 左/右无文字, 展示央美篆刻92分全国最高喜报 (112.2s-116.5s)
        ("LEFT",  "画中画_左", img_ym_zhuanke,      -0.62, 0.08, 0.35, 112_200_000, 116_500_000, IntroType.向右滑动, sfx_drop),

        # --- 高三冲刺与真题段 (128.1s-137.0s): 严格在「高三阶段」章节分段退场后切入 ---
        ("LEFT",  "画中画_左", img_xiaokao_plan,    -0.62, 0.08, 0.35, cue_st("校考之前", 128.07), 132_000_000, IntroType.向右滑动, sfx_whoosh),
        ("RIGHT", "画中画_右", img_xiaokao_subjects, 0.62, 0.08, 0.35, 132_400_000,                137_000_000, IntroType.向左滑动, sfx_page),

        # --- 结尾服务价值闭环 (147.6s-163.04s): 三组成对稳步展示，每组4~5.5秒，绝不闪切、不撞字幕 ---
        ("LEFT",  "画中画_左", img_plan_g2_excel,   -0.62, 0.10, 0.34, 147_600_000, 151_600_000, IntroType.向右滑动, sfx_page),
        ("RIGHT", "画中画_右", img_plan_doc_036,     0.62, 0.10, 0.34, 147_900_000, 151_600_000, IntroType.向左滑动, None),
        ("LEFT",  "画中画_左", img_group_critique,  -0.62, 0.10, 0.34, 152_000_000, 156_600_000, IntroType.向右滑动, sfx_whoosh),
        ("RIGHT", "画中画_右", img_parent_thanks,    0.62, 0.10, 0.34, 152_300_000, 156_600_000, IntroType.向左滑动, None),
        ("LEFT",  "画中画_左", img_plan_g2_duxue,   -0.62, 0.10, 0.34, 157_200_000, total_tl_us, IntroType.向右滑动, sfx_page),
        ("RIGHT", "画中画_右", img_duxue_14,         0.62, 0.10, 0.34, 157_500_000, total_tl_us, IntroType.向左滑动, None),
    ]

    # Scheduled native JianYing animated data callouts + 3 user-tuned centered 25pt chapter dividers!
    # Format: (zone, track_name, label, x, y, font_size, start_us, end_us, anim)
    side_text_plan: list[tuple[str, str, str, float, float, float, int, int, TextIntro]] = [
        # 数据分离段 #1 — 南北各省本科线对比 (55.9s-65.5s): 背景虚化压暗 + 上方圆形清晰人物 + 下方左右大字数据！
        ("LEFT",   "侧边原生文字_左", "高分省\n浙 490\n苏 480\n豫 460\n鲁 440", -0.50, -0.10, 15.5, cue_st("浙江省490", 55.93), 65_500_000, TextIntro.打字机_I),
        ("RIGHT",  "侧边原生文字_右", "捡漏省\n黑 380\n吉 340\n内蒙 400",        0.50, -0.10, 15.5, cue_st("黑龙江380", 61.90), 65_500_000, TextIntro.打字机_I),
        # 3 处居中大字章节分段 (完全复刻用户 v8 手调: 25pt 居中 y=-0.04 + 仅主轨模糊 + 锐利半透明黑场衬底条!)
        ("CENTER", "侧边原生文字_右", "高一阶段\n文化+打底",                       0.00, -0.04, 25.0, 81_170_000,  83_670_000, TextIntro.向上弹入),
        ("CENTER", "侧边原生文字_右", "高二阶段\n抢跑篆刻",                       0.00, -0.04, 25.0, 93_530_000,  96_770_000, TextIntro.向上弹入),
        # 数据分离段 #2 — 国美 vs 央美科目分值 (103.9s-111.85s): 上方圆形清晰人物 + 左文右图错位，零重叠！
        ("LEFT",   "侧边原生文字_左", "国美校考\n书法 100\n篆刻 100\n古汉语 100", -0.50, -0.10, 15.0, 103_900_000, 107_850_000, TextIntro.打字机_I),
        ("LEFT",   "侧边原生文字_左", "央美校考\n书法 100\n篆刻 100",             -0.50, -0.10, 15.5, 108_100_000, 111_850_000, TextIntro.向上弹入),
        # 章节分段 #3
        ("CENTER", "侧边原生文字_右", "高三阶段\n真题+冲文化",                     0.00, -0.04, 25.0, 119_330_000, 123_070_000, TextIntro.向上弹入),
    ]

    # Built-in 2D space-time collision gate: fail loudly if ANY zone has overlapping PiP/side-text!
    zone_items: dict[str, list[tuple[int, int, str]]] = {"LEFT": [], "CENTER": [], "RIGHT": []}
    for z, _, p, _, _, _, st, ed, _, _ in pip_plan:
        assert ed - st >= 1_400_000, f"Flash-cut PiP <1.4s: {p.name} ({(ed-st)/1e6:.2f}s)"
        zone_items[z].append((st, ed, f"PiP:{p.name}"))
    for z, _, lbl, _, _, _, st, ed, _ in side_text_plan:
        assert ed - st >= 1_400_000, f"Flash-cut side text <1.4s: {lbl}"
        zone_items[z].append((st, ed, f"TEXT:{lbl.splitlines()[0]}"))
    for z, lst in zone_items.items():
        lst.sort(key=lambda x: x[0])
        for (a0, a1, an), (b0, b1, bn) in zip(lst, lst[1:]):
            assert b0 >= a1, f"ZONE COLLISION in {z}: {an}[{a0/1e6:.2f}-{a1/1e6:.2f}] vs {bn}[{b0/1e6:.2f}-{b1/1e6:.2f}]"

    pip_count = 0
    for z, tname, img_path, px, py, pscale, st, ed, anim, sfx_p in pip_plan:
        dur_us = min(ed, total_tl_us) - st
        if dur_us < 1_000_000:
            continue
        vmat = VideoMaterial(str(img_path))
        pseg = VideoSegment(
            vmat,
            Timerange(st, dur_us),
            clip_settings=ClipSettings(transform_x=px, transform_y=py, scale_x=pscale, scale_y=pscale),
        )
        pseg.add_animation(anim, "0.32s")
        pseg.add_animation(OutroType.渐隐, "0.22s")
        script.add_segment(pseg, tname)
        if sfx_p is not None:
            sfx_events.append((st, sfx_p, 0.40))
        pip_count += 1
    print(f"[pip] added {pip_count} collision-free real 交付知识库 PiPs")

    side_added = 0
    for z, tname, label, sx, sy, ssz, st, ed, anim in side_text_plan:
        dur_us = min(ed, total_tl_us) - st
        if dur_us < 1_000_000:
            continue
        sseg = TextSegment(
            label,
            Timerange(st, dur_us),
            font=FontType.仓耳丰黑,
            style=TextStyle(size=ssz, color=COLOR_YELLOW, align=1, bold=False, line_spacing=8),
            clip_settings=ClipSettings(transform_x=sx, transform_y=sy, scale_x=1.0, scale_y=1.0),
            border=None,
            shadow=TextShadow(alpha=0.85, color=(0.0, 0.0, 0.0), diffuse=10.0, distance=5.0, angle=-45.0),
        )
        sseg.add_animation(anim, "0.35s")
        script.add_segment(sseg, tname)
        side_added += 1
    print(f"[side-text] added {side_added} collision-free native JianYing animated side callouts")

    # 9b. Compute 3 restrained TL0-style `暗角` focus moments (no gimmicky AI effects!)
    vignette_ranges: list[tuple[int, int]] = []
    for vkw, extra_dur in [
        ("折在了文化分上", 1_600_000),
        ("悬殊100分", 1_500_000),
        ("双线并进", 1_600_000),
    ]:
        vhit = find_cue_range(cues, vkw)
        if vhit:
            vst = max(0, vhit[0] - 100_000)
            vdur = min(extra_dur, total_tl_us - vst)
            if vdur >= 600_000:
                vignette_ranges.append((vst, vdur))

    # 10. Add looped BGM track (volume = 0.3162 ≈ -10 dB, matching Draft #1!)
    bgm_mat = AudioMaterial(str(bgm_path))
    bgm_cursor = 0
    bgm_segs = 0
    while bgm_cursor < total_tl_us:
        rem = total_tl_us - bgm_cursor
        seg_dur = min(bgm_mat.duration, rem)
        aseg = AudioSegment(
            bgm_mat,
            Timerange(bgm_cursor, seg_dur),
            source_timerange=Timerange(0, seg_dur),
            volume=0.3162,
        )
        if bgm_cursor == 0:
            aseg.add_fade("0.8s", "0s")
        if bgm_cursor + seg_dur >= total_tl_us:
            aseg.add_fade("0s", "2.0s")
        script.add_segment(aseg, "BGM_古筝轻音乐")
        bgm_cursor += seg_dur
        bgm_segs += 1
    print(f"[bgm] added {bgm_segs} looped BGM segments (vol=0.3162)")

    # 11. Add sparse SFX accents (deduplicated / non-overlapping on single SFX track)
    sfx_mat_cache: dict[Path, AudioMaterial] = {}
    sfx_last_end = 0
    sfx_added = 0
    for st, spath, svol in sorted(sfx_events, key=lambda x: x[0]):
        if st < sfx_last_end + 150_000:
            continue
        amat = sfx_mat_cache.get(spath)
        if amat is None:
            amat = AudioMaterial(str(spath))
            sfx_mat_cache[spath] = amat
        dur = min(amat.duration, 1_100_000, total_tl_us - st)
        if dur < 150_000:
            continue
        aseg = AudioSegment(amat, Timerange(st, dur), source_timerange=Timerange(0, dur), volume=svol)
        script.add_segment(aseg, "音效点缀")
        sfx_last_end = st + dur
        sfx_added += 1
    print(f"[sfx] added {sfx_added} sparse SFX accents")

    # 12. Save draft + inject beauty preset, masks, restrained vignettes, verified local fonts & meta info
    script.save()
    patch_draft_postprocess(draft_dir, NEW_DRAFT_NAME, total_tl_us, vignette_ranges=vignette_ranges)
    print(f"[done] JianYing draft saved to: {draft_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
