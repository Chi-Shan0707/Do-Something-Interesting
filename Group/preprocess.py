import re
import pandas as pd
import numpy as np
from pathlib import Path

SEPARATORS_RE = r"[;,，|\n]+"

email_re = re.compile(r"^[A-Za-z0-9._%+-]+@(?:m\.)?fudan\.edu\.cn$")


def split_multi(s):
    if pd.isna(s):
        return []
    if isinstance(s, (list, tuple)):
        return list(s)
    return [x.strip() for x in re.split(SEPARATORS_RE, str(s)) if x.strip()]


def load_and_clean(path: Path):
    df = pd.read_csv(str(path), dtype=str)
    df = df.rename(columns=lambda c: c.strip())
    df = df.fillna("")

    col_map = {}
    for c in df.columns:
        lc = c.lower()
        if "邮" in lc or "email" in lc:
            col_map['email'] = c
        if "年级" in lc or "专业" in lc:
            col_map['grade_major'] = c
        if c.strip().startswith('06') or '目标' in lc or '首要' in lc:
            col_map['goal'] = c
        if c.strip().startswith('07') or '赛道' in lc:
            col_map['tracks'] = c
        if c.strip().startswith('08') or '掌控' in lc:
            col_map['role'] = c
        if c.strip().startswith('09') or '熟悉' in lc or '技能' in lc:
            col_map['skills'] = c
        if '问卷' in lc or '编号' in lc or c.strip().lower().startswith('id') or '序号' in lc:
            col_map['survey'] = col_map.get('survey', c)
        if '学号' in lc or 'student' in lc or '学籍' in lc:
            col_map['student_id'] = c

    if 'survey' in col_map:
        df['survey_id'] = df[col_map['survey']].astype(str).str.strip()
    else:
        df['survey_id'] = (df.index + 1).astype(str)
    if 'student_id' in col_map:
        df['student_id'] = df[col_map['student_id']].astype(str).str.strip()
    else:
        df['student_id'] = ''
    if 'email' in col_map:
        df['email'] = df[col_map['email']].astype(str).str.strip()
    else:
        df['email'] = ''
    df['person_id'] = df['survey_id'].fillna('').astype(str) + '---' + df['student_id'].fillna('').astype(str) + '---' + df['email'].fillna('').astype(str)

    if 'email' in col_map:
        df['email_valid'] = df[col_map['email']].str.strip().apply(lambda s: bool(email_re.match(s)))
    else:
        df['email_valid'] = False

    for key in ('tracks', 'role', 'skills'):
        if key in col_map:
            df[f'{key}_list'] = df[col_map[key]].apply(split_multi)
        else:
            df[f'{key}_list'] = [[] for _ in range(len(df))]

    if 'goal' in col_map:
        df['goal_choice'] = df[col_map['goal']].str.strip()
    else:
        df['goal_choice'] = ''

    # 简化版 philosophy 打分（与原脚本保持一致）
    def score_q12(s: str) -> int:
        s = (s or '').lower()
        if '主导' in s or '主导者' in s:
            return 2
        if '分析' in s or '分析者' in s:
            return 1
        return 0

    def score_q13(s: str) -> int:
        s = (s or '').lower()
        if '内归因' in s or '反思' in s:
            return 1
        return 0

    def score_q14(s: str) -> int:
        s = (s or '').lower()
        if '死磕' in s or '不睡' in s:
            return 2
        if '收缩' in s or '砍' in s:
            return 1
        return 0

    def score_q15(s: str) -> int:
        s = (s or '').lower()
        if '实用' in s:
            return 1
        return 0

    # 尝试抓取原问卷中可能的 Q12-Q15 列名
    q12_col = col_map.get('q12')
    q13_col = col_map.get('q13')
    q14_col = col_map.get('q14')
    q15_col = col_map.get('q15')

    scores = []
    labels = []
    for idx, row in df.iterrows():
        s12 = row[q12_col] if q12_col else ''
        s13 = row[q13_col] if q13_col else ''
        s14 = row[q14_col] if q14_col else ''
        s15 = row[q15_col] if q15_col else ''
        sc = score_q12(s12) + score_q13(s13) + score_q14(s14) + score_q15(s15)
        if sc >= 5:
            lbl = '强驱动型'
        elif sc == 4:
            lbl = '务实且有主见'
        elif 2 <= sc <= 3:
            lbl = '平衡型'
        else:
            lbl = '协作/体验优先'
        scores.append(sc)
        labels.append(lbl)

    df['philosophy'] = labels
    df['philosophy_score'] = scores

    return df, col_map


def export_person_summary(df, out_path: Path):
    export = pd.DataFrame()
    export['person_id'] = df.get('person_id', (df.index + 1).astype(str))
    export['survey_id'] = df.get('survey_id', (df.index + 1).astype(str))
    export['email'] = df.get('email', '')
    export['goal'] = df.get('goal_choice', '')
    for key in ('tracks_list', 'role_list', 'skills_list'):
        if key in df.columns:
            export[key.replace('_list','')] = df[key].apply(lambda items: '|'.join(items) if items else '')
        else:
            export[key.replace('_list','')] = ''
    export['philosophy'] = df.get('philosophy', '')

    export.to_csv(str(out_path), index=False)
    print(f'Exported choices per person: {out_path}')


if __name__ == '__main__':
    base = Path(__file__).resolve().parent
    csv_path = base.joinpath('test.csv')
    out = base.joinpath('choices_per_person.csv')
    df, col_map = load_and_clean(csv_path)
    export_person_summary(df, out)
