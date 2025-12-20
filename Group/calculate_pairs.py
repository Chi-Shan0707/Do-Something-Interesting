import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import MultiLabelBinarizer
import re

SEPARATOR = r"[;,，|\n]+"


def parse_multi(s: str):
    if pd.isna(s) or s == '':
        return []
    return [x.strip() for x in re.split(SEPARATOR, str(s)) if x.strip()]


def compute(i: int, j: int, df: pd.DataFrame):
    """
    Compute similarity score between person i and j based on survey responses.
    Higher score means better match.
    """
    # `df` is expected to be the traits DataFrame produced by `preprocess.py`.
    # We operate with integer-location indexing (`iloc`) because callers pass indices (0-based positions).
    score = 0.0
    
    # 04: 参加意愿 - 相同高分
    if df.iloc[i]['q4_code'] == 1 and df.iloc[j]['q4_code'] == 1:  # 都确定
        score += 4.0
    elif df.iloc[i]['q4_code'] == 2 and df.iloc[j]['q4_code'] == 2:  # 都大概率
        score += 2.0
    elif df.iloc[i]['q4_code'] + df.iloc[j]['q4_code'] == 3 :
        score += 1.5  # 不同也给点分
    else :
        score +=0.5
    
    # 05: 组队意愿 - 都接受匹配高分
    if df.iloc[i]['q5_code'] == 1 and df.iloc[j]['q5_code'] == 1:  # 都完全接受
        score += 2.0
    elif df.iloc[i]['q5_code'] == df.iloc[j]['q5_code']:
        score += 1.0
    else:
        score += 0.0  # 有队伍的和无队伍的低分
    
    # 06: 目标 - 相同高分
    if df.iloc[i]['q6_code'] == df.iloc[j]['q6_code']:
        score += 3.0
    else:
        score += 1.5  # 不同目标也可能互补
    
    # 07: multi-select tracks — prefer raw `q7_raw` Jaccard similarity when available
    if 'q7_raw' in df.columns:
        set_i = set(parse_multi(df.at[i, 'q7_raw']))
        set_j = set(parse_multi(df.at[j, 'q7_raw']))
        union = set_i | set_j
        if union:
            jaccard = len(set_i & set_j) / len(union)
            score += jaccard * 2.2
    else:
        # fallback to legacy one-hot columns (long header names)
        q7_cols = [c for c in df.columns if c.startswith('8.你最感兴趣的赛道是？:') or c.startswith('q7_')]
        common_tracks = sum(1 for c in q7_cols if df.iloc[i][c] == 1 and df.iloc[j][c] == 1)
        total_tracks = sum(1 for c in q7_cols if df.iloc[i][c] == 1 or df.iloc[j][c] == 1)
        if total_tracks > 0:
            jaccard = common_tracks / total_tracks
            score += jaccard * 2.0
    
    # 08: 掌控部分 
    if df.iloc[i]['q8_code'] == df.iloc[j]['q8_code']:
        score += 1.5
    else:
        score += 2.0  # 不同部分可能互补
    
    # 09: skills (multi-select) — prefer raw `q9_raw` Jaccard similarity when available
    if 'q9_raw' in df.columns:
        set_i = set(parse_multi(df.at[i, 'q9_raw']))
        set_j = set(parse_multi(df.at[j, 'q9_raw']))
        union = set_i | set_j
        if union:
            jaccard = len(set_i & set_j) / len(union)
            score += jaccard * 1.5+len(union)*1.5
    else:
        q9_cols = [c for c in df.columns if c.startswith('11.其他技能（选填）_') or c.startswith('q9_')]
        common_skills = sum(1 for c in q9_cols if df.iloc[i][c] == 1 and df.iloc[j][c] == 1)
        total_skills = sum(1 for c in q9_cols if df.iloc[i][c] == 1 or df.iloc[j][c] == 1)
        if total_skills > 0:
            jaccard = common_skills / total_skills
            score += jaccard * 2.0
    
    
    # q11_quality - 相似质量高分
    # q11_quality is a heuristic numeric score (0..3) derived from free text; closer quality -> higher score
    diff_quality = abs(df.iloc[i]['q11_quality'] - df.iloc[j]['q11_quality'])
    score += max(0, 4.0 - diff_quality * 0.3)
    
    # helper to safely get raw/text fields; fallback to philosophy_raw parts if available
    # helper to retrieve raw/text answers. Use `df.at` for fast scalar access by label.
    def _get_raw(idx, col):
        return str(df.at[idx, col]) if col in df.columns else ''

    # 12: 分歧处理 - 相同风格高分
    # comparing verbatim raw text answers can be noisy but is simple and explainable here
    v_i = _get_raw(i, 'q12_raw')
    v_j = _get_raw(j, 'q12_raw')
    score += 1.0 if v_i == v_j and v_i != '' else 0.5

    # 13: 反应方式 - 相同高分
    v_i = _get_raw(i, 'q13_raw')
    v_j = _get_raw(j, 'q13_raw')
    score += 1.0 if v_i == v_j and v_i != '' else 0.5

    # 14: 压力处理 - 相同高分
    v_i = _get_raw(i, 'q14_raw')
    v_j = _get_raw(j, 'q14_raw')
    score += 1.0 if v_i == v_j and v_i != '' else 0.5
    
    # 15: 作品偏好 - 相同高分
    # q15_code is a compact integer encoding for single-choice Q15
    if df.iloc[i]['q15_code'] == df.iloc[j]['q15_code']:
        score += 1.0
    else:
        score += 0.5
    
    # 哲学类型 - 相同类型高分
    # philosophy_type is a categorical label produced by `score_philosophy`.
    # Matching types should increase compatibility; different types might also complement each other.
    if df.iloc[i]['philosophy_type'] == df.iloc[j]['philosophy_type']:
        score += 3.0
    else:
        score += 2.0
    
    # 哲学分数 - 接近高分
    diff_phil = abs(df.iloc[i]['philosophy_score'] - df.iloc[j]['philosophy_score'])
    score += max(0, 1.0 - diff_phil * 0.1)  # 相差0 1.0, 相差5 0.5
    
    return score
