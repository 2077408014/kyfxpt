import re
from typing import List, Dict


# 单词行匹配：可选序号 + 英文单词 + 可选音标([]/()///) + 剩余释义
WORD_LINE_PATTERN = re.compile(
    r'^(?:\d+[\.\)、\s]+)?'           # 可选行首序号：1. / 1) / 1、
    r'([a-zA-Z][\w\-\'\.]*)'          # 英文单词
    r'\s*'
    r'(?:\[([^\]]+)\]|\(([^)]+)\)|/([^/]+)/)?'  # 可选音标：[...] / (...) / /.../
    r'\s*'
    r'(.*)$'                           # 剩余：释义（可能含例句）
)

# 词性标记，用于切分释义和例句
POS_MARKERS = ['n.', 'v.', 'adj.', 'adv.', 'prep.', 'conj.', 'pron.', 'art.', 'num.', 'vt.', 'vi.', 'aux.', 'abbr.']


def parse_wordbook_text(text: str) -> List[Dict]:
    """从词书文本中提取单词列表。

    支持常见格式：
      abandon /əˈbændən/ v. 放弃，抛弃
      1. abandon [əˈbændən] v. 放弃
      abandon v. 放弃，抛弃  He abandoned it.
    """
    if not text:
        return []

    words: List[Dict] = []
    seen = set()

    for raw_line in text.split('\n'):
        line = raw_line.strip()
        if not line:
            continue

        m = WORD_LINE_PATTERN.match(line)
        if not m:
            continue

        word = m.group(1)
        phonetic_raw = m.group(2) or m.group(3) or m.group(4) or ''
        rest = (m.group(5) or '').strip()

        # 单词过短或无释义，跳过（可能是标题/页眉）
        if len(word) < 2 or not rest:
            continue

        # 去重（同一词书内）
        key = word.lower()
        if key in seen:
            continue
        seen.add(key)

        # 规范化音标：补上斜杠包裹
        phonetic = phonetic_raw.strip()
        if phonetic and not phonetic.startswith('/'):
            phonetic = f'/{phonetic}/'

        # 尝试分离释义和例句：例句通常是大写开头或包含空格的英文短语，跟在中文释义之后
        meaning, example = _split_meaning_example(rest)

        words.append({
            'word': word,
            'phonetic': phonetic,
            'meaning': meaning,
            'example_sentence': example
        })

    return words


def _split_meaning_example(rest: str) -> tuple:
    """尝试从剩余文本中分离释义和例句。

    策略：
    1. 若文本中有中文，中文部分归释义，其后若紧跟英文句子则为例句。
    2. 若无中文，整体作为释义。
    """
    if not rest:
        return rest, ''

    # 找到最后一个中文字符的位置
    last_cn_idx = -1
    for i, ch in enumerate(rest):
        if '\u4e00' <= ch <= '\u9fff':
            last_cn_idx = i

    if last_cn_idx == -1:
        # 无中文，整体作为释义
        return rest.strip(), ''

    # 中文之后的部分可能是例句
    after_cn = rest[last_cn_idx + 1:].strip()
    meaning = rest[:last_cn_idx + 1].strip()

    # 例句通常以英文开头且较长
    if after_cn and len(after_cn) >= 5 and re.match(r'[A-Z"\']', after_cn):
        return meaning, after_cn

    # 中文后还有内容但不像例句，并入释义
    if after_cn:
        meaning = f'{meaning} {after_cn}'.strip()

    return meaning, ''
