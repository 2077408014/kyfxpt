import re
from typing import List, Dict


POS_MARKERS = ['n.', 'v.', 'adj.', 'adv.', 'prep.', 'conj.', 'pron.', 'art.', 'num.',
               'vt.', 'vi.', 'aux.', 'abbr.', 'a.', 'ad.', 'pro.', 'pro', 'int.']
POS_MARKERS_SORTED = sorted(POS_MARKERS, key=len, reverse=True)


def _has_chinese(text: str) -> bool:
    return any('\u4e00' <= c <= '\u9fff' for c in text)


def _group_entries(text: str) -> str:
    """每3行一组合并成完整词条行"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    grouped = []
    for i in range(0, len(lines) - 2, 3):
        grouped.append(' '.join(lines[i:i + 3]))
    return '\n'.join(grouped)


def _split_entry(line: str) -> tuple:
    """将合并行拆分为 (word, phonetic, meaning)"""
    parts = line.split(None, 1)
    if len(parts) < 2:
        return (line, '', '')
    word = parts[0]
    rest = parts[1]

    split_at = len(rest)
    for i in range(len(rest)):
        for marker in POS_MARKERS_SORTED:
            if rest[i:].startswith(marker):
                after = i + len(marker)
                if after >= len(rest) or rest[after] == ' ' or '\u4e00' <= rest[after] <= '\u9fff':
                    split_at = i
                    break
        if split_at < len(rest):
            break

    phonetic = rest[:split_at].strip()
    meaning = rest[split_at:].strip()
    return (word, phonetic, meaning)


def parse_wordbook_text(text: str) -> List[Dict]:
    if not text:
        return []

    text = _group_entries(text)

    words: List[Dict] = []
    seen = set()

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue

        word, phonetic, meaning = _split_entry(line)

        if len(word) < 2 or not meaning:
            continue
        if not _has_chinese(meaning):
            continue

        key = word.lower()
        if key in seen:
            continue
        seen.add(key)

        if phonetic and not phonetic.startswith('/'):
            phonetic = f'/{phonetic}/'

        words.append({
            'word': word,
            'phonetic': phonetic,
            'meaning': meaning,
            'example_sentence': ''
        })

    return words
