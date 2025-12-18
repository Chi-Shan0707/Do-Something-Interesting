# 分组与匹配工具 — Group/

此目录包含将问卷数据清洗、计算两两相似度并按相似度贪心分组的若干脚本。下面给出每个主要脚本的简短说明与典型使用顺序。

主要脚本一览
- `preprocess.py`：读取原始 CSV（默认 `test.csv`），做字段探测与清洗，将问卷的原始答案和紧凑的数值特征（单选编码、部分多选 one-hot、`philosophy` 分数与类型、`q11_quality` 等）输出为 `trait.csv`。
- `calculate_pairs.py`：包含 `compute_similarity(i, j, df)`。按问题层面的规则（单选比较、多选 Jaccard、文本回退、philosophy 接近度等）计算两人匹配度。
- `make_matrix.py`：载入 `trait.csv`，对每对被试调用 `calculate_pairs.compute_similarity`，生成并写出纯数值方阵 `matrix.csv`（行列标签为 `survey_id` 或 `person_id`）。
- `divide_groups.py`：基于 `matrix.csv` 实现贪心分组策略，包含两种方式：`greedy_grouping`（按对排序、可合并/替换）和 `force_grouping_exact(..., group_size=4)`（贪心填充种子以尽力生成每组恰好 4 人，支持最大迭代上限以防死循环）。脚本当前采用 `force_grouping_exact` 为默认入口。


典型工作流程

1. 清洗并导出特征：
```bash
python preprocess.py    # 生成 trait.csv
```
2. 计算相似度矩阵：
```bash
python make_matrix.py   # 生成 matrix.csv
```
3. 生成分组（每组 4 人为默认）：
```bash
python divide_groups.py # 打印/输出分组
```
4. （可选）查看每人 Top-K 匹配：
```bash
python -c "import pandas as pd; import calculate_pairs; df=pd.read_csv('trait.csv'); print(calculate_pairs.find_top_matches(df, top_k=5)[:5])"
```

注意事项与配置
- 若要重现/调试匹配逻辑，主要查看 `calculate_pairs.py` 中的 `compute_similarity`，其含有可调整的权重和回退逻辑。  
- `make_matrix.py` 依赖 `trait.csv` 中的若干 `_code/_count/_score/_quality` 列，请先运行 `preprocess.py` 并确认输出。  
- `divide_groups.py` 提供可配置的 `group_size` 与 `max_iters` 参数；若希望改变“踢出”策略或随机性，可修改文件顶部的随机种子或相应逻辑。  

如果需要我把 README 再精简、加示例输出或补充每个函数的调用样例，我可以继续修改。