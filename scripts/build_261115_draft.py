#!/usr/bin/env python3
"""
Build a complete rough-cut + packaged JianYing 11.8 plaintext draft for
`261115书法生想上国美央美` using pyJianYingDraft.

Features:
  1. Non-destructive rough cut (removes retakes, stutters, fillers, and long silences/breaths)
     with all kept talking-head clips set to 1.3x playback speed.
  2. Subtitles: FontType.金陵体 (FZCuJinLJW.ttf), size 13.5, lower-middle (y=-0.56),
     #FFFFFF + black border (0.08) + shadow, ASR typos corrected, exact 1.3x synced timing.
  3. Persistent top two-line title: FontType.清刻本悦 (FZQKBYSJW.ttf, from Timeline #3),
     color palette from Draft #1 (#FFFFFF top line + #FFF29D light-yellow hook line),
     positioned cleanly in the white-wall headroom above the speaker's head.
  4. Emphasis keyword popups (#FFF29D & #FF619D) with Draft #1 / Timeline #3 intro animations.
  5. Verified masked proof PiP cards (国美/央美喜报、录取通知书、省统考喜报、线上1v1讲评)
     placed on the left/right edges so they never cover the speaker's face.
  6. Looped ancient-zither BGM (volume=0.3162 ≈ -10 dB, 2s fade-out) + sparse SFX accents.
  7. Injects verified local JianYing font cache paths so custom fonts render immediately.
"""
from __future__ import annotations

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
    OutroType,
    TextBorder,
    TextIntro,
    TextSegment,
    TextShadow,
    TextStyle,
    Timerange,
    TrackSpec,
    TrackType,
    VideoMaterial,
    VideoSegment,
)

# ---------------------------------------------------------------------------
# Paths & Constants
# ---------------------------------------------------------------------------
JIANYING_DRAFTS_ROOT = Path(r"D:\Software\剪映\JianyingPro Drafts")
NEW_DRAFT_NAME = "261115书法生想上国美央美_AI粗剪包装_v2"

RAW_VIDEO_PATH = Path(r"D:\Software\剪映\AI素材库\261115书法生想上国美央美_原片.mp4")
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
PROOF_GAOSAN_DIR = Path(
    r"D:\Jiely Life\projects\海晞文化-内容助理\02_resources\书法海海知识库\06_交付知识库\02_交付证明\07_成绩结果图\03_高三"
)

CANVAS_WIDTH = 1320
CANVAS_HEIGHT = 1760
DRAFT_FPS = 30
PLAYBACK_SPEED = 1.3

# Exact local font cache paths verified on this PC (from Draft 1 TL0 & TL3)
LOCAL_FONT_CACHE = {
    FontType.金陵体.value.resource_id: (
        "C:/Users/jiely/AppData/Local/JianyingPro/User Data/Cache/effect/"
        "7086699209738424840/599831579b8aa5b5f0608d5e7d4ec5ce/FZCuJinLJW.ttf"
    ),
    FontType.清刻本悦.value.resource_id: (
        "C:/Users/jiely/AppData/Local/JianyingPro/User Data/Cache/effect/"
        "7086429206543864350/2e70579a0538bde91edc1eaedc68c02f/FZQKBYSJW.ttf"
    ),
    FontType.新青年体.value.resource_id: (
        "D:/Software/剪映/JianyingPro/11.8.0.14778/Resources/Font/新青年体.ttf"
    ),
}

# Colors (RGB 0..1)
COLOR_WHITE = (1.0, 1.0, 1.0)
COLOR_YELLOW = (1.0, 0.949, 0.616)  # #FFF29D — Draft #1 main highlight yellow
COLOR_PINK = (1.0, 0.380, 0.616)    # #FF619D — Draft #1 secondary number highlight pink

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
    """Split a Chinese clause at natural semantic boundaries instead of mid-word."""
    if len(chunk) <= max_chars:
        return [chunk]
    # Preferred natural break tokens (break BEFORE these words)
    break_before = ["以及", "而且", "但是", "或者", "并且", "就是", "其实", "最后", "同时", "然后", "直接", "利用", "能够", "已经", "和", "给", "把", "去", "在", "到"]
    # Preferred break AFTER these tokens
    break_after = ["的", "了", "啊", "呢", "吧", "上", "中", "里", "后", "前"]
    mid = len(chunk) // 2
    best_idx = None
    best_dist = 999
    for tok in break_before:
        pos = chunk.find(tok, 4, len(chunk) - 3)
        if pos != -1 and abs(pos - mid) < best_dist:
            best_dist = abs(pos - mid)
            best_idx = pos
    if best_idx is None or best_dist > 5:
        for tok in break_after:
            pos = chunk.find(tok, 4, len(chunk) - 4)
            if pos != -1:
                cand = pos + len(tok)
                if abs(cand - mid) < best_dist:
                    best_dist = abs(cand - mid)
                    best_idx = cand
    if best_idx is None:
        best_idx = mid
    left = chunk[:best_idx].strip()
    right = chunk[best_idx:].strip()
    return [p for p in (left, right) if p]


def split_long_cue(text: str, start_us: int, end_us: int, max_chars: int = 14) -> list[tuple[int, int, str]]:
    """Split a long subtitle sentence cleanly at punctuation or natural semantic breaks."""
    dur = end_us - start_us
    if len(text) <= max_chars or dur < 700_000:
        clean = re.sub(r"[，。、；：,]+", " ", text).strip()
        return [(start_us, end_us, clean)]

    # Split on strong & soft punctuation first
    parts = [p.strip() for p in re.split(r"[，。！？、；：,]", text) if p.strip()]
    merged: list[str] = []
    for part in parts:
        if merged and len(merged[-1]) + 1 + len(part) <= max_chars:
            merged[-1] = merged[-1] + " " + part
        elif merged and len(part) <= 2:
            merged[-1] = merged[-1] + part
        else:
            merged.append(part)

    final_parts: list[str] = []
    for chunk in merged:
        if len(chunk) <= max_chars + 1:
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
            nxt = min(end_us - 120_000, cur + max(250_000, share))
        if nxt > cur:
            cues.append((cur, nxt, part))
            cur = nxt
    return cues


def build_subtitle_cues(sentences: list[dict[str, Any]], clips: list[KeptClip]) -> list[tuple[int, int, str]]:
    """Convert ASR sentences into clean, non-overlapping 1.3x timeline subtitle cues."""
    raw_cues: list[tuple[int, int, str, bool]] = []  # (start_us, end_us, text, ends_sentence)

    for sent in sentences:
        sa = sent["start"] / 1000.0
        sb = sent["end"] / 1000.0
        txt = str(sent.get("sentence", ""))

        # Handle partially trimmed sentences with explicit prefix deletions
        if abs(sa - 144.44) < 0.2:
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

        sub_parts = split_long_cue(clean_txt, t0, t1, max_chars=14)
        for idx_p, (pst, ped, ptxt) in enumerate(sub_parts):
            raw_cues.append((pst, ped, ptxt, ends_sentence and idx_p == len(sub_parts) - 1))

    # Merge short fragments (<= 3 chars) cleanly without crossing sentence boundaries!
    merged_cues: list[tuple[int, int, str, bool]] = []
    for st, ed, txt, ends_s in sorted(raw_cues, key=lambda x: x[0]):
        if merged_cues:
            pst, ped, ptxt, p_ends = merged_cues[-1]
            if st < ped:
                st = ped
            if ed <= st + 90_000:
                continue
            # Merge forward into next cue if previous cue was very short (like "今天", "家长", "400")
            if not p_ends and len(ptxt) <= 3 and (st - ped) <= 400_000 and len(ptxt) + len(txt) <= 15:
                sep = " " if (ptxt[-1].isdigit() or txt[0].isdigit()) else ""
                merged_cues[-1] = (pst, ed, ptxt + sep + txt, ends_s)
                continue
            # Merge tiny trailing word into previous cue (like "内蒙" + "400", "马上" + "掉头")
            if not p_ends and len(txt) <= 3 and (st - ped) <= 400_000 and len(ptxt) + len(txt) <= 15:
                merged_cues[-1] = (pst, ed, ptxt + txt, ends_s)
                continue
        merged_cues.append((st, ed, txt, ends_s))

    return [(st, ed, txt) for st, ed, txt, _ in merged_cues]


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


def patch_draft_fonts_and_meta(draft_dir: Path, draft_name: str, total_duration_us: int) -> None:
    """Inject verified local JianYing font paths so custom fonts render immediately in 11.8."""
    content_path = draft_dir / "draft_content.json"
    data = json.loads(content_path.read_text(encoding="utf-8"))

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
            strokes = st0.get("strokes") or []
            if strokes and isinstance(strokes[0], dict):
                mat["border_width"] = strokes[0].get("width", 0.08)
            shadows = st0.get("shadows") or []
            if shadows and isinstance(shadows[0], dict):
                mat["has_shadow"] = True
                mat["shadow_color"] = "#000000"
                mat["shadow_alpha"] = shadows[0].get("alpha", 0.75)
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

    # Update draft_meta_info.json with proper name & duration
    meta_path = draft_dir / "draft_meta_info.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["draft_name"] = draft_name
        meta["draft_fold_path"] = str(draft_dir).replace("\\", "/")
        meta["draft_root_path"] = str(draft_dir.parent).replace("\\", "/")
        meta["tm_duration"] = total_duration_us
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[patch] injected verified local font paths on {patched_fonts} text materials")


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

    # 4. Declare tracks in clean z-order (video -> PiP -> text -> audio)
    script.append_track(TrackSpec(TrackType.video, name="主视频_1.3x粗剪"))
    script.append_track(TrackSpec(TrackType.video, name="画中画_左"))
    script.append_track(TrackSpec(TrackType.video, name="画中画_中"))
    script.append_track(TrackSpec(TrackType.video, name="画中画_右"))

    script.append_track(TrackSpec(TrackType.text, name="字幕_金陵体"))
    script.append_track(TrackSpec(TrackType.text, name="重点大字包装"))
    script.append_track(TrackSpec(TrackType.text, name="顶部常驻标题_上行"))
    script.append_track(TrackSpec(TrackType.text, name="顶部常驻标题_下行"))

    script.append_track(TrackSpec(TrackType.audio, name="BGM_古筝轻音乐"))
    script.append_track(TrackSpec(TrackType.audio, name="音效点缀"))

    # 5. Add main rough-cut video track at 1.3x speed
    for clip in clips:
        src_tr = Timerange(sec_to_us(clip.src_start), sec_to_us(clip.src_end - clip.src_start))
        tgt_tr = Timerange(clip.tl_start_us, clip.tl_dur_us)
        vseg = VideoSegment(
            raw_mat,
            tgt_tr,
            source_timerange=src_tr,
            speed=PLAYBACK_SPEED,
            volume=1.0,
            clip_settings=ClipSettings(
                scale_x=clip.scale,
                scale_y=clip.scale,
                transform_y=clip.transform_y,
            ),
        )
        script.add_segment(vseg, "主视频_1.3x粗剪")

    # 6. Add persistent top two-line title
    #    - Font: FontType.清刻本悦 (FZQKBYSJW.ttf — Timeline #3's exact top-title font!)
    #    - Color: Draft #1's palette (#FFFFFF upper line + #FFF29D light-yellow lower hook line!)
    #    - Intro: TextIntro.向上弹入 (0.4s, same as Draft #1 T15!)
    top_line1 = TextSegment(
        "书法生想上国美央美",
        Timerange(0, total_tl_us),
        font=FontType.清刻本悦,
        style=TextStyle(size=12.5, color=COLOR_WHITE, align=1, bold=False, letter_spacing=1),
        clip_settings=ClipSettings(transform_x=0.0, transform_y=0.845, scale_x=1.38, scale_y=1.38),
        border=TextBorder(alpha=1.0, color=(0.0, 0.0, 0.0), width=35.0),
        shadow=TextShadow(alpha=0.65, color=(0.0, 0.0, 0.0), diffuse=15.0, distance=5.0, angle=-45.0),
    )
    top_line1.add_animation(TextIntro.向上弹入, "0.4s")
    script.add_segment(top_line1, "顶部常驻标题_上行")

    top_line2 = TextSegment(
        "高中三年怎么规划？",
        Timerange(0, total_tl_us),
        font=FontType.清刻本悦,
        style=TextStyle(size=11.0, color=COLOR_YELLOW, align=1, bold=False, letter_spacing=1),
        clip_settings=ClipSettings(transform_x=0.0, transform_y=0.685, scale_x=1.38, scale_y=1.38),
        border=TextBorder(alpha=1.0, color=(0.0, 0.0, 0.0), width=40.0),
        shadow=TextShadow(alpha=0.75, color=(0.0, 0.0, 0.0), diffuse=15.0, distance=5.0, angle=-45.0),
    )
    top_line2.add_animation(TextIntro.向上弹入, "0.4s")
    script.add_segment(top_line2, "顶部常驻标题_下行")

    # 7. Add subtitles: 金陵体, size 13.5 (13~14), lower-middle (y=-0.56)
    sub_style = TextStyle(
        size=13.5,
        color=COLOR_WHITE,
        align=1,
        auto_wrapping=True,
        max_line_width=0.84,
    )
    sub_clip = ClipSettings(transform_x=0.0, transform_y=-0.56, scale_x=1.0, scale_y=1.0)
    sub_border = TextBorder(alpha=1.0, color=(0.0, 0.0, 0.0), width=40.0)  # 0.08 in JianYing
    sub_shadow = TextShadow(alpha=0.78, color=(0.0, 0.0, 0.0), diffuse=15.0, distance=5.0, angle=-45.0)

    for st, ed, txt in cues:
        tseg = TextSegment(
            txt,
            Timerange(st, ed - st),
            font=FontType.金陵体,
            style=sub_style,
            clip_settings=sub_clip,
            border=sub_border,
            shadow=sub_shadow,
        )
        script.add_segment(tseg, "字幕_金陵体")

    # 8. Add emphasis keyword popups (placed cleanly at y=-0.76 below subtitle or y=-0.36 above, never over face!)
    #    Each entry: (search_keyword, popup_text, color, font, y, scale, intro_anim, sfx_path, sfx_vol)
    popup_specs: list[tuple[str, str, tuple[float, float, float], FontType, float, float, TextIntro, Path, float]] = [
        ("中国美术学院", "国美本硕 · 七年", COLOR_YELLOW, FontType.金陵体, -0.76, 1.45, TextIntro.向上弹入, sfx_drop, 0.45),
        ("合格证", "折在文化分!", COLOR_PINK, FontType.新青年体, -0.76, 1.55, TextIntro.缩小, sfx_dong, 0.40),
        ("平时死守文化课", "平时死守文化课\n周末书法打底", COLOR_YELLOW, FontType.金陵体, -0.77, 1.35, TextIntro.向上弹入, sfx_ding, 0.48),
        ("不低于本省", "不低于本省本科线", COLOR_YELLOW, FontType.金陵体, -0.76, 1.45, TextIntro.左移弹动, sfx_drop, 0.45),
        ("浙江省490", "浙490 · 苏480 · 豫460 · 鲁440", COLOR_PINK, FontType.新青年体, -0.76, 1.18, TextIntro.打字机_I, sfx_drop, 0.45),
        ("黑龙江380", "黑380 · 吉340 · 内蒙400", COLOR_PINK, FontType.新青年体, -0.76, 1.25, TextIntro.打字机_I, sfx_drop, 0.45),
        ("悬殊100分", "悬殊 100 分!", COLOR_PINK, FontType.新青年体, -0.76, 1.65, TextIntro.缩小, sfx_stamp, 0.45),
        ("画室机构", "别早早脱产烧钱集训", COLOR_YELLOW, FontType.金陵体, -0.76, 1.38, TextIntro.向上弹入, sfx_dong, 0.38),
        ("篆刻科目", "高二尽早接触【篆刻】", COLOR_YELLOW, FontType.金陵体, -0.76, 1.42, TextIntro.左移弹动, sfx_ding, 0.48),
        ("四体是100", "国美：书法100 + 篆刻100 + 古汉语100", COLOR_PINK, FontType.新青年体, -0.76, 1.05, TextIntro.左移弹动, sfx_drop, 0.45),
        ("央美呢", "央美：书法100 + 篆刻100", COLOR_PINK, FontType.新青年体, -0.76, 1.28, TextIntro.缩小, sfx_stamp, 0.45),
        ("背单词", "碎片时间背单词 · 背文综", COLOR_YELLOW, FontType.金陵体, -0.76, 1.32, TextIntro.打字机_I, sfx_drop, 0.45),
        ("校考一结束", "2-3月校考结束 → 立刻冲文化", COLOR_YELLOW, FontType.金陵体, -0.76, 1.22, TextIntro.向上弹入, sfx_ding, 0.45),
        ("双线并进", "专业 + 文化 · 双线并进", COLOR_YELLOW, FontType.金陵体, -0.76, 1.42, TextIntro.缩小, sfx_dong, 0.38),
        ("留下书法艺考", "评论区留【书法艺考】", COLOR_YELLOW, FontType.金陵体, -0.76, 1.48, TextIntro.向上弹入, sfx_ding, 0.50),
    ]

    sfx_events: list[tuple[int, Path, float]] = []
    last_popup_end = 0
    popup_count = 0
    for kw, label, color, font, py, pscale, intro_anim, sfx_path, sfx_vol in popup_specs:
        hit = find_cue_range(cues, kw, after_us=max(0, last_popup_end - 300_000))
        if not hit:
            continue
        st, ed = hit
        if st < last_popup_end + 150_000:
            st = last_popup_end + 150_000
        dur = max(1_600_000, min(3_400_000, ed - st + 900_000))
        if st + dur > total_tl_us:
            dur = total_tl_us - st
        if dur < 600_000:
            continue
        pseg = TextSegment(
            label,
            Timerange(st, dur),
            font=font,
            style=TextStyle(size=12.0, color=color, align=1, bold=False),
            clip_settings=ClipSettings(transform_x=0.0, transform_y=py, scale_x=pscale, scale_y=pscale),
            border=TextBorder(alpha=1.0, color=(0.0, 0.0, 0.0), width=42.0),
            shadow=TextShadow(alpha=0.80, color=(0.0, 0.0, 0.0), diffuse=15.0, distance=5.0, angle=-45.0),
        )
        pseg.add_animation(intro_anim, "0.35s")
        script.add_segment(pseg, "重点大字包装")
        sfx_events.append((st, sfx_path, sfx_vol))
        last_popup_end = st + dur
        popup_count += 1
    print(f"[popups] added {popup_count} emphasis text popups")

    # 9. Add PiP proof cards (strictly on left/right/lower edges, never covering speaker's face!)
    pip_specs: list[tuple[str, str, Path, float, float, float, int, IntroType, Path]] = [
        ("一共七年", "画中画_左", img_gm_2nd, -0.62, 0.05, 0.34, 2_800_000, IntroType.向右滑动, sfx_whoosh),
        ("送进国美", "画中画_左", img_gm_xibao, -0.62, 0.04, 0.34, 3_000_000, IntroType.向右滑动, sfx_whoosh),
        ("送进国美", "画中画_右", img_ym_notice, 0.62, 0.04, 0.34, 3_000_000, IntroType.向左滑动, sfx_page),
        ("省统考", "画中画_左", img_rank1, -0.64, 0.16, 0.30, 2_700_000, IntroType.向上滑动, sfx_whoosh),
        ("省统考", "画中画_中", img_rank3, 0.00, -0.18, 0.28, 2_500_000, IntroType.向上滑动, sfx_drop),
        ("省统考", "画中画_右", img_rank7, 0.64, 0.16, 0.30, 2_700_000, IntroType.向上滑动, sfx_drop),
        ("在线上找专业", "画中画_左", img_1v1, -0.60, -0.02, 0.36, 3_200_000, IntroType.向右滑动, sfx_whoosh),
        ("在线上找专业", "画中画_右", img_online_class, 0.60, -0.02, 0.36, 3_200_000, IntroType.向左滑动, sfx_page),
        ("央美呢", "画中画_右", img_ym_zhuanke, 0.61, 0.02, 0.36, 3_500_000, IntroType.向左滑动, sfx_page),
    ]

    track_last_end: dict[str, int] = {}
    pip_count = 0
    for kw, tname, img_path, px, py, pscale, dur_us, anim, sfx_p in pip_specs:
        hit = find_cue_range(cues, kw)
        if not hit:
            continue
        st = hit[0]
        if tname == "画中画_中":
            st += 250_000
        elif tname == "画中画_右" and kw in ("送进国美", "省统考", "在线上找专业"):
            st += 450_000
        prev_end = track_last_end.get(tname, 0)
        if st < prev_end + 200_000:
            st = prev_end + 200_000
        if st + dur_us > total_tl_us:
            dur_us = total_tl_us - st
        if dur_us < 800_000:
            continue
        vmat = VideoMaterial(str(img_path))
        pseg = VideoSegment(
            vmat,
            Timerange(st, dur_us),
            clip_settings=ClipSettings(transform_x=px, transform_y=py, scale_x=pscale, scale_y=pscale),
        )
        pseg.add_animation(anim, "0.35s")
        pseg.add_animation(OutroType.渐隐, "0.25s")
        script.add_segment(pseg, tname)
        track_last_end[tname] = st + dur_us
        if tname == "画中画_左" or kw == "央美呢":
            sfx_events.append((st, sfx_p, 0.42))
        pip_count += 1
    print(f"[pip] added {pip_count} proof PiP cards")

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

    # 12. Save draft + inject verified local font paths & meta info
    script.save()
    patch_draft_fonts_and_meta(draft_dir, NEW_DRAFT_NAME, total_tl_us)
    print(f"[done] JianYing draft saved to: {draft_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
