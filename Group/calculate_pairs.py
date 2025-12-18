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


def compute_similarity(i: int, j: int, df: pd.DataFrame):
    """
    Compute similarity score between person i and j based on survey responses.
    Higher score means better match.
    """
    score = 0.0
    
    # 04: 参加意愿 - 相同高分
    if df.iloc[i]['q4_code'] == df.iloc[j]['q4_code']:
        score += 2.0  # 都确定参加最高
    elif df.iloc[i]['q4_code'] == 1 and df.iloc[j]['q4_code'] == 1:  # 都确定
        score += 2.0
    elif df.iloc[i]['q4_code'] == 2 and df.iloc[j]['q4_code'] == 2:  # 都大概率
        score += 1.5
    else:
        score += 0.5  # 不同也给点分
    
    # 05: 组队意愿 - 都接受匹配高分
    if df.iloc[i]['q5_code'] == 1 and df.iloc[j]['q5_code'] == 1:  # 都完全接受
        score += 2.0
    elif df.iloc[i]['q5_code'] == df.iloc[j]['q5_code']:
        score += 1.0
    else:
        score += 0.0  # 有队伍的和无队伍的低分
    
    # 06: 目标 - 相同高分
    if df.iloc[i]['q6_code'] == df.iloc[j]['q6_code']:
        score += 1.5
    else:
        score += 0.5  # 不同目标也可能互补
    
    # 07: 赛道 - 多选，共同选择越多分越高
    q7_cols = [c for c in df.columns if c.startswith('8.你最感兴趣的赛道是？:')]
    common_tracks = sum(1 for c in q7_cols if df.iloc[i][c] == 1 and df.iloc[j][c] == 1)
    total_tracks = sum(1 for c in q7_cols if df.iloc[i][c] == 1 or df.iloc[j][c] == 1)
    if total_tracks > 0:
        jaccard = common_tracks / total_tracks
        score += jaccard * 2.0  # 最大 2.0
    
    # 08: 掌控部分 - 相同高分，互补也行
    if df.iloc[i]['q8_code'] == df.iloc[j]['q8_code']:
        score += 1.5
    else:
        score += 1.0  # 不同部分可能互补
    
    # 09: 技能 - 多选，共同技能越多分越高
    q9_cols = [c for c in df.columns if c.startswith('11.其他技能（选填）_')]
    common_skills = sum(1 for c in q9_cols if df.iloc[i][c] == 1 and df.iloc[j][c] == 1)
    total_skills = sum(1 for c in q9_cols if df.iloc[i][c] == 1 or df.iloc[j][c] == 1)
    if total_skills > 0:
        jaccard = common_skills / total_skills
        score += jaccard * 2.0  # 最大 2.0
    
    # 11: AI开发熟练度 - 相似水平高分
    diff_level = abs(df.iloc[i]['q11_code'] - df.iloc[j]['q11_code'])
    score += max(0, 1.0 - diff_level * 0.3)  # 相同 1.0, 相差1 0.7, 相差2 0.4, 相差3 0.1
    
    # q11_quality - 相似质量高分
    diff_quality = abs(df.iloc[i]['q11_quality'] - df.iloc[j]['q11_quality'])
    score += max(0, 1.0 - diff_quality * 0.3)
    
    # helper to safely get raw/text fields; fallback to philosophy_raw parts if available
    def _get_raw(idx, col):
        if col in df.columns:
            return str(df.at[idx, col])
        # fallback: philosophy_raw contains q12|q13|q14 in preprocess
        if 'philosophy_raw' in df.columns and col in ('q12_raw', 'q13_raw', 'q14_raw'):
            parts = str(df.at[idx, 'philosophy_raw']).split('|')
            mapping = {'q12_raw': 0, 'q13_raw': 1, 'q14_raw': 2}
            p = mapping[col]
            if len(parts) > p:
                return parts[p]
        return ''

    # 12: 分歧处理 - 相同风格高分
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
    if df.iloc[i]['q15_code'] == df.iloc[j]['q15_code']:
        score += 1.0
    else:
        score += 0.5
    
    # 哲学类型 - 相同类型高分
    if df.iloc[i]['philosophy_type'] == df.iloc[j]['philosophy_type']:
        score += 1.5
    else:
        score += 0.5
    
    # 哲学分数 - 接近高分
    diff_phil = abs(df.iloc[i]['philosophy_score'] - df.iloc[j]['philosophy_score'])
    score += max(0, 1.0 - diff_phil * 0.1)  # 相差0 1.0, 相差5 0.5
    
    return score
