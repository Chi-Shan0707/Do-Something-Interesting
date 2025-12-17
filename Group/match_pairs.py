import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import MultiLabelBinarizer
import re

SEPARATOR = r"\|"


def parse_list_cell(s: str):
    if pd.isna(s) or s == '':
        return []
    if isinstance(s, (list, tuple)):
        return list(s)
    return [x.strip() for x in re.split(SEPARATOR, str(s)) if x.strip()]


def build_feature_matrix_from_export(df: pd.DataFrame):
    # 将 tracks/role/skills 的文本列转换为 list
    for col in ('tracks', 'role', 'skills'):
        if col in df.columns:
            df[f'{col}_list'] = df[col].apply(parse_list_cell)
        else:
            df[f'{col}_list'] = [[] for _ in range(len(df))]

    features = []
    feature_names = []
    mlb = MultiLabelBinarizer(sparse_output=False)
    # 合并三类多选特征
    for key in ('tracks_list', 'role_list', 'skills_list'):
        X = mlb.fit_transform(df[key]) if len(df) > 0 else np.zeros((len(df), 0))
        cols = [f"{key.replace('_list','')}_{v}" for v in mlb.classes_]
        features.append(X)
        feature_names += cols

    # goal 单选
    goal_mlb = MultiLabelBinarizer()
    goal_X = goal_mlb.fit_transform(df['goal'].apply(lambda s: [s] if s else [])) if 'goal' in df.columns else np.zeros((len(df), 0))
    goal_cols = [f"goal_{v}" for v in goal_mlb.classes_] if hasattr(goal_mlb, 'classes_') else []
    features.append(goal_X)
    feature_names += goal_cols

    # philosophy
    if 'philosophy' in df.columns:
        phil_mlb = MultiLabelBinarizer()
        phil_X = phil_mlb.fit_transform(df['philosophy'].apply(lambda s: [s] if s else []))
        phil_cols = [f"philosophy_{v}" for v in phil_mlb.classes_]
        features.append(phil_X)
        feature_names += phil_cols

    X_all = np.hstack(features) if features else np.zeros((len(df), 0))
    return X_all, feature_names


def cosine_sim(a, b):
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def find_top_matches(X: np.ndarray, top_k=3):
    n = X.shape[0]
    results = {}
    for i in range(n):
        sims = []
        for j in range(n):
            if i == j:
                continue
            s = cosine_sim(X[i], X[j])
            sims.append((j, s))
        sims.sort(key=lambda t: t[1], reverse=True)
        results[i] = sims[:top_k]
    return results


def save_matches(df: pd.DataFrame, matches: dict, out_path: Path):
    rows = []
    for i, sims in matches.items():
        me = df.iloc[i]['person_id'] if 'person_id' in df.columns else str(i)
        for rank, (j, score) in enumerate(sims, start=1):
            other = df.iloc[j]['person_id'] if 'person_id' in df.columns else str(j)
            rows.append({'person_id': me, 'rank': rank, 'match_person_id': other, 'score': float(score)})
    out_df = pd.DataFrame(rows)
    out_df.to_csv(str(out_path), index=False)
    print(f'Saved matches to {out_path}')


if __name__ == '__main__':
    base = Path(__file__).resolve().parent
    in_csv = base.joinpath('choices_per_person.csv')
    if not in_csv.exists():
        raise FileNotFoundError(f"Expected {in_csv} to exist. Run preprocess.py first.")
    df = pd.read_csv(str(in_csv), dtype=str).fillna('')
    X, feature_names = build_feature_matrix_from_export(df)
    matches = find_top_matches(X, top_k=5)
    out = base.joinpath('matches_per_person.csv')
    save_matches(df, matches, out)
    # 打印简短结果
    for i, sims in matches.items():
        me = df.iloc[i].get('email') or df.iloc[i].get('person_id') or f'idx_{i}'
        print(f"== 推荐给: {me} ==")
        for j, score in sims:
            other = df.iloc[j].get('email') or df.iloc[j].get('person_id') or f'idx_{j}'
            print(f"  {other}\t相似度={score:.3f}")
        print()
