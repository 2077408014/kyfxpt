from datetime import date, timedelta
from typing import Optional

REVIEW_INTERVALS = [1, 3, 7, 14, 30]

MASTERY_LEVELS = ["生疏", "熟悉", "掌握"]
WORD_LEVELS = ["陌生", "认识", "熟悉", "掌握"]
DIFFICULTY_MULTIPLIER = {"简单": 0.8, "中等": 1.0, "困难": 1.5}


def calculate_next_review_date(
    current_level: str,
    difficulty: str,
    review_count: int,
    correct_count: int
):
    multiplier = DIFFICULTY_MULTIPLIER.get(difficulty, 1.0)

    level_index = MASTERY_LEVELS.index(current_level) if current_level in MASTERY_LEVELS else 0

    interval_index = min(review_count - 1, len(REVIEW_INTERVALS) - 1)
    base_interval = REVIEW_INTERVALS[interval_index]

    accuracy = correct_count / review_count if review_count > 0 else 0

    if accuracy >= 0.6:
        level_index = min(level_index + 1, len(MASTERY_LEVELS) - 1)
        base_interval = REVIEW_INTERVALS[min(interval_index + 1, len(REVIEW_INTERVALS) - 1)]
    elif accuracy < 0.4:
        level_index = max(level_index - 1, 0)
        base_interval = REVIEW_INTERVALS[max(interval_index - 1, 0)]

    adjusted_interval = int(base_interval * multiplier)
    next_date = date.today() + timedelta(days=adjusted_interval)

    return next_date, MASTERY_LEVELS[level_index]


def calculate_word_next_review(
    mastery_level: str,
    review_count: int,
    correct_count: int
):
    level_index = WORD_LEVELS.index(mastery_level) if mastery_level in WORD_LEVELS else 0

    interval_index = min(review_count, len(REVIEW_INTERVALS) - 1)
    base_interval = REVIEW_INTERVALS[interval_index]

    if correct_count >= max(review_count * 0.8, 2):
        level_index = min(level_index + 1, len(WORD_LEVELS) - 1)
    elif correct_count < review_count * 0.5:
        level_index = max(level_index - 1, 0)

    if level_index >= len(WORD_LEVELS) - 1:
        next_date = date.today() + timedelta(days=REVIEW_INTERVALS[-1])
    else:
        next_date = date.today() + timedelta(days=base_interval)

    return next_date, WORD_LEVELS[level_index]


def calculate_next_review(mastery_level: str) -> date:
    levels = ["生疏", "认识", "熟悉", "掌握"]
    idx = levels.index(mastery_level) if mastery_level in levels else 0
    interval = REVIEW_INTERVALS[min(idx, len(REVIEW_INTERVALS) - 1)]
    return date.today() + timedelta(days=interval)