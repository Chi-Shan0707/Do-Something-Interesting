from pathlib import Path
import pandas as pd
import numpy as np
import calculate_pairs


def load_traits(path: Path):
    df = pd.read_csv(str(path), dtype=str).fillna('')
    # convert numeric-ish columns
    for c in df.columns:
        if c.endswith('_code') or c.endswith('_count') or c.endswith('_score') or c.endswith('_quality'):
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df


def build_matrix(df: pd.DataFrame):
    n = len(df)
    # prefer survey_id for row/column labels; fall back to person_id
    df = df.reset_index(drop=True)
    if 'survey_id' in df.columns and df['survey_id'].notna().any():
        ids = df['survey_id'].astype(str).tolist()
    else:
        ids = df['person_id'].astype(str).tolist() if 'person_id' in df.columns else [str(i) for i in range(n)]
    mat = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            if i == j:
                mat[i, j] = 1.0
            else:
                mat[i, j] = calculate_pairs.compute_similarity(i, j, df)
    mat_df = pd.DataFrame(mat, index=ids, columns=ids)
    # ensure square numeric-only CSV and hide index/column name
    mat_df.index.name = ''
    mat_df.columns.name = ''
    return mat_df


if __name__ == '__main__':
    base = Path(__file__).resolve().parent
    trait_path = base.joinpath('trait.csv')
    if not trait_path.exists():
        raise FileNotFoundError('trait.csv not found - run preprocess.py first')
    df = load_traits(trait_path)
    mat_df = build_matrix(df)
    out = base.joinpath('matrix.csv')
    # write pure numeric square matrix (rows and cols are survey_id)
    mat_df.to_csv(str(out), float_format='%.6f')
    print(f'Wrote trait matrix to {out}')
