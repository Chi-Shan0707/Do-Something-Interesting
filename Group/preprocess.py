import re
import pandas as pd
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder
from pathlib import Path

SEPARATORS_RE = r"[;,，|\n]+"

email_re = re.compile(r"^[A-Za-z0-9._%+-]+@(?:m\.)?fudan\.edu\.cn$")


def split_multi(s):
    if pd.isna(s) or s is None:
        return []
    if isinstance(s, (list, tuple)):
        return list(s)
    return [x.strip() for x in re.split(SEPARATORS_RE, str(s)) if x.strip()]


def detect_columns(df: pd.DataFrame):
    """Detect important columns: survey id, email, timestamp, and q4..q15 columns."""
    col_map = {}
    for c in df.columns:
        lc = c.lower()
        cs = c.strip()
        if '邮' in lc or 'email' in lc:
            col_map['email'] = c
        if '问卷' in lc or '编号' in lc or cs.lower().startswith('id') or '序号' in lc:
            col_map['survey'] = c
        if '学号' in lc or 'student' in lc or '学籍' in lc:
            col_map['student_id'] = c
        if '时间' in lc or '时间戳' in lc or '答题时间' in lc or '提交时间' in lc:
            col_map['timestamp'] = c

        # map q4..q15 by leading number if present, otherwise by keywords
        if cs.startswith('04') or cs.startswith('4') or '能否' in lc or '参加' in lc:
            col_map['q4'] = c
        if cs.startswith('05') or cs.startswith('5') or '朋友' in lc or '组队' in lc:
            col_map['q5'] = c
        if cs.startswith('06') or cs.startswith('6') or '首要目标' in lc or '目标' in lc:
            col_map['q6'] = c
        if cs.startswith('07') or cs.startswith('7') or '赛道' in lc:
            col_map['q7'] = c
        if cs.startswith('08') or cs.startswith('8') or '掌控' in lc or '部分' in lc:
            col_map['q8'] = c
        if cs.startswith('09') or cs.startswith('9') or '熟悉' in lc or '技能' in lc:
            col_map['q9'] = c
        if cs.startswith('10') or cs.startswith('11') or cs.startswith('10') or '其他技能' in lc or '选填' in lc:
            # try to detect 10 and 11; since header may vary, capture both heuristically
            if 'q10' not in col_map and (cs.startswith('10') or '其他技能' in lc or '选填' in lc):
                col_map['q10'] = c
            elif 'q11' not in col_map:
                col_map['q11'] = c
        if cs.startswith('11') or '熟练度' in lc or '开发熟练度' in lc:
            col_map['q11'] = c
        if cs.startswith('12') or '分歧' in lc or '时间紧迫' in lc:
            col_map['q12'] = c
        if cs.startswith('13') or '进展' in lc or '反应' in lc:
            col_map['q13'] = c
        if cs.startswith('14') or '周六' in lc or 'demo' in lc:
            col_map['q14'] = c
        if cs.startswith('15') or '更想做' in lc or '作品' in lc:
            col_map['q15'] = c

    return col_map


def encode_single_choice(series: pd.Series):
    """
    Encode a single-choice categorical column into compact integer codes.

    Why integer codes:
    - One integer per respondent is more compact than many one-hot columns.
    - Keeps the feature space small for single-choice questions.
    - Missing responses map to 0, valid categories map to 1..K.

    Returns (codes, categories) where `codes` is a numpy array of ints
    and `categories` is the ordered list of category strings corresponding
    to codes 1..K.
    """
    # normalize strings and treat empty as missing
    s = series.fillna('').astype(str).str.strip()
    # use pandas Categorical to get stable category ordering
    cats = pd.Categorical(s.replace('', np.nan))
    codes = cats.codes  # -1 denotes NaN/missing
    # map -1 -> 0 (missing), else +1 so categories map to 1..K
    codes = np.where(codes == -1, 0, codes + 1).astype(int)
    categories = list(pd.Series(cats.categories).astype(str))
    return codes, categories


def encode_multi_choice(series: pd.Series):
    """Use MultiLabelBinarizer to produce one-hot binary columns for multi-select options.
    Returns (df_mlb, classes)
    """
    lists = series.apply(split_multi)
    import inspect
    sig = inspect.signature(MultiLabelBinarizer)
    mlb_params = {}
    if 'sparse_output' in sig.parameters:
        mlb_params['sparse_output'] = False
    mlb = MultiLabelBinarizer(**mlb_params)
    if len(series) == 0:
        return pd.DataFrame(index=series.index), []
    try:
        mat = mlb.fit_transform(lists)
    except Exception:
        return pd.DataFrame(index=series.index), []
    cols = [f"{series.name}_{c}" for c in mlb.classes_]
    df_mlb = pd.DataFrame(mat, columns=cols, index=series.index).astype(int)
    return df_mlb, list(mlb.classes_)


def score_philosophy(s12: str, s13: str, s14: str):
    s12 = (s12 or '').lower()
    s13 = (s13 or '').lower()
    s14 = (s14 or '').lower()
    sc = 0
    if '主导' in s12 or '主导者' in s12:
        sc += 2
    elif '分析' in s12 or '分析者' in s12:
        sc += 1
    if '内归因' in s13 or '反思' in s13:
        sc += 1
    if '死磕' in s14 or '不睡' in s14:
        sc += 2
    elif '收缩' in s14 or '砍' in s14:
        sc += 1
    # map to types
    if sc >= 5:
        t = 'strong_driven'
    elif sc == 4:
        t = 'practical_leader'
    elif 2 <= sc <= 3:
        t = 'balanced'
    else:
        t = 'collaborative'
    return sc, t


def load_and_clean(path: Path):
    df = pd.read_csv(str(path), dtype=str)
    df = df.rename(columns=lambda c: c.strip())
    df = df.fillna('')

    col_map = detect_columns(df)

    # ensure survey id/email/student
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

    # collect q4..q11 raw and codes
    traits = pd.DataFrame()
    traits['survey_id'] = df['survey_id']
    traits['person_id'] = df['person_id']
    traits['email'] = df['email']
    # timestamp if available
    if 'timestamp' in col_map:
        traits['timestamp'] = df[col_map['timestamp']]

    # process questions 4..11: generate raw columns and numeric feature columns
    # NOTE: per spec, only q7 and q9 are multi-select; others are single-choice.
    feature_frames = []  # list of DataFrames with numeric feature columns to be concatenated
    for q in range(4, 12):
        key = f'q{q}'
        col = col_map.get(key)
        raw_col = f'{key}_raw'
        # create a raw-text column for traceability
        traits[raw_col] = ''
        if not col:
            # missing question column -> leave raw empty and continue
            continue
        # copy raw text answers
        traits[raw_col] = df[col].astype(str)

        # q7 and q9 are multi-select (keep as binary indicator columns)
        if key in ('q7', 'q9'):
            # multi-select: one binary column per option (0/1)
            df_mlb, classes = encode_multi_choice(df[col])
            if not df_mlb.empty:
                # sanitize and append
                df_mlb.columns = [c.replace(' ', '_').replace('/', '_') for c in df_mlb.columns]
                # also add a count of selections as a compact numeric feature
                df_mlb[f'{key}_count'] = df_mlb.sum(axis=1)
                feature_frames.append(df_mlb)
        else:
            # single-choice: encode as compact integer codes (0=missing, 1..K categories)
            codes, categories = encode_single_choice(df[col])
            # store the integer codes as a single-column DataFrame
            df_codes = pd.DataFrame({f'{key}_code': codes}, index=df.index)
            feature_frames.append(df_codes)

    # process philosophy (q12,q13,q14) -> score and type
    q12_col = col_map.get('q12')
    q13_col = col_map.get('q13')
    q14_col = col_map.get('q14')
    ph_scores = []
    ph_types = []
    ph_raw = []
    for idx, row in df.iterrows():
        s12 = row[q12_col] if q12_col else ''
        s13 = row[q13_col] if q13_col else ''
        s14 = row[q14_col] if q14_col else ''
        sc, t = score_philosophy(s12, s13, s14)
        ph_scores.append(sc)
        ph_types.append(t)
        ph_raw.append('|'.join([str(s12), str(s13), str(s14)]))
    # write philosophy fields and numeric code
    traits['philosophy_score'] = ph_scores
    traits['philosophy_type'] = ph_types
    unique_types = sorted(set(ph_types))
    type_map = {t: i + 1 for i, t in enumerate(unique_types)}
    traits['philosophy_type_code'] = [type_map[t] for t in ph_types]
    traits['philosophy_raw'] = ph_raw

    # process question 15 (single-choice: encode as integer code)
    q15_col = col_map.get('q15')
    if q15_col:
        traits['q15_raw'] = df[q15_col].astype(str)
        # single-choice: use compact integer codes
        codes, categories = encode_single_choice(df[q15_col])
        df_codes = pd.DataFrame({f'q15_code': codes}, index=df.index)
        feature_frames.append(df_codes)
    else:
        traits['q15_raw'] = ''

    # combine numeric feature frames (if any) into traits
    if feature_frames:
        feat_all = pd.concat(feature_frames, axis=1)
        feat_all = feat_all.reindex(traits.index)
        traits = pd.concat([traits.reset_index(drop=True), feat_all.reset_index(drop=True)], axis=1)

    # add q11 quality score
    if 'q11_raw' in traits.columns:
        q11_qualities = []
        for raw in traits['q11_raw']:
            raw = raw.strip()
            if not raw or raw in ['无', '🈚️', '？无', '选填']:
                q11_qualities.append(0)
            else:
                score = 0
                if 'Python' in raw or 'Pytorch' in raw or 'C++' in raw or 'Java' in raw:
                    score += 2
                if '项目' in raw or '论文' in raw or '比赛' in raw or '实习' in raw:
                    score += 1
                if 'LaTeX' in raw or 'Stata' in raw or 'MATLAB' in raw or 'SQL' in raw:
                    score += 1
                q11_qualities.append(min(score, 3))
        traits['q11_quality'] = q11_qualities

    # sort by numeric survey id if possible
    def try_int(x):
        try:
            return int(x)
        except Exception:
            return x
    traits['__sort_key'] = traits['survey_id'].apply(try_int)
    traits = traits.sort_values('__sort_key')
    traits = traits.drop(columns=['__sort_key'])

    return traits, col_map


def export_traits(traits: pd.DataFrame, out_path: Path):
    traits.to_csv(str(out_path), index=False)
    print(f'Exported trait file: {out_path}')


if __name__ == '__main__':
    base = Path(__file__).resolve().parent
    csv_path = base.joinpath('test.csv')
    out = base.joinpath('trait.csv')
    traits, col_map = load_and_clean(csv_path)
    export_traits(traits, out)
