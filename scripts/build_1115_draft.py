#!/usr/bin/env python3
"""
Build a complete rough-cut + packaged JianYing 11.8 plaintext draft for
`1115刚上高中书法生转变` using pyJianYingDraft.

Applies 100% of the finalized v13 SOP (`海晞口播剪辑与包装标准模板.md`):
  1. Stage 1 — Pre-cut base prep applied across all main talking-head clips (+ circular PiP clips):
     1.3x playback speed + +10 dB voice gain (volume=last_nonzero_volume=3.162278) + 17-item Haixi beauty preset.
  2. Stage 2 — Non-destructive rough cut (removes all verified retakes, stumbles, hiss, and long dead-air silences).
  3. Stage 3 — Manual-edit-grade packaging:
     - Subtitles: FontType.金陵体, size 13.5, #FFFFFF, NO border/stroke + black shadow 85%,
       strictly <= 10 visible chars per regular cue; drops locally to y=-0.729 ONLY inside data-separation screens.
     - Paired emphasis keywords: FontType.仓耳丰黑 + #FFF29D, direct size 18.5-21.0 (scale=1.0),
       varied non-repetitive TextIntro animations, paired below <=10-char main subtitle (or relayed at y=-0.708 in data screens).
     - Top two-line persistent title (`清刻本悦`, Line 1 bold #FFFFFF + Line 2 normal #FFF29D) +
       top gradient dark shadow (`黑场` + linear mask feather=1.0), auto-cut around B-roll, chapter dividers & data screens.
     - Full-screen personal credential B-roll (国美本硕) + muted soft-feathered top-right circular speaker PiP
       (feather=0.04, enable_mask_stroke=False, independent material_id).
     - 4 crisp chapter dividers (Track-0-only segment blur 50% + crisp Track-1 semi-transparent black banner + 25pt title).
     - 4 data/viewpoint separation screens (Track-0-only blur 42-45% + dark veil + top-center crisp white-stroked circular
       speaker y=+0.597, feather=0.0, independent material_id, enable_mask_stroke=True + two-tone white-header/yellow-body lists).
     - 100% visually-verified real `06_交付知识库` topic-matched PiPs with hard 2D zone collision & >=1.4s duration gates.
     - 3 restrained `暗角` focus accents + looped zither BGM (-15 dB, 0.1778) + sparse SFX (0 dB).
     - 100% self-contained draft (`assets/` copied locally) + verified local JianYing `.ttf` cache paths.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
NEW_DRAFT_NAME = "1115刚上高中书法生转变_AI粗剪包装_v1"

RAW_VIDEO_PATH = Path(r"D:\Software\剪映\AI素材库\1115刚上高中书法生转变_原片.mp4")
BLACK_FIELD_PATH = Path(r"D:\Software\剪映\AI素材库\黑场_1920x1080.png")

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
MASK_STROKE_CACHE_PATH = (
    "C:/Users/jiely/AppData/Local/JianyingPro/User Data/Cache/artistEffect/"
    "7563928939278765348/290341ad03f260b3cd502bf88a55c5eb"
)
MASK_STROKE_RESOURCE_ID = "7563928939278765348"
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
    r"\scratch\asr_1115_out\逐字稿\IOS_ALBUM@8BB7B526-1C44-41FE-9225-87A6FB0C7129_L0_001@1794750522000.json"
)
SILENCE_LOG_PATH = Path(
    r"C:\Users\jiely\.gemini\antigravity\brain\66a1cadc-f2f0-47fd-890f-b411ed01293a"
    r"\scratch\silence_1115.log"
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

# Verified local font cache paths on this PC
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

# STRICT 2-COLOR RULE: ONLY pure white & Haixi light yellow (#FFF29D)
COLOR_WHITE = (1.0, 1.0, 1.0)
COLOR_YELLOW = (1.0, 0.949, 0.616)  # #FFF29D

# Two-tone data-screen header labels (first line #FFFFFF, body lines #FFF29D)
TWO_TONE_HEADERS = {
    "以前录取",
    "现在录取",
    "应试书法",
    "兴趣班书法",
    "平时周末",
    "假期提分",
}

# Confirmed retakes / stumbles / dead air to remove (source video seconds, verified by ear)
EXPLICIT_DELETE_RANGES: list[tuple[float, float, str]] = [
    (0.00, 5.28, "片头准备静音"),
    (48.10, 48.72, "起句口误：书法课"),
    (203.20, 209.75, "重录前版：我很理解他们自身也有教学压力"),
    (245.90, 250.20, "重录前版：那这些掉队下来的小孩怎么办呢"),
    (268.00, 268.50, "独立吸气杂音：嘶"),
    (407.80, 410.22, "口误重录：以为到了高三继续临摹帖"),
    (476.40, 478.38, "卡壳重录：那么这五分啊，在书"),
    (484.20, 485.55, "口误重录半句：拉下一百[断]"),
    (570.65, 573.08, "卡壳重录：才不会方才不会荒"),
    (596.10, 601.05, "重录前版：把孩子好好的底子给毁了"),
    (626.20, 632.20, "重录前版：为最终孩子的书法录取"),
    (641.25, 642.41, "片尾静音"),
]

# Verified ASR homophone / typo corrections (display text only)
TEXT_CORRECTIONS: list[tuple[str, str]] = [
    ("两头的晕头转向", "两头都晕头转向"),
    ("书法课，书法高考", "书法高考"),
    ("这些年代，团队在线上", "这些年带团队在线上"),
    ("相今天数", "像听天书"),
    ("签在全国各省的书法统考", "现在全国各省的书法统考"),
    ("甚至从985/211", "甚至冲985/211"),
    ("分区一个更低层次的版", "分去一个更低层次的班"),
    ("只能烙在家长您的肩膀上了", "只能落在家长您的肩膀上了"),
    ("甫高深了", "普高生了"),
    ("初中念过书法", "初中练过书法"),
    ("硬式书法", "应试书法"),
    ("对碑体理解的精准度", "对碑帖理解的精准度"),
    ("以前在书法性缺班呢，可能就是老是哄着", "以前在书法兴趣班呢，可能就是老师哄着"),
    ("拿下100来名", "拉下100来名"),
    ("映式体系", "应试体系"),
    ("十一年", "11年"),
    ("这五分啊", "这5分啊"),
    ("一百名", "100名"),
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
    text = (
        raw.decode("utf-16", errors="ignore")
        if raw[:2] in (b"\xff\xfe", b"\xfe\xff")
        else raw.decode("utf-8", errors="ignore")
    )
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


def is_deleted_source(a: float, b: float) -> bool:
    mid = (a + b) / 2.0
    for da, db, _ in EXPLICIT_DELETE_RANGES:
        if da <= mid <= db:
            return True
    return False


def compute_kept_clips(
    sentences: list[dict[str, Any]],
    silences: list[tuple[float, float]],
    video_duration_s: float,
) -> list[KeptClip]:
    """Build tight, breath-trimmed, retake-free video clips with safe speech padding."""
    first_speech = max(0.0, sentences[0]["start"] / 1000.0 - 0.12)
    last_speech = min(video_duration_s - 0.05, sentences[-1]["end"] / 1000.0 + 0.35)

    cut_ranges: list[tuple[float, float]] = [(a, b) for a, b, _ in EXPLICIT_DELETE_RANGES]

    for sa, sb in silences:
        dur = sb - sa
        if dur >= 0.30:
            trim_start = sa + 0.08
            trim_end = sb - 0.06
            if trim_end - trim_start >= 0.14:
                cut_ranges.append((trim_start, trim_end))

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

    speech_spans = [(s["start"] / 1000.0, s["end"] / 1000.0) for s in sentences]

    def has_speech(a: float, b: float) -> bool:
        for sa, sb in speech_spans:
            if min(b, sb) - max(a, sa) >= 0.08:
                return True
        return False

    cleaned = [(a, b) for a, b in raw_kept if (b - a) >= 0.14 and has_speech(a, b)]
    for s in sentences:
        sa, sb = s["start"] / 1000.0, s["end"] / 1000.0
        if is_deleted_source(sa, sb):
            continue
        if not any(min(b, sb) - max(a, sa) >= 0.05 for a, b in cleaned):
            cleaned.append((max(first_speech, sa - 0.06), min(last_speech, sb + 0.08)))
    cleaned = merge_intervals(cleaned, gap=0.10)

    # Subtle 1.00 / 1.06 chapter punch-in transitions (keeps top headroom intact)
    chapter_punch_starts = [66.0, 100.0, 142.0, 187.0, 265.0, 306.0, 398.0, 491.0, 583.0]
    clips: list[KeptClip] = []
    cursor_us = 0
    for a, b in cleaned:
        src_start_us = sec_to_us(a)
        src_dur_us = sec_to_us(b - a)
        if src_dur_us < 100_000:
            continue
        tl_dur_us = round(src_dur_us / PLAYBACK_SPEED)
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
    for c in clips:
        if c.src_start <= src_s <= c.src_end:
            offset_us = round(((src_s - c.src_start) * 1_000_000.0) / PLAYBACK_SPEED)
            return c.tl_start_us + min(offset_us, c.tl_dur_us)
    best: tuple[float, int] | None = None
    for c in clips:
        if prefer_end:
            dist = abs(src_s - c.src_end)
            cand = c.tl_start_us + c.tl_dur_us
        else:
            dist = abs(src_s - c.src_start)
            cand = c.tl_start_us
        if dist <= 0.35 and (best is None or dist < best[0]):
            best = (dist, cand)
    return best[1] if best is not None else None


def clean_subtitle_text(text: str) -> str:
    s = text.strip()
    for wrong, right in TEXT_CORRECTIONS:
        s = s.replace(wrong, right)
    s = re.sub(r"^[，。、！？；：,.!?;:\s]+", "", s)
    s = re.sub(r"[，。、；：,.;:\s]+$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _smart_chinese_split(chunk: str, max_chars: int) -> list[str]:
    chunk = chunk.strip()
    if len(chunk) <= max_chars:
        return [chunk] if chunk else []
    break_before = [
        "以及", "而且", "但是", "或者", "并且", "就是", "其实", "最后", "同时",
        "然后", "直接", "能够", "已经", "如果", "因为", "所以", "比如", "甚至",
        "不要", "可以", "应该", "还是", "全国", "各省", "书法", "文化", "专业",
        "高一", "高二", "高三", "高中", "初中", "线上", "线下", "和", "跟", "给", "把", "去", "在", "到",
    ]
    break_after = ["的", "了", "啊", "呢", "吧", "上", "中", "里", "后", "前", "是", "有"]
    mid = len(chunk) // 2
    min_left = max(2, len(chunk) - max_chars)
    max_left = min(len(chunk) - 2, max_chars)
    best_idx = None
    best_dist = 999

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


# Paired emphasis-split rules (SOP: main <= 10 chars + yellow 仓耳丰黑 keyword below, ZERO duplication!)
# Varied non-repetitive TextIntro animations across the timeline!
# Format: (match_text, main_text_le_10, kw_text, kw_font_size, kw_anim, sfx_name, sfx_vol)
KEYWORD_SPLIT_RULES: list[tuple[str, str, str, float, TextIntro, str, float]] = [
    ("一定要做好四个心理准备", "一定要做好", "四个心理准备", 20.0, TextIntro.向上弹入, "ding", 1.0),
    ("两头都晕头转向", "两头都", "晕头转向", 21.0, TextIntro.缩小, "dong", 1.0),
    ("书法高考这条路我走了11年", "书法高考这条路", "我走了11年", 20.0, TextIntro.开幕, "ding", 1.0),
    ("给全国近300个家庭", "给全国", "近300个家庭", 20.0, TextIntro.放大, "drop", 1.0),
    ("文化和专业两条路都走稳", "文化和专业", "两条路都走稳", 19.5, TextIntro.汇聚, "ding", 1.0),
    ("可能刚进高中就给他当头一棒", "可能刚进高中就给他", "当头一棒", 21.0, TextIntro.缩小, "stamp", 1.0),
    ("文化差点也没关系", "文化差点", "也没关系", 20.5, TextIntro.向下露出, "dong", 1.0),
    ("大部分录取都是专业文化五五开", "大部分录取都是", "专业文化五五开", 19.0, TextIntro.左移弹动, "ding", 1.0),
    ("因为这可能是和他们的职称绩效挂钩的", "这可能和他们的", "职称绩效挂钩", 19.5, TextIntro.开幕, "drop", 1.0),
    ("更考验小孩的独立性了", "更考验小孩的", "独立性了", 21.0, TextIntro.放大, "ding", 1.0),
    ("这下连随大流的机会都没有了", "这下连随大流的机会", "都没有了", 20.5, TextIntro.缩小, "dong", 1.0),
    ("只能落在家长您的肩膀上了", "只能落在家长您的", "肩膀上了", 21.0, TextIntro.向下露出, "stamp", 1.0),
    ("考试内容 录取方式都天差地别", "考试内容 录取方式", "都天差地别", 20.0, TextIntro.汇聚, "ding", 1.0),
    ("和高考的应试书法完全是两码事", "和高考的应试书法", "完全是两码事", 19.5, TextIntro.缩小, "stamp", 1.0),
    ("都要扣5分", "都要", "扣5分!", 21.0, TextIntro.放大, "stamp", 1.0),
    ("就能把您家小孩的名次拉下100来名", "就能把您家小孩的名次", "拉下100来名!", 19.5, TextIntro.缩小, "stamp", 1.25),
    ("时间真的就是挤出来的", "时间真的就是", "挤出来的", 21.0, TextIntro.左移弹动, "ding", 1.0),
    ("才不会荒废高中的宝贵时间", "才不会荒废高中的", "宝贵时间", 20.5, TextIntro.汇聚, "ding", 1.0),
    ("让专业跟文化都能够两手抓", "让专业跟文化都能够", "两手抓", 21.0, TextIntro.向上弹入, "ding", 1.0),
    ("那么可以留下线上集训", "那么可以留下", "线上集训", 20.5, TextIntro.向上弹入, "ding", 1.0),
]


def _match_keyword_split(text: str) -> tuple[str, str, float, TextIntro, str, float] | None:
    norm = re.sub(r"\s+", " ", text).strip()
    norm_compact = norm.replace(" ", "")
    for pat, main_t, kw_t, kw_sz, anim, sfx_k, sfx_v in KEYWORD_SPLIT_RULES:
        pat_compact = pat.replace(" ", "")
        # Strict near-exact match so extra clauses are NEVER swallowed!
        if norm_compact == pat_compact or (
            pat_compact in norm_compact and abs(len(norm_compact) - len(pat_compact)) <= 2
        ):
            return (main_t, kw_t, kw_sz, anim, sfx_k, sfx_v)
    return None


def split_long_cue(text: str, start_us: int, end_us: int, max_chars: int = 10) -> list[tuple[int, int, str]]:
    dur = end_us - start_us
    clean_sp = re.sub(r"[，。、；：,]+", " ", text).strip()
    if _match_keyword_split(clean_sp) is not None:
        return [(start_us, end_us, clean_sp)]
    if len(clean_sp) <= max_chars:
        return [(start_us, end_us, clean_sp)]

    parts = [p.strip() for p in re.split(r"[，。！？、；：,]", text) if p.strip()]
    merged: list[str] = []
    for part in parts:
        if merged and len(merged[-1]) + 1 + len(part) <= max_chars:
            merged[-1] = merged[-1] + " " + part
        elif merged and len(part) <= 2 and len(merged[-1]) + len(part) <= max_chars:
            merged[-1] = merged[-1] + part
        else:
            merged.append(part)

    final_parts: list[str] = []
    for chunk in merged:
        if len(chunk) <= max_chars or _match_keyword_split(chunk) is not None:
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
    """Convert ASR sentences into crisp, non-overlapping 1.3x timeline subtitle cues."""
    raw_cues: list[tuple[int, int, str, bool]] = []

    for idx, sent in enumerate(sentences):
        sa = sent["start"] / 1000.0
        sb = sent["end"] / 1000.0
        txt = str(sent.get("sentence", ""))

        # Surgical boundary overrides matching explicit partial-sentence cuts
        if idx == 8:
            sa = 48.72
            txt = "书法高考这条路我走了11年"
        elif idx == 82:
            # Merged cleanly into idx 83 ("这当然要区别于")
            continue
        elif idx == 83:
            sa = 358.82
            txt = "这当然要区别于"
        elif idx == 120:
            sb = 484.18
            txt = "就能把您家小孩的名次"
        elif idx == 144:
            sb = 570.62
            txt = "这样规划合理"
        elif idx == 18:
            txt = "第一个准备呢，就是小孩"
        elif idx == 19:
            txt = "的文化课一上高一就会上强度"

        if is_deleted_source(sa, sb):
            continue

        overlapping_clips = [c for c in clips if min(sb, c.src_end) - max(sa, c.src_start) >= 0.04]
        if not overlapping_clips:
            continue

        ends_sentence = txt.strip().endswith(("。", "！", "？"))
        clean_txt = clean_subtitle_text(txt)
        if not clean_txt:
            continue

        t0 = map_src_to_tl_us(max(sa, overlapping_clips[0].src_start), clips, prefer_end=False)
        t1 = map_src_to_tl_us(min(sb, overlapping_clips[-1].src_end), clips, prefer_end=True)
        if t0 is None or t1 is None or t1 - t0 < 80_000:
            continue

        # Custom natural-phrase splits (zero mid-word breaks, zero dropped chars!)
        custom_splits: dict[str, list[str]] = {
            "给全国近300个家庭做书法艺考规划": ["给全国近300个家庭", "做书法艺考规划"],
            "把孩子高中文化和专业两条路都走稳": ["把孩子高中", "文化和专业两条路都走稳"],
            "刚初三升高一，并且打算走书法艺考的家长": ["刚初三升高一", "并且打算走", "书法艺考的家长"],
            "的文化课一上高一就会上强度": ["的文化课", "一上高一就会上强度"],
            "书法是多么极其小众的专业": ["书法是多么", "极其小众的专业"],
            "小孩书法学习规划的重担": ["小孩书法学习", "规划的重担"],
            "您既然已经帮孩子选择了走书法专业这条路": ["您既然已经", "帮孩子选择了", "走书法专业这条路"],
            "他们就是通过纯文化去考大学的呀": ["他们就是通过", "纯文化去考大学的呀"],
            "必须把它当做，就像高中文化课里一门主科一样": ["必须把它当做", "就像高中文化课里", "一门主科一样"],
            "小长假也可以跟着线上的专业老师做书法考试的真题训练": ["小长假也可以跟着", "线上的专业老师做", "书法考试的真题训练"],
            "繁体字、篆字像背英语单词一样": ["繁体字 篆字", "像背英语单词一样"],
            "我今天急着把这些对高一书法生家长的话录下来": ["我今天急着把这些", "对高一书法生家长的", "话录下来"],
        }
        if clean_txt in custom_splits:
            parts_c = custom_splits[clean_txt]
            tot_c = max(1, sum(len(p) for p in parts_c))
            cur_c = t0
            for idx_c, p_c in enumerate(parts_c):
                nxt_c = t1 if idx_c == len(parts_c) - 1 else min(t1 - 100_000, cur_c + max(180_000, round((t1 - t0) * len(p_c) / tot_c)))
                raw_cues.append((cur_c, nxt_c, p_c, ends_sentence and idx_c == len(parts_c) - 1))
                cur_c = nxt_c
            continue

        sub_parts = split_long_cue(clean_txt, t0, t1, max_chars=10)
        for idx_p, (pst, ped, ptxt) in enumerate(sub_parts):
            raw_cues.append((pst, ped, ptxt, ends_sentence and idx_p == len(sub_parts) - 1))

    # Clean targeted merges so no tiny orphaned fragments remain (while staying <= 10 chars or matching a keyword rule)
    merged_cues: list[tuple[int, int, str, bool]] = []
    for st, ed, txt, ends_s in sorted(raw_cues, key=lambda x: x[0]):
        if merged_cues:
            pst, ped, ptxt, p_ends = merged_cues[-1]
            if st < ped:
                st = ped
            if ed <= st + 60_000:
                continue

            # Explicit natural joins across ASR pause splits
            if ptxt == "就是小孩" and txt.startswith("的文化课"):
                merged_cues[-1] = (pst, ed, "就是小孩的文化课", False)
                continue
            if ptxt.endswith("高一孩子") and txt == "验证":
                merged_cues[-1] = (pst, ed, ptxt + "验证", True)
                continue
            if ptxt == "就能把您家小孩的名次" and txt == "拉下100来名":
                merged_cues[-1] = (pst, ed, "就能把您家小孩的名次拉下100来名", True)
                continue
            if ptxt == "这" and txt.startswith("当然要区别于"):
                merged_cues[-1] = (pst, ed, "这" + txt, ends_s)
                continue
            if ptxt == "所以" and txt == "一旦选择了这条路":
                merged_cues[-1] = (pst, ed, "所以一旦选择了这条路", ends_s)
                continue
            if ptxt == "甚至" and len(txt) <= 8:
                merged_cues[-1] = (pst, ed, "甚至" + txt, ends_s)
                continue
            if ptxt == "他到了" and len(txt) <= 7:
                merged_cues[-1] = (pst, ed, "他到了" + txt, ends_s)
                continue
            if ptxt == "一门主科一样" and txt == "去对待":
                merged_cues[-1] = (pst, ed, "一门主科一样去对待", True)
                continue
            if ptxt == "读完了" and txt == "国美书法专业的本硕":
                # Keep separated cleanly (<= 10 chars each)
                merged_cues.append((st, ed, txt, ends_s))
                continue

            if (
                not p_ends
                and _match_keyword_split(ptxt) is None
                and _match_keyword_split(txt) is None
                and (st - ped) <= 450_000
            ):
                if len(ptxt) <= 3 and len(ptxt) + len(txt) <= 10:
                    merged_cues[-1] = (pst, ed, ptxt + txt, ends_s)
                    continue
                if len(txt) <= 3 and len(ptxt) + len(txt) <= 10:
                    merged_cues[-1] = (pst, ed, ptxt + txt, ends_s)
                    continue

        merged_cues.append((st, ed, txt, ends_s))

    # Handle "的文化课一上高一就会上强度" split cleanly when preceded by "第一个准备呢" + "就是小孩"
    polished: list[tuple[int, int, str]] = []
    i = 0
    while i < len(merged_cues):
        st, ed, txt, _ = merged_cues[i]
        if (
            txt == "就是小孩"
            and i + 1 < len(merged_cues)
            and merged_cues[i + 1][2].startswith("的文化课")
        ):
            nxt_st, nxt_ed, nxt_txt, _ = merged_cues[i + 1]
            rem = nxt_txt[4:].strip()
            if rem:
                mid = nxt_st + round((nxt_ed - nxt_st) * 4 / max(5, len(nxt_txt)))
                polished.append((st, mid, "就是小孩的文化课"))
                polished.append((mid, nxt_ed, rem))
            else:
                polished.append((st, nxt_ed, "就是小孩的文化课"))
            i += 2
            continue
        if _match_keyword_split(txt) is not None or len(txt) <= 10:
            polished.append((st, ed, txt))
        else:
            polished.extend(split_long_cue(txt, st, ed, max_chars=10))
        i += 1
    return polished


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
    broll_window: tuple[int, int] | None = None,
    vignette_ranges: list[tuple[int, int]] | None = None,
) -> None:
    """Post-process draft_content.json & draft_meta_info.json:
    1. Attach Haixi 17-item beauty preset to Track 0 & Track 3 clips + mirror +10 dB gain into last_nonzero_volume.
    2. Track 3 circular speaker PiP: clone independent material_id per segment (prevents mask-stroke loss on save!),
       set crisp white single mask stroke + enable_mask_stroke=True on data screens (feather=0.0),
       and soft feather=0.04 + enable_mask_stroke=False on B-roll top-right PiP.
    3. Attach linear mask (feather=1.0, centerY=0.316) on top gradient dark shadow.
    4. Patch Track 0 segment-level `模糊` to verified local cache & apply_target_type=0 (ZERO blur bleed!).
    5. Inject restrained `暗角` focus track (max 3 beats).
    6. Inject verified local JianYing `.ttf` paths, sync bold_width/shadow, enforce zero text strokes,
       and apply two-tone white-header + yellow-body styling on data-screen lists.
    """
    content_path = draft_dir / "draft_content.json"
    data = json.loads(content_path.read_text(encoding="utf-8"))

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
    stroked_circles = 0

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
            videos_list = data.setdefault("materials", {}).setdefault("videos", [])
            vmat_by_id = {v["id"]: v for v in videos_list}
            for seg in tr.get("segments", []):
                seg["volume"] = 0.0
                seg["last_nonzero_volume"] = 0.0
                st_us = seg.get("target_timerange", {}).get("start", 0)
                is_broll_pip = (
                    broll_window is not None
                    and broll_window[0] - 50_000 <= st_us <= broll_window[1] + 50_000
                )
                orig_vmat = vmat_by_id.get(seg.get("material_id"))
                if orig_vmat is not None:
                    indep_vmat = copy.deepcopy(orig_vmat)
                    new_mid = str(uuid.uuid4()).upper()
                    indep_vmat["id"] = new_mid
                    indep_vmat["video_mask_stroke"] = {
                        "alpha": 1.0,
                        "color": "#ffffff",
                        "distance": 0.0,
                        "horizontal_shift": 0.0,
                        "path": MASK_STROKE_CACHE_PATH,
                        "resource_id": MASK_STROKE_RESOURCE_ID,
                        "size": 0.20,
                        "texture": 0.0,
                        "type": "mask-stroke-single",
                        "vertical_shift": 0.0,
                    }
                    videos_list.append(indep_vmat)
                    seg["material_id"] = new_mid
                    seg["enable_mask_stroke"] = not is_broll_pip
                    if not is_broll_pip:
                        stroked_circles += 1

                extra_refs = seg.setdefault("extra_material_refs", [])
                cmask_cfg = (
                    {
                        "aspectRatio": 1.0,
                        "centerX": 0.0,
                        "centerY": 0.14,
                        "feather": 0.04,
                        "height": 0.435,
                        "invert": False,
                        "rotation": 0.0,
                        "roundCorner": 0.0,
                        "width": 0.58,
                    }
                    if is_broll_pip
                    else {
                        "aspectRatio": 1.0,
                        "centerX": -0.064,
                        "centerY": 0.093,
                        "feather": 0.0,
                        "height": 0.532,
                        "invert": False,
                        "rotation": 0.0,
                        "roundCorner": 0.0,
                        "width": 0.709,
                    }
                )
                cmask_id = str(uuid.uuid4()).upper()
                masks_list.append(
                    {
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
                        "config": cmask_cfg,
                    }
                )
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
                masks_list.append(
                    {
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
                )
                seg.setdefault("extra_material_refs", []).append(mask_id)
                top_shadow_masks += 1

    # Patch Track 0 segment-level `模糊` to verified local 11.8 cache & apply_target_type=0
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

    # Restrained `暗角` video effect track (at most 3 peak emotional beats)
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

    # Patch text materials: local font cache, bold_width, zero-stroke, black shadow & two-tone data headers
    patched_fonts = 0
    two_tone_patched = 0
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
                    txt_val = str(cjson.get("text") or "")
                    first_line = txt_val.split("\n", 1)[0]
                    if "\n" in txt_val and first_line in TWO_TONE_HEADERS:
                        hdr_len = len(first_line)
                        st_hdr = copy.deepcopy(st0)
                        st_hdr["range"] = [0, hdr_len]
                        st_hdr["fill"]["content"]["solid"]["color"] = [1.0, 1.0, 1.0]
                        st_body = copy.deepcopy(st0)
                        st_body["range"] = [hdr_len, len(txt_val)]
                        st_body["fill"]["content"]["solid"]["color"] = list(COLOR_YELLOW)
                        cjson["styles"] = [st_hdr, st_body]
                        two_tone_patched += 1
                    mat["content"] = json.dumps(cjson, ensure_ascii=False)
                    patched_fonts += 1

    content_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    meta_path = draft_dir / "draft_meta_info.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["draft_name"] = draft_name
        meta["draft_fold_path"] = str(draft_dir).replace("\\", "/")
        meta["draft_root_path"] = str(draft_dir.parent).replace("\\", "/")
        meta["tm_duration"] = total_duration_us
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"[patch] beauty on {beauty_clips} main clips (+{circle_pip_masks} circular PiP clips, "
        f"{stroked_circles} white-stroked, {beauty_refs_total} beauty refs); "
        f"linear masks={top_shadow_masks}, main-only blurs={patched_blurs}, vignettes={vignette_added}; "
        f"local fonts={patched_fonts} (two-tone headers={two_tone_patched})"
    )


def write_srt(cues: list[tuple[int, int, str]], out_path: Path) -> None:
    def fmt(us: int) -> str:
        ms = max(0, us // 1000)
        h, rem = divmod(ms, 3_600_000)
        m, rem = divmod(rem, 60_000)
        s, ms = divmod(rem, 1_000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    blocks = [f"{i}\n{fmt(st)} --> {fmt(ed)}\n{txt}\n" for i, (st, ed, txt) in enumerate(cues, start=1)]
    out_path.write_text("\n".join(blocks), encoding="utf-8")


def main() -> int:
    # 1. Load ASR + acoustic silence log
    asr_raw = json.loads(ASR_JSON_PATH.read_text(encoding="utf-8"))
    if isinstance(asr_raw, list):
        asr_raw = asr_raw[0]
    sentences: list[dict[str, Any]] = asr_raw["sentence_info"]
    silences = load_silences(SILENCE_LOG_PATH)

    raw_probe = VideoMaterial(str(RAW_VIDEO_PATH))
    video_dur_s = raw_probe.duration / 1_000_000.0
    print(f"[source] {RAW_VIDEO_PATH.name} ({raw_probe.width}x{raw_probe.height}, {video_dur_s:.2f}s)")

    # 2. Compute rough-cut kept clips & synced 1.3x subtitle cues
    clips = compute_kept_clips(sentences, silences, video_dur_s)
    total_src_kept_s = sum(c.src_end - c.src_start for c in clips)
    total_tl_us = clips[-1].tl_start_us + clips[-1].tl_dur_us
    total_tl_s = total_tl_us / 1_000_000.0
    cues = build_subtitle_cues(sentences, clips)

    print(
        f"[rough-cut] {len(clips)} kept clips | raw {video_dur_s:.1f}s -> "
        f"kept {total_src_kept_s:.1f}s -> @1.3x = {total_tl_s:.2f}s"
    )
    print(f"[subtitles] {len(cues)} synced cues")

    SCRATCH_OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_srt(cues, SCRATCH_OUT_DIR / "1115_1.3x_synced.srt")
    (SCRATCH_OUT_DIR / "1115_cut_plan.json").write_text(
        json.dumps(
            {
                "raw_duration_s": round(video_dur_s, 2),
                "kept_1x_duration_s": round(total_src_kept_s, 2),
                "timeline_1_3x_duration_s": round(total_tl_s, 2),
                "playback_speed": PLAYBACK_SPEED,
                "explicit_deletes": EXPLICIT_DELETE_RANGES,
                "clips": [c.__dict__ for c in clips],
                "subtitles": [
                    {"start_s": round(a / 1e6, 2), "end_s": round(b / 1e6, 2), "text": t}
                    for a, b, t in cues
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # 3. Create brand-new self-contained JianYing draft (never touches user's original draft!)
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

    self_contained_vid = copy_asset(RAW_VIDEO_PATH, asset_vid_dir, "1115_raw.mp4")
    raw_mat = VideoMaterial(str(self_contained_vid))

    # Self-contained BGM + SFX
    bgm_path = copy_asset(DRAFT1_AUDIO_DIR / "55c164ff20b76d77a0d845b1ad74522f.mp3", asset_aud_dir, "bgm_chinese_zither.mp3")
    sfx_drop = copy_asset(DRAFT1_AUDIO_DIR / "fd8b75a140bba2a6bad77df92e6598dd.mp3", asset_aud_dir, "sfx_water_drop.mp3")
    sfx_dong = copy_asset(DRAFT1_AUDIO_DIR / "4c4801715dbe9272b61a6d0fa1f4d6f6.mp3", asset_aud_dir, "sfx_dong.mp3")
    sfx_ding = copy_asset(DRAFT1_AUDIO_DIR / "26fac03104a2059d7c1bb4ecd0eccb4d.mp3", asset_aud_dir, "sfx_dingdong.mp3")
    sfx_whoosh = copy_asset(DRAFT1_AUDIO_DIR / "0291b72047769e085e7595ce5d65dbd2.mp3", asset_aud_dir, "sfx_whoosh.mp3")
    sfx_stamp = copy_asset(DRAFT1_AUDIO_DIR / "f2c28329e88e189b89fa16f59fc65464.mp3", asset_aud_dir, "sfx_stamp.mp3")
    sfx_page = copy_asset(DRAFT1_AUDIO_DIR / "bcebdd78f3173216cb1aaae12f7dd291.mp3", asset_aud_dir, "sfx_page.mp3")

    # Self-contained visually-verified Grade 1/2 proof & personal credential images
    img_black_field = copy_asset(BLACK_FIELD_PATH, asset_img_dir, "top_shadow_black.png")
    img_haixi_609 = copy_asset(
        DRAFT1_VIDEO_DIR / "1164_穿校服的女生在校园树下留影，下方展板写着“海晞（609.5分）年级排名8 中国美术学院”.jpg",
        asset_img_dir,
        "00_海晞609分国美校园.jpg",
    )
    img_gm_diploma = copy_asset(
        DRAFT1_VIDEO_DIR / "03_中国美术学院毕业证书封皮.jpg",
        asset_img_dir,
        "00_国美毕业证封皮.jpg",
    )
    img_gm_master = copy_asset(
        DRAFT1_VIDEO_DIR / "02_国美硕士毕业_蓝色硕士服红立柱.jpg",
        asset_img_dir,
        "00_国美硕士毕业照.jpg",
    )

    # Opening hook (distinct Grade 1 posters — never reused later!)
    img_hook_zhungaoyi = copy_asset(
        PROOF_ROOT_DIR / r"02_上课讲评图\01_高一\581_【准高一】线上集训招生海报，展示篆书作品及群内教学截图，宣传28届20天零基础篆书学习.jpg",
        asset_img_dir,
        "01_准高一线上集训.jpg",
    )
    img_hook_qiangpao = copy_asset(
        PROOF_ROOT_DIR / r"02_上课讲评图\01_高一\306_一张图文卡片，背景为书法学院门头，叠加了“高一线上全程”、“提前抢跑的高一学生”等标题及聊天记录截图.jpg",
        asset_img_dir,
        "02_提前抢跑的高一学生.jpg",
    )
    # 300 families / verified by Grade 1 students
    img_rank1 = copy_asset(
        DRAFT1_VIDEO_DIR / "286_展示全省统考第一的成绩截图、聊天记录及学生反馈，含“全省状元”“总分267.0”字样.jpg",
        asset_img_dir,
        "03_省统考第1名.jpg",
    )
    img_rank3 = copy_asset(
        DRAFT1_VIDEO_DIR / "294_展示2026年吉林省统考成绩截图及微信聊天记录，明确显示总分265分、全省第3名.jpg",
        asset_img_dir,
        "04_省统考第3名.jpg",
    )
    img_g1_zhuanshu = copy_asset(
        PROOF_ROOT_DIR / r"05_进步对比图\01_高一\935_书法海海线上特训营高一书法生篆书课程线上集训前后对比.jpg",
        asset_img_dir,
        "05_高一篆书前后对比.jpg",
    )
    # Top universities (公办/985/211/国美央美)
    img_gm_2nd = copy_asset(
        PROOF_GAOSAN_DIR / "008_展示一名书法考生从复读到国美全国第二的录取成果，含分数、名次及录取喜报.jpg",
        asset_img_dir,
        "06_国美全国第二.jpg",
    )
    img_ym_notice = copy_asset(
        PROOF_GAOSAN_DIR / "20261104_中央美术学院录取通知书与入学手册（姓名贴纸打码版）.png",
        asset_img_dir,
        "07_央美录取通知书打码版.png",
    )
    # Treat as major subject + online system + 1v1 critique
    img_g1_kaogang = copy_asset(
        PROOF_ROOT_DIR / r"02_上课讲评图\01_高一\462_红色背景宣传图，展示“特训营高一全程同学”及专属学习群讲评实况，列出考纲体系课等课程卖点.jpg",
        asset_img_dir,
        "08_高一考纲体系课.jpg",
    )
    img_plan_doc_036 = copy_asset(
        PROOF_ROOT_DIR / r"01_学生规划图\07_通用\036_海老师给学员“桐桐”制定的学习计划文档，包含每日基础任务、视频学习、书写练习及月度考核安排.png",
        asset_img_dir,
        "09_定制个人学习计划.png",
    )
    img_g1_kegao = copy_asset(
        PROOF_ROOT_DIR / r"02_上课讲评图\01_高一\372_右侧竖排大字“高一全程同学专属课稿”，背景为水波纹，下方展示一张写有“浑”“见”等字的书法作业纸.jpg",
        asset_img_dir,
        "10_高一全程专属课稿.jpg",
    )
    img_1v1 = copy_asset(DRAFT1_VIDEO_DIR / "05_1v1讲评_v3.png", asset_img_dir, "11_1v1讲评.png")
    # Exam system & 5-point deduction stakes
    img_tixike_508 = copy_asset(
        PROOF_ROOT_DIR / r"01_学生规划图\07_通用\508_课程宣传图，展示“流程①体系课展示”，列出技法、繁体字、书法史等课程模块及对应视频资料.jpg",
        asset_img_dir,
        "12_应试体系课展示.jpg",
    )
    img_rank7 = copy_asset(
        DRAFT1_VIDEO_DIR / "300_展示学生书法统考成绩268.8000分及全省第7名的喜报截图.jpg",
        asset_img_dir,
        "13_省统考第7名.jpg",
    )
    # Data Screen #3A (Weekend 40 min planning) + Grade 1/2 dramatic progress comparisons
    img_plan_g1 = copy_asset(
        PROOF_ROOT_DIR / r"01_学生规划图\01_高一\001_这是一张宣传海报，主体为“书法海海线上教育”的“高一”课程推广。画面包含两份微信聊天记录截图，内容涉及书法学习规划、隶书课程资料及作业安排，.jpg",
        asset_img_dir,
        "14_高一学习规划表.jpg",
    )
    img_g1_10d = copy_asset(
        PROOF_ROOT_DIR / r"05_进步对比图\01_高一\735_书法线上集训宣传海报，展示2v1辅导、专属学习群及高一同学10天进步对比.jpg",
        asset_img_dir,
        "15_高一10天进步对比.jpg",
    )
    img_g1_xingshu_20d = copy_asset(
        PROOF_ROOT_DIR / r"05_进步对比图\01_高一\146_展示高一同学行书作品“前”后对比，标注“20天效果”及日期“26.4.10”.jpg",
        asset_img_dir,
        "16_高一行书20天对比.jpg",
    )
    img_g1_beats_g3 = copy_asset(
        PROOF_ROOT_DIR / r"02_上课讲评图\01_高一\478_展示学生小篆作业与聊天记录，红框圈出老师讲评“不错”的反馈，标注“标记辅助线”“调整字形”.jpg",
        asset_img_dir,
        "17_高一写得超很多高三集训生.jpg",
    )
    img_g2_district1 = copy_asset(
        PROOF_ROOT_DIR / r"07_成绩结果图\02_高二\233_海报“报喜 区第一”，展示高二同学考试讲评聊天：“这个篆书分数是全区第一”.jpg",
        asset_img_dir,
        "18_高二篆书全区第一.jpg",
    )
    # Data Screen #3B (Holidays + traditional/seal character memorization pack)
    img_g1_summer = copy_asset(
        PROOF_ROOT_DIR / r"02_上课讲评图\01_高一\527_展示学生暑期篆书临摹作业，背景为美术学院，右侧附带家长群聊天记录反馈.jpg",
        asset_img_dir,
        "19_准高一暑期学习.jpg",
    )
    img_g1_daibei = copy_asset(
        PROOF_ROOT_DIR / r"02_上课讲评图\01_高一\628_宣传海报展示“高一线上全程”课程，含带背资料包及美术学院背景.jpg",
        asset_img_dir,
        "20_高一全程带背资料包.jpg",
    )
    # Closing trust loop (6 distinct verified posters)
    img_plan_g1_2v1 = copy_asset(
        PROOF_ROOT_DIR / r"01_学生规划图\01_高一\002_这是一张宣传海报，主体为书法培训机构的线上辅导内容。画面展示了学生练习的隶书作品（依据横画蚕头燕尾特征），并配有微信聊天记录截图，内容涉及学.jpeg",
        asset_img_dir,
        "21_高一专属2V1规划.jpeg",
    )
    img_g2_lishu_20d = copy_asset(
        PROOF_ROOT_DIR / r"05_进步对比图\02_高二\141_展示高二学生隶书创作的前后对比，左侧为前，右侧为后，中间有箭头连接.jpg",
        asset_img_dir,
        "22_高二隶书20天对比.jpg",
    )
    img_group_critique = copy_asset(
        DRAFT1_VIDEO_DIR / "11_专属学习群逐字讲评海报_红黄绿线标注示范.jpg",
        asset_img_dir,
        "23_专属学习群逐字讲评.jpg",
    )
    img_duxue_14 = copy_asset(
        DRAFT1_VIDEO_DIR / "14_专属督学海报_不止督促作业更关心练习状态.jpeg",
        asset_img_dir,
        "24_专属日常督学海报.jpeg",
    )
    img_parent_thanks = copy_asset(
        DRAFT1_VIDEO_DIR / "28_喜报海报_分数比预期高_家长致谢不走弯路.png",
        asset_img_dir,
        "25_家长致谢不走弯路喜报.png",
    )
    img_g1_lishu_15d = copy_asset(
        PROOF_ROOT_DIR / r"05_进步对比图\01_高一\108_展示高一学生隶书创作“前”后对比，画面包含“书法海海线上特训营”、“2V1精品辅导”及“15天效果”字样.jpg",
        asset_img_dir,
        "26_高一隶书15天前后对比.jpg",
    )

    # 4. Declare tracks in clean z-order (identical proven architecture to v13!)
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

    def cue_st(kw: str, fallback_s: float, after_us: int = 0) -> int:
        hit = find_cue_range(cues, kw, after_us=after_us)
        return hit[0] if hit else sec_to_us(fallback_s)

    def cue_ed(kw: str, fallback_s: float, after_us: int = 0) -> int:
        hit = find_cue_range(cues, kw, after_us=after_us)
        return hit[1] if hit else sec_to_us(fallback_s)

    # Exact structural windows anchored directly to synced 1.3x speech cues!
    chapter_windows: list[tuple[int, int, str]] = [
        (cue_st("第一个准备", 27.33), cue_ed("就会上强度", 30.83), "准备一\n文化课上强度"),
        (cue_st("第二个准备", 58.08), cue_ed("比初中快多了", 61.32), "准备二\n老师快 难随大流"),
        (cue_st("第三个准备", 137.73), cue_ed("小学", 140.28, after_us=137_000_000), "准备三\n兴趣≠应试书法"),
        (cue_st("所以", 169.26, after_us=168_500_000), cue_ed("应试体系", 172.77), "高一落地\n切换应试+挤时间"),
    ]

    ds1_st, ds1_ed = cue_st("以前的高校录取", 44.88), cue_ed("五五开", 52.24)
    ds2_st, ds2_ed = cue_st("应试书法呢", 148.16), cue_ed("成就感满满了", 159.64)
    ds3a_st, ds3a_ed = cue_st("像我们高一", 178.24), cue_ed("练习时间", 184.74)
    ds3b_st, ds3b_ed = cue_st("那除了周末以外", 193.86), cue_ed("督学老师监督", 204.84)

    data_sep_windows: list[tuple[int, int, float, float, float]] = [
        # (start_us, end_us, blur_pct, veil_alpha, speaker_y) — exact v9/v12/v13 top-center y=0.597!
        (ds1_st, ds1_ed, 45.0, 0.42, 0.597),
        (ds2_st, ds2_ed, 45.0, 0.42, 0.597),
        (ds3a_st, ds3a_ed, 42.0, 0.38, 0.597),
        (ds3b_st, ds3b_ed, 42.0, 0.38, 0.597),
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

    # 5. Stage 1 + 2: Main rough-cut video track at 1.3x speed & +10 dB voice gain
    #    - Split cleanly at blur_boundaries so segment-level `模糊` (apply_target_type=0) applies ONLY to Track 0
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
                volume=0.0,
                clip_settings=ClipSettings(transform_x=px, transform_y=py, scale_x=pscale, scale_y=pscale),
            )
            script.add_segment(cseg, "圆形画中画_海老师")
            added += 1
        return added

    # 5a. Crisp semi-transparent black bars (4 chapter dividers) & full-frame dark veils (4 data screens) on Track 1
    black_mat = VideoMaterial(str(img_black_field), material_name="黑场")
    for ch_st, ch_ed, _ in chapter_windows:
        bar_seg = VideoSegment(
            black_mat,
            Timerange(ch_st, ch_ed - ch_st),
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
            clip_settings=ClipSettings(transform_x=0.0, transform_y=0.0, scale_x=2.4, scale_y=2.4, alpha=veil_alpha),
        )
        veil_seg.add_animation(IntroType.渐显, "0.25s")
        veil_seg.add_animation(OutroType.渐隐, "0.25s")
        script.add_segment(veil_seg, "章节与数据暗底_黑场")
        data_cpip_total += add_circular_speaker_pip(ds_st, ds_ed, px=0.0, py=sp_y, pscale=0.40)
    print(
        f"[chapter+data] added {len(chapter_windows)} crisp chapter dividers + "
        f"{len(data_sep_windows)} data-separated screens ({data_cpip_total} circular speaker clips)"
    )

    # 5b. Full-screen credential B-roll ("书法高考这条路我走了11年 ... 国美书法专业的本硕")
    b_st = cue_st("书法高考这条路", 11.80)
    b_ed = cue_ed("国美书法专业的本硕", 17.24)
    broll_window: tuple[int, int] | None = None
    if b_ed > b_st + 1_500_000:
        b_dur = b_ed - b_st
        broll_window = (b_st, b_ed)
        d1 = round(b_dur * 0.34)
        d2 = round(b_dur * 0.32)
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
        print(f"[broll] added 3 full-screen 国美 credential photos + top-right circular PiP ({b_st/1e6:.2f}s-{b_ed/1e6:.2f}s)")

    # 6. Top gradient dark shadow + persistent two-line title (`清刻本悦`), auto-cut around B-roll, chapters & data screens!
    cutout_windows: list[tuple[int, int]] = []
    if broll_window is not None:
        cutout_windows.append(broll_window)
    for ch_st, ch_ed, _ in chapter_windows:
        cutout_windows.append((ch_st, ch_ed))
    for ds_st, ds_ed, _, _, _ in data_sep_windows:
        cutout_windows.append((ds_st, ds_ed))
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
            "刚上高中的书法生",
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
            "做好这四个心理准备",
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

    # 7 & 8. Single-line subtitles (<=10 chars!) + paired keyword-split highlights
    #        - Regular cues: y=-0.56 (or y=-0.49 stacked with keyword at y=-0.69)
    #        - Inside data-separation screens ONLY: drop to y=-0.729 (keyword relays at y=-0.708)
    sub_style = TextStyle(
        size=13.5,
        color=COLOR_WHITE,
        align=1,
        auto_wrapping=True,
        max_line_width=0.90,
    )
    sub_clip_normal = ClipSettings(transform_x=0.0, transform_y=-0.56, scale_x=1.0, scale_y=1.0)
    sub_clip_paired = ClipSettings(transform_x=0.0, transform_y=-0.49, scale_x=1.0, scale_y=1.0)
    sub_clip_data = ClipSettings(transform_x=0.0, transform_y=-0.729, scale_x=1.0, scale_y=1.0)
    sub_shadow = TextShadow(alpha=0.85, color=(0.0, 0.0, 0.0), diffuse=10.0, distance=5.0, angle=-45.0)
    kw_shadow = TextShadow(alpha=0.88, color=(0.0, 0.0, 0.0), diffuse=10.0, distance=5.0, angle=-45.0)

    def in_data_window(st_us: int, ed_us: int) -> bool:
        mid = (st_us + ed_us) // 2
        return any(ds_st - 120_000 <= mid <= ds_ed + 200_000 for ds_st, ds_ed, _, _, _ in data_sep_windows)

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
        is_data_cue = in_data_window(st, ed)
        hit_kw = _match_keyword_split(txt)
        rule_key = f"{hit_kw[0]}|{hit_kw[1]}" if hit_kw is not None else ""
        if hit_kw is not None and rule_key not in used_kw_rules and (ed - st) >= 650_000:
            main_t, kw_t, kw_sz, kw_anim, sfx_k, sfx_v = hit_kw
            used_kw_rules.add(rule_key)

            total_len = max(1, len(main_t) + len(kw_t))
            ratio = len(main_t) / total_len
            kw_st = st + int((ed - st) * ratio) - 80_000
            kw_st = max(st + 180_000, min(ed - 420_000, kw_st))
            if kw_st < last_kw_end + 80_000:
                kw_st = last_kw_end + 80_000
            kw_dur = ed - kw_st

            if is_data_cue and kw_dur >= 350_000:
                main_dur = max(180_000, kw_st - st)
                tseg = TextSegment(
                    main_t,
                    Timerange(st, main_dur),
                    font=FontType.金陵体,
                    style=sub_style,
                    clip_settings=sub_clip_data,
                    border=None,
                    shadow=sub_shadow,
                )
                script.add_segment(tseg, "字幕_金陵体")
                sub_count += 1
                kw_y = -0.708
            else:
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
                kw_y = -0.69

            if kw_dur >= 350_000:
                kseg = TextSegment(
                    kw_t,
                    Timerange(kw_st, kw_dur),
                    font=FontType.仓耳丰黑,
                    style=TextStyle(size=kw_sz, color=COLOR_YELLOW, align=1, bold=False),
                    clip_settings=ClipSettings(transform_x=0.0, transform_y=kw_y, scale_x=1.0, scale_y=1.0),
                    border=None,
                    shadow=kw_shadow,
                )
                kseg.add_animation(kw_anim, "0.3s")
                script.add_segment(kseg, "重点大字包装")
                sfx_events.append((kw_st, sfx_map[sfx_k], sfx_v))
                last_kw_end = ed
                popup_count += 1
        else:
            # Safety cap: if an unmatched cue somehow exceeded 10 chars, split it cleanly!
            parts_safe = [(st, ed, txt)] if len(txt) <= 10 else split_long_cue(txt, st, ed, max_chars=10)
            for pst, ped, ptxt in parts_safe:
                tseg = TextSegment(
                    ptxt,
                    Timerange(pst, ped - pst),
                    font=FontType.金陵体,
                    style=sub_style,
                    clip_settings=sub_clip_data if is_data_cue else sub_clip_normal,
                    border=None,
                    shadow=sub_shadow,
                )
                script.add_segment(tseg, "字幕_金陵体")
                sub_count += 1

    print(f"[subtitles] placed {sub_count} single-line main cues (<=10 chars) + {popup_count} paired keyword highlights")

    # 9. 100% Collision-Free Real `06_交付知识库` PiPs + Native Animated Data Lists & 4 Chapter Dividers
    pip_plan: list[tuple[str, str, Path, float, float, float, int, int, IntroType, Path | None]] = [
        # --- 黄金前3秒开场钩子 (0.40s-3.60s): 准高一集训 + 高一抢跑 (绝不与后文重复!) ---
        ("LEFT",   "画中画_左", img_hook_zhungaoyi, -0.62, 0.08, 0.34, 400_000,   3_600_000, IntroType.向右滑动, sfx_whoosh),
        ("RIGHT",  "画中画_右", img_hook_qiangpao,   0.62, 0.08, 0.34, 700_000,   3_600_000, IntroType.向左滑动, None),

        # --- 全国近300家庭/高一验证 (18.54s-23.60s) ---
        ("LEFT",   "画中画_左", img_rank1,          -0.64, 0.12, 0.31, 18_540_000, 23_600_000, IntroType.向右滑动, sfx_page),
        ("RIGHT",  "画中画_右", img_rank3,           0.64, 0.12, 0.31, 18_900_000, 23_600_000, IntroType.向左滑动, None),
        ("CENTER", "画中画_中", img_g1_zhuanshu,     0.00, 0.15, 0.28, 20_800_000, 23_600_000, IntroType.向上滑动, None),

        # --- 公办本科 / 985 / 211 / 国美央美 (52.50s-57.70s, 紧接数据屏#1后、章节#2前) ---
        ("LEFT",   "画中画_左", img_gm_2nd,         -0.62, 0.08, 0.34, 52_500_000, 57_700_000, IntroType.向右滑动, sfx_whoosh),
        ("RIGHT",  "画中画_右", img_ym_notice,       0.62, 0.08, 0.34, 53_100_000, 57_700_000, IntroType.向左滑动, None),

        # --- 把书法当成一门主科规划 + 学了会用会考 (127.60s-137.40s, 严格在章节#3前收尾) ---
        ("LEFT",   "画中画_左", img_g1_kaogang,     -0.62, 0.08, 0.34, 127_600_000, 132_400_000, IntroType.向右滑动, sfx_page),
        ("RIGHT",  "画中画_右", img_plan_doc_036,    0.62, 0.08, 0.34, 128_000_000, 132_400_000, IntroType.向左滑动, None),
        ("LEFT",   "画中画_左", img_g1_kegao,       -0.62, 0.08, 0.34, 133_200_000, 137_400_000, IntroType.向右滑动, sfx_whoosh),
        ("RIGHT",  "画中画_右", img_1v1,             0.62, 0.08, 0.34, 133_600_000, 137_400_000, IntroType.向左滑动, None),

        # --- 考场错字扣5分拉下100来名 (160.20s-168.80s, 严格在数据屏#2后、章节#4前) ---
        ("LEFT",   "画中画_左", img_tixike_508,     -0.62, 0.08, 0.34, 160_200_000, 164_800_000, IntroType.向右滑动, sfx_page),
        ("RIGHT",  "画中画_右", img_rank7,           0.62, 0.08, 0.34, 165_000_000, 168_800_000, IntroType.向左滑动, sfx_drop),

        # --- 数据屏#3A 右侧配图 (178.40s-184.74s): 左文右图错位，零叠字 ---
        ("RIGHT",  "画中画_右", img_plan_g1,         0.54, -0.06, 0.34, ds3a_st + 200_000, ds3a_ed, IntroType.向左滑动, sfx_page),

        # --- 高一高二真实进步 + 高二超越高三集训生 (185.45s-193.65s) ---
        ("LEFT",   "画中画_左", img_g1_10d,         -0.62, 0.08, 0.34, 185_450_000, 189_100_000, IntroType.向右滑动, sfx_whoosh),
        ("RIGHT",  "画中画_右", img_g1_xingshu_20d,  0.62, 0.08, 0.34, 185_800_000, 189_100_000, IntroType.向左滑动, None),
        ("LEFT",   "画中画_左", img_g1_beats_g3,    -0.62, 0.08, 0.34, 189_400_000, 193_650_000, IntroType.向右滑动, sfx_page),
        ("RIGHT",  "画中画_右", img_g2_district1,    0.62, 0.08, 0.34, 189_800_000, 193_650_000, IntroType.向左滑动, None),

        # --- 数据屏#3B 右侧配图 (194.20s-204.84s): 准高一暑期学习 + 全程带背资料包 ---
        ("RIGHT",  "画中画_右", img_g1_summer,       0.54, -0.06, 0.34, ds3b_st + 350_000, 199_000_000, IntroType.向左滑动, sfx_drop),
        ("RIGHT",  "画中画_右", img_g1_daibei,       0.54, -0.06, 0.34, 199_200_000,       ds3b_ed,     IntroType.向左滑动, sfx_page),

        # --- 结尾服务价值与转化闭环 (215.20s-228.67s): 3组4~4.5秒稳步成对展示，绝不闪切 ---
        ("LEFT",   "画中画_左", img_plan_g1_2v1,    -0.62, 0.10, 0.34, 215_200_000, 219_500_000, IntroType.向右滑动, sfx_page),
        ("RIGHT",  "画中画_右", img_g2_lishu_20d,    0.62, 0.10, 0.34, 215_500_000, 219_500_000, IntroType.向左滑动, None),
        ("LEFT",   "画中画_左", img_group_critique, -0.62, 0.10, 0.34, 219_800_000, 224_200_000, IntroType.向右滑动, sfx_whoosh),
        ("RIGHT",  "画中画_右", img_duxue_14,        0.62, 0.10, 0.34, 220_100_000, 224_200_000, IntroType.向左滑动, None),
        ("LEFT",   "画中画_左", img_parent_thanks,  -0.62, 0.10, 0.34, 224_500_000, total_tl_us, IntroType.向右滑动, sfx_page),
        ("RIGHT",  "画中画_右", img_g1_lishu_15d,    0.62, 0.10, 0.34, 224_800_000, total_tl_us, IntroType.向左滑动, None),
    ]

    side_text_plan: list[tuple[str, str, str, float, float, float, int, int, TextIntro]] = [
        # 章节分段 #1
        ("CENTER", "侧边原生文字_右", chapter_windows[0][2], 0.00, -0.04, 25.0, chapter_windows[0][0], chapter_windows[0][1], TextIntro.向上弹入),
        # 数据分离屏 #1 — 以前三七开 vs 现在五五开 (双色层次: 白标题+黄内容)
        ("LEFT",   "侧边原生文字_左", "以前录取\n文化 30%\n专业 70%\n靠专业拉分", -0.50, -0.06, 15.5, ds1_st, ds1_ed, TextIntro.打字机_I),
        ("RIGHT",  "侧边原生文字_右", "现在录取\n文化 50%\n专业 50%\n文化不能丢",  0.50, -0.06, 15.5, cue_st("但现在基本没有了", 49.59), ds1_ed, TextIntro.向上弹入),
        # 章节分段 #2
        ("CENTER", "侧边原生文字_右", chapter_windows[1][2], 0.00, -0.04, 25.0, chapter_windows[1][0], chapter_windows[1][1], TextIntro.向上弹入),
        # 章节分段 #3
        ("CENTER", "侧边原生文字_右", chapter_windows[2][2], 0.00, -0.04, 25.0, chapter_windows[2][0], chapter_windows[2][1], TextIntro.向上弹入),
        # 数据分离屏 #2 — 应试书法 vs 兴趣班书法
        ("LEFT",   "侧边原生文字_左", "应试书法\n碑帖精准度\n多体临摹创作\n繁体字与篆字", -0.50, -0.06, 15.0, ds2_st, ds2_ed, TextIntro.打字机_I),
        ("RIGHT",  "侧边原生文字_右", "兴趣班书法\n老师哄着写\n抄几幅作品\n拿比赛奖状",   0.50, -0.06, 15.0, cue_st("以前在书法兴趣班", 154.76), ds2_ed, TextIntro.打字机_I),
        # 章节分段 #4
        ("CENTER", "侧边原生文字_右", chapter_windows[3][2], 0.00, -0.04, 25.0, chapter_windows[3][0], chapter_windows[3][1], TextIntro.向上弹入),
        # 数据分离屏 #3A — 平时周末怎么挤时间 (左文右图)
        ("LEFT",   "侧边原生文字_左", "平时周末\n每周 1~2 天\n每天 40 分钟\n稳扎专业底子", -0.50, -0.06, 15.0, ds3a_st, ds3a_ed, TextIntro.打字机_I),
        # 数据分离屏 #3B — 寒暑假/小长假提分 (左文右图)
        ("LEFT",   "侧边原生文字_左", "假期提分\n寒暑假小长假\n考纲真题训练\n繁篆带背+督学", -0.50, -0.06, 15.0, ds3b_st, ds3b_ed, TextIntro.打字机_I),
    ]

    # Hard in-script 2D space-time collision gate + >=1.4s no-flash-cut gate!
    zone_items: dict[str, list[tuple[int, int, str]]] = {"LEFT": [], "CENTER": [], "RIGHT": []}
    for z, _, p, _, _, _, st, ed, _, _ in pip_plan:
        assert ed - st >= 1_400_000, f"Flash-cut PiP <1.4s: {p.name} ({(ed-st)/1e6:.2f}s)"
        zone_items[z].append((st, ed, f"PiP:{p.name}"))
    for z, _, lbl, _, _, _, st, ed, _ in side_text_plan:
        assert ed - st >= 1_400_000, f"Flash-cut side text <1.4s: {lbl} ({(ed-st)/1e6:.2f}s)"
        zone_items[z].append((st, ed, f"TEXT:{lbl.splitlines()[0]}"))
    for z, lst in zone_items.items():
        lst.sort(key=lambda x: x[0])
        for (a0, a1, an), (b0, b1, bn) in zip(lst, lst[1:]):
            assert b0 >= a1, (
                f"ZONE COLLISION in {z}: {an}[{a0/1e6:.2f}-{a1/1e6:.2f}] vs {bn}[{b0/1e6:.2f}-{b1/1e6:.2f}]"
            )

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
            sfx_events.append((st, sfx_p, 1.0))
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
    print(f"[side-text] added {side_added} collision-free native JianYing callouts & chapter titles")

    # 9b. 3 restrained `暗角` focus accents (max 3!)
    vignette_ranges: list[tuple[int, int]] = []
    for vkw, extra_dur in [
        ("当头一棒", 1_500_000),
        ("拉下100来名", 1_600_000),
        ("把孩子好好的底子", 1_600_000),
    ]:
        vhit = find_cue_range(cues, vkw)
        if vhit:
            vst = max(0, vhit[0] - 100_000)
            vdur = min(extra_dur, total_tl_us - vst)
            if vdur >= 600_000:
                vignette_ranges.append((vst, vdur))

    # 10. Looped BGM at -15 dB (0.1778)
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
            volume=0.1778,
        )
        if bgm_cursor == 0:
            aseg.add_fade("0.8s", "0s")
        if bgm_cursor + seg_dur >= total_tl_us:
            aseg.add_fade("0s", "2.0s")
        script.add_segment(aseg, "BGM_古筝轻音乐")
        bgm_cursor += seg_dur
        bgm_segs += 1
    print(f"[bgm] added {bgm_segs} looped BGM segments (vol=0.1778 ≈ -15 dB)")

    # 11. Sparse deduplicated SFX accents (0 dB ~ 1.25)
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

    # 12. Save draft + post-process beauty, masks, mask strokes, vignettes, verified local fonts & meta info
    script.save()
    patch_draft_postprocess(
        draft_dir,
        NEW_DRAFT_NAME,
        total_tl_us,
        broll_window=broll_window,
        vignette_ranges=vignette_ranges,
    )
    print(f"[done] JianYing draft saved to: {draft_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
