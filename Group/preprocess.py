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
    # Use Python's `re.split` to split on multiple separators (commas, semicolons, newlines).
    # We convert to string to be defensive against numeric/missing input and strip whitespace.
    return [x.strip() for x in re.split(SEPARATORS_RE, str(s)) if x.strip()]


def detect_columns(df: pd.DataFrame):
    """Detect important columns: survey id, email, timestamp, and q4..q15 columns."""
    col_map = {}
    for c in df.columns:
        # lowercase/strip once for lightweight heuristics over headers
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
        # 10: other skills / optional free-text
        if cs.startswith('10') or '其他技能' in lc or '选填' in lc:
            col_map['q10'] = c
        # 11: self-reported proficiency / 熟练度
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
    # normalize strings and treat empty as missing: operate vectorized with pandas Series
    s = series.fillna('').astype(str).str.strip()
    # `pd.Categorical` produces a stable integer code per category (codes -1..K-1)
    # using categorical is faster and more memory-efficient than manual mapping.
    cats = pd.Categorical(s.replace('', np.nan))
    codes = cats.codes  # -1 denotes NaN/missing
    # map -1 -> 0 (missing), else +1 so categories map to 1..K (compact representation)
    codes = np.where(codes == -1, 0, codes + 1).astype(int)
    categories = list(pd.Series(cats.categories).astype(str))
    return codes, categories


def encode_multi_choice(series: pd.Series):
    """Use MultiLabelBinarizer to produce one-hot binary columns for multi-select options.
    Returns (df_mlb, classes)
    """
    # Convert each cell into a list of selected choices.
    # `MultiLabelBinarizer` vectorizes multi-select into a binary indicator matrix (one-hot per choice).
    lists = series.apply(split_multi)
    import inspect
    sig = inspect.signature(MultiLabelBinarizer)
    mlb_params = {}
    # Some sklearn versions use `sparse_output`; keep compatibility by inspecting signature.
    if 'sparse_output' in sig.parameters:
        mlb_params['sparse_output'] = False
    mlb = MultiLabelBinarizer(**mlb_params)
    if len(series) == 0:
        return pd.DataFrame(index=series.index), []
    try:
        mat = mlb.fit_transform(lists)
    except Exception:
        return pd.DataFrame(index=series.index), []
    # prefix generated columns with the original series name to maintain traceability
    cols = [f"{series.name}_{c}" for c in mlb.classes_]
    # Build a DataFrame from the binary matrix; cast to int for downstream numeric ops
    df_mlb = pd.DataFrame(mat, columns=cols, index=series.index).astype(int)
    return df_mlb, list(mlb.classes_)


def score_philosophy(s12: str, s13: str, s14: str):
    # normalize to lowercase strings for simple keyword heuristics
    s12 = (s12 or '').lower()
    s13 = (s13 or '').lower()
    s14 = (s14 or '').lower()
    sc = 0
    if '反思' in s13 :
        sc+=2
    elif '情绪化' in s13:
        sc+=1
    if '战略' in s14 :
        sc+=2
    else :
        sc+=1
        # if traits['q6_code']==0 and '死' in s14:
        #     sc+=1
    if '作' in s12 :
        t=3
    elif '主导' in s12 :
        t=2
    else :
        t=1

    return sc, t


def load_and_clean(path: Path):
    # Read CSV into pandas DataFrame. Using dtype=str avoids unwanted type coercion.
    df = pd.read_csv(str(path), dtype=str)
    # cleanse header whitespace and normalize missing values
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

    # process questions 4..11: create `_raw` trace columns and compact numeric features
    # NOTE: per spec, q7 and q9 are multi-select (one-hot via MultiLabelBinarizer), others are single-choice
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
            # multi-select: one binary indicator column per option (0/1). This keeps sparse categorical info.
            df_mlb, classes = encode_multi_choice(df[col])
            if not df_mlb.empty:
                # sanitize and append
                df_mlb.columns = [c.replace(' ', '_').replace('/', '_') for c in df_mlb.columns]
                # also add a count of selections as a compact numeric feature
                df_mlb[f'{key}_count'] = df_mlb.sum(axis=1)
                feature_frames.append(df_mlb)
        elif key in ('q10',):
            continue
            # # q10: question for 'other skills' or free-text answers.
            # # Keep the raw text and try to parse it as multi-select (one-hot) like q7/q9.
            # traits[raw_col] = df[col].astype(str)
            # df_mlb, classes = encode_multi_choice(df[col])
            # if not df_mlb.empty:
            #     df_mlb.columns = [c.replace(' ', '_').replace('/', '_') for c in df_mlb.columns]
            #     df_mlb[f'{key}_count'] = df_mlb.sum(axis=1)
            #     feature_frames.append(df_mlb)
        else:
            # single-choice: encode as compact integer codes (0=missing, 1..K categories)
            # Using integer codes rather than one-hot keeps feature dimensionality small.
            codes, categories = encode_single_choice(df[col])
            # store the integer codes as a single-column DataFrame for concatenation later
            df_codes = pd.DataFrame({f'{key}_code': codes}, index=df.index)
            feature_frames.append(df_codes)

    # process philosophy (q12,q13,q14) -> score and type
    q12_col = col_map.get('q12')
    q13_col = col_map.get('q13')
    q14_col = col_map.get('q14')
    ph_scores = []
    ph_types = []
    q12_list = []
    q13_list = []
    q14_list = []
    # iterate rows to compute philosophy scores. `iterrows()` is acceptable for small-to-moderate data sizes.
    for idx, row in df.iterrows():
        s12 = row[q12_col] if q12_col else ''
        s13 = row[q13_col] if q13_col else ''
        s14 = row[q14_col] if q14_col else ''
        sc, t = score_philosophy(s12, s13, s14)
        ph_scores.append(sc)
        ph_types.append(t)
        # also keep individual raw answers for q12/q13/q14 to simplify downstream lookups
        q12_list.append(str(s12))
        q13_list.append(str(s13))
        q14_list.append(str(s14))
    # write philosophy fields and numeric code
    traits['philosophy_score'] = ph_scores
    traits['philosophy_type'] = ph_types
    # expose q12/q13/q14 raw answers as explicit columns for easier access
    traits['q12_raw'] = q12_list
    traits['q13_raw'] = q13_list
    traits['q14_raw'] = q14_list

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
    # combine numeric feature frames (one-hot and codes) into the `traits` DataFrame
    if feature_frames:
        # concat along columns (axis=1). `reindex` ensures row alignment by original index.
        feat_all = pd.concat(feature_frames, axis=1)
        feat_all = feat_all.reindex(traits.index)
        traits = pd.concat([traits.reset_index(drop=True), feat_all.reset_index(drop=True)], axis=1)

    # add q11 quality score
    # derive a simple heuristic `q11_quality` score from free-text `q10_raw` (per your request)
    if 'q10_raw' in traits.columns:
        q11_qualities = []
        for raw in traits['q10_raw']:
            raw = str(raw).strip()
            if not raw or raw in ['无', '🈚️', '？无', '选填']:
                q11_qualities.append(0)
                continue
            score = 0
            if any(k in raw for k in ('Python', 'Pytorch', 'C++', 'Java')):
                score += 1.25
            if any(k in raw for k in ('项目', '论文', '比赛', '实习')):
                score += 2.0
            if any(k in raw for k in ('LaTeX', 'Stata', 'MATLAB', 'SQL')):
                score += 0.5
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
    # Create a more concise export: keep identifiers, compact numeric features,
    # one-hot indicator columns, some raw text fields useful for human review,
    # and philosophy summary fields. This reduces the CSV width compared to
    # exporting every intermediate `_raw` column.
    cols = []
    # basic identifiers
    for c in ('survey_id', 'person_id', 'email'):
        if c in traits.columns:
            cols.append(c)

    # compact numeric feature columns (codes, counts, scores, quality)
    cols += [c for c in traits.columns if c.endswith('_code') or c.endswith('_quality')]

    # keep some raw text fields that are useful for manual inspection
    for c in ('q10_raw', 'q12_raw', 'q13_raw', 'q14_raw', 'q15_raw'):
        if c in traits.columns and c not in cols:
            cols.append(c)

    # philosophy summary fields — only export compact summary (score and type)
    for c in ('philosophy_score', 'philosophy_type'):
        if c in traits.columns and c not in cols:
            cols.append(c)

    # # include one-hot indicator columns produced by MultiLabelBinarizer: they typically
    # # have an underscore in the name but are not `_raw`/`_code`/`_count` etc.
    # onehot_candidates = [c for c in traits.columns if ('_' in c and not c.endswith('_raw') and not c.endswith('_code') and not c.endswith('_count') and not c.endswith('_score') and not c.endswith('_quality') and not c.startswith('philosophy'))]
    # for c in onehot_candidates:
    #     if c not in cols:
    #         cols.append(c)

    # fall back: if cols is empty for some reason, export full traits
    if not cols:
        export_df = traits
    else:
        # preserve original row order
        export_df = traits.loc[:, [c for c in cols if c in traits.columns]]

    export_df.to_csv(str(out_path), index=False)
    print(f'Exported concise trait file: {out_path} (columns: {len(export_df.columns)})')


if __name__ == '__main__':
    base = Path(__file__).resolve().parent
    csv_path = base.joinpath('test.csv')
    out = base.joinpath('trait.csv')
    traits, col_map = load_and_clean(csv_path)
    export_traits(traits, out)
