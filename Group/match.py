import re
import pandas as pd
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer
from pathlib import Path

# 可配置：CSV 路径（相对脚本目录）
CSV_PATH = Path(__file__).resolve().parent.joinpath("test.csv")

SEPARATORS_RE = r"[;,，|\n]+"

email_re = re.compile(r"^[A-Za-z0-9._%+-]+@(?:m\.)?fudan\.edu\.cn$")


def split_multi(s):
    if pd.isna(s):
        return []
    if isinstance(s, (list, tuple)):
        return list(s)
    return [x.strip() for x in re.split(SEPARATORS_RE, str(s)) if x.strip()]


def load_and_clean(path=CSV_PATH):
    df = pd.read_csv(str(path), dtype=str)
    df = df.rename(columns=lambda c: c.strip())
    df = df.fillna("")

    # 基本字段清洗示例（根据实际 CSV 列名调整）
    # 期待列名示例： 姓名, 邮箱, 年级/专业, Q6, Q7, Q8, Q9
    # 尝试寻找包含关键词的列
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
        # 尝试匹配第14-16题（用于生成 philosophy 聚合）
        if c.strip().startswith('12') or '分歧' in lc or '时间紧迫' in lc:
            col_map['q12'] = c
        if c.strip().startswith('13') or '进展' in lc or '反应' in lc:
            col_map['q13'] = c
        if c.strip().startswith('14') or '周六' in lc or 'demo' in lc:
            col_map['q14'] = c
        if c.strip().startswith('15') or '更想做' in lc or '作品' in lc:
            col_map['q15'] = c

        # 尝试匹配问卷编号 / 序号 / 学号 列，以便早期生成 person_id
        if '问卷' in lc or '编号' in lc or c.strip().lower().startswith('id') or '序号' in lc:
            # 优先使用更具体的问卷编号关键词
            col_map['survey'] = col_map.get('survey', c)
        if '学号' in lc or 'student' in lc or '学籍' in lc:
            col_map['student_id'] = c

    # 在此处尽早生成 survey_id / student_id / email 与 person_id（格式：survey---student---email）
    # survey_id 优先使用表内列，否则使用 index+1
    if 'survey' in col_map:
        df['survey_id'] = df[col_map['survey']].astype(str).str.strip()
    else:
        df['survey_id'] = (df.index + 1).astype(str)
    if 'student_id' in col_map:
        df['student_id'] = df[col_map['student_id']].astype(str).str.strip()
    else:
        df['student_id'] = ''
    # 预填 email（若存在）以便组成 person_id
    if 'email' in col_map:
        df['email'] = df[col_map['email']].astype(str).str.strip()
    else:
        df['email'] = ''
    df['person_id'] = df['survey_id'].fillna('').astype(str) + '---' + df['student_id'].fillna('').astype(str) + '---' + df['email'].fillna('').astype(str)

    # 验证邮箱
    if 'email' in col_map:
        df['email_valid'] = df[col_map['email']].str.strip().apply(lambda s: bool(email_re.match(s)))
    else:
        df['email_valid'] = False

    # 切分多选题（tracks/role/skills）
    for key in ('tracks', 'role', 'skills'):
        if key in col_map:
            df[f'{key}_list'] = df[col_map[key]].apply(split_multi)
        else:
            df[f'{key}_list'] = [[] for _ in range(len(df))]

    # 单选题 goal 保持原值
    if 'goal' in col_map:
        df['goal_choice'] = df[col_map['goal']].str.strip()
    else:
        df['goal_choice'] = ''

    # 生成 philosophy 聚合（基于 Q12-Q15 的组合规则）
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
        # 映射为哲学标签（基于总分）
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

    # (已在上方根据列名提前生成 survey_id / student_id / person_id)

    return df, col_map


def print_and_visualize_choices(df, col_map):
    """打印每题选择情况；若安装了 matplotlib，会为每题生成柱状图并保存到脚本目录。"""
    base = Path(__file__).resolve().parent
    questions = [
        ('goal', '单选 - 首要目标'),
        ('tracks', '多选 - 赛道'),
        ('role', '多选 - 掌控部分'),
        ('skills', '多选 - 熟悉的技能/工具'),
        ('philosophy', '聚合 - philosophy')
    ]

    for key, title in questions:
        print(f"-- {title} ({key}) --")
        counts = {}
        if key + '_list' in df.columns:
            for items in df[key + '_list']:
                for it in items:
                    it = it.strip()
                    if not it:
                        continue
                    counts[it] = counts.get(it, 0) + 1
        else:
            # 可能是单列文本
            col = col_map.get(key) if key in col_map else (key if key in df.columns else None)
            if col:
                ser = df[col].astype(str).str.strip().replace('', np.nan)
                vc = ser.value_counts(dropna=True)
                counts = vc.to_dict()

        if not counts:
            print('  (无可统计数据)')
            continue

        # 打印按次数排序的条目
        for k, v in sorted(counts.items(), key=lambda t: -t[1]):
            print(f"  {k}: {v}")

        # 可视化（如果可用）
        try:
            import matplotlib.pyplot as plt
            labels, values = zip(*sorted(counts.items(), key=lambda t: -t[1]))
            plt.figure(figsize=(max(4, len(labels) * 0.6), 3))
            plt.bar(range(len(values)), values)
            plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
            plt.ylabel('count')
            plt.title(title)
            plt.tight_layout()
            out = base.joinpath(f'choices_{key}.png')
            plt.savefig(str(out))
            plt.close()
            print(f'  可视化已保存: {out}')
        except Exception:
            # matplotlib 未安装或其他错误，忽略可视化
            pass


def export_person_summary(df, col_map):
    """按人导出汇总 CSV（每人一行，显示所有关键题的选择）。"""
    base = Path(__file__).resolve().parent
    out = base.joinpath('choices_per_person.csv')
    # 组成要导出的列
    export = pd.DataFrame()
    export['person_id'] = df.get('person_id', (df.index + 1).astype(str))
    export['survey_id'] = df.get('survey_id', (df.index + 1).astype(str))
    export['email'] = df.get('email', '')
    export['goal'] = df.get('goal_choice', '')
    # 将 list 列用 | 拼接
    for key in ('tracks_list', 'role_list', 'skills_list'):
        if key in df.columns:
            export[key.replace('_list','')] = df[key].apply(lambda items: '|'.join(items) if items else '')
        else:
            export[key.replace('_list','')] = ''
    export['philosophy'] = df.get('philosophy', '')

    export.to_csv(str(out), index=False)
    print(f'Person-level summary saved: {out}')


def visualize_person_matrix(df, X, feature_names):
    """把特征矩阵以热图形式保存，行=person, 列=特征（需要 matplotlib）。"""
    base = Path(__file__).resolve().parent
    try:
        import matplotlib.pyplot as plt
        if X.size == 0:
            print('  特征矩阵为空，跳过人-特征热图')
            return
        fig, ax = plt.subplots(figsize=(max(6, len(feature_names) * 0.25), max(4, X.shape[0] * 0.2)))
        im = ax.imshow(X, aspect='auto', cmap='Blues')
        ax.set_yticks(range(len(df)))
        # 使用 person_id 作为行标签（若过长可能会被截断）
        ylabels = df.get('person_id', (df.index + 1).astype(str)).tolist()
        ax.set_yticklabels(ylabels)
        ax.set_xticks(range(len(feature_names)))
        ax.set_xticklabels(feature_names, rotation=90, fontsize=6)
        plt.colorbar(im, ax=ax)
        plt.tight_layout()
        out = base.joinpath('person_feature_matrix.png')
        plt.savefig(str(out), dpi=150)
        plt.close()
        print(f'Person-feature heatmap saved: {out}')
    except Exception:
        print('  matplotlib 未安装或发生错误，无法生成 person-feature 热图')


def visualize_person_answers(df, col_map):
    """为每个人生成一张 PNG，展示该人在每个关键问题上的回答。"""
    base = Path(__file__).resolve().parent
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print('  matplotlib 未安装，跳过每人回答图生成')
        return

    def sanitize(s: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]", "_", s)[:200]

    keys = [
        ('survey_id', '问卷编号'),
        ('student_id', '学号'),
        ('email', '邮箱'),
        ('goal_choice', '首要目标'),
        ('tracks_list', '赛道'),
        ('role_list', '掌控部分'),
        ('skills_list', '熟悉技能'),
        ('philosophy', 'philosophy')
    ]

    for idx, row in df.iterrows():
        pid = row.get('person_id', str(idx + 1))
        lines = []
        for col, title in keys:
            if col.endswith('_list') and col in df.columns:
                val = row[col]
                text = '|'.join(val) if isinstance(val, (list, tuple)) else str(val)
            else:
                text = str(row.get(col, ''))
            lines.append(f"{title}: {text}")

        # 绘制文本图
        h = max(2, 0.4 * len(lines) + 0.5)
        fig = plt.figure(figsize=(6, h))
        plt.axis('off')
        y = 1.0
        for line in lines:
            plt.text(0.01, y, line, fontsize=10, va='top')
            y -= 1.0 / (len(lines) + 1)

        fname = base.joinpath(f"person_answers_{sanitize(pid)}.png")
        plt.tight_layout()
        fig.savefig(str(fname), dpi=150)
        plt.close(fig)
        print(f'  Saved per-person PNG: {fname}')



def build_feature_matrix(df):
    # 对多选列做 one-hot
    mlb = MultiLabelBinarizer(sparse_output=False)
    features = []
    feature_names = []

    for key in ('tracks_list', 'role_list', 'skills_list'):
        X = mlb.fit_transform(df[key])
        cols = [f"{key.replace('_list','')}_{v}" for v in mlb.classes_]
        features.append(X)
        feature_names += cols

    # 对单选 goal 做 one-hot
    goal_mlb = MultiLabelBinarizer()
    goal_X = goal_mlb.fit_transform(df['goal_choice'].apply(lambda s: [s] if s else []))
    goal_cols = [f"goal_{v}" for v in goal_mlb.classes_]
    features.append(goal_X)
    feature_names += goal_cols

    # 将 philosophy 纳入特征（如果存在）
    if 'philosophy' in df.columns:
        phil_mlb = MultiLabelBinarizer()
        phil_X = phil_mlb.fit_transform(df['philosophy'].apply(lambda s: [s] if s else []))
        phil_cols = [f"philosophy_{v}" for v in phil_mlb.classes_]
        features.append(phil_X)
        feature_names += phil_cols

    # 可加上年级/专业等文本特征的简单编码（这里不做复杂 NLP）
    X_all = np.hstack(features) if features else np.zeros((len(df), 0))
    return X_all, feature_names


def cosine_sim(a, b):
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def find_top_matches(df, X, top_k=3):
    n = len(df)
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


if __name__ == '__main__':
    df, col_map = load_and_clean()
    # 打印并可视化每题选择（若安装 matplotlib 则会把图保存到脚本目录）
    print_and_visualize_choices(df, col_map)
    X, feature_names = build_feature_matrix(df)
    # 导出每人摘要并保存人-特征热图
    export_person_summary(df, col_map)
    visualize_person_matrix(df, X, feature_names)
    # 为每个人生成回答摘要图（每人一张PNG）
    visualize_person_answers(df, col_map)
    matches = find_top_matches(df, X, top_k=5)

    # 打印每个人的 top-5 推荐（用邮箱或姓名标识）
    id_col = None
    for c in df.columns:
        if '名' in c:
            id_col = c
            break
    if not id_col and 'email' in col_map:
        id_col = col_map['email']

    for i, sims in matches.items():
        me = df.iloc[i][id_col] if id_col else f"idx_{i}"
        print(f"== 推荐给: {me} ==")
        for j, score in sims:
            other = df.iloc[j][id_col] if id_col else f"idx_{j}"
            print(f"  {other}\t相似度={score:.3f}")
        print()
