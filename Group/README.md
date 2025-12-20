# 分组与匹配工具 — Group/

此目录包含将问卷数据清洗、计算两两相似度并按相似度贪心分组的若干脚本。下面给出每个主要脚本的简短说明与典型使用顺序。

主要脚本一览
- `preprocess.py`：读取原始 CSV（默认 `test.csv`），做字段探测与清洗，将问卷的原始答案和紧凑的数值特征（单选编码、部分多选 one-hot、`philosophy` 分数与类型、`q11_quality` 等）输出为 `trait.csv`。
- `calculate_pairs.py`：包含 `compute(i, j, df)`。按问题层面的规则（单选比较、多选 Jaccard、文本回退、philosophy 接近度等）计算两人匹配度。
- `make_matrix.py`：载入 `trait.csv`，对每对被试调用 `calculate_pairs.compute`，生成并写出纯数值方阵 `matrix.csv`（行列标签为 `survey_id` 或 `person_id`）。
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
python -c "import pandas as pd; import calculate_pairs; df=pd.read_csv('trait.csv'); 
```

注意事项与配置
- 若要重现/调试匹配逻辑，主要查看 `calculate_pairs.py` 中的 `compute`，其含有可调整的权重和回退逻辑。  
- `make_matrix.py` 依赖 `trait.csv` 中的若干 `_code/_count/_score/_quality` 列，请先运行 `preprocess.py` 并确认输出。  
- `divide_groups.py` 提供可配置的 `group_size` 与 `max_iters` 参数；若希望改变“踢出”策略或随机性，可修改文件顶部的随机种子或相应逻辑。  

如果需要我把 README 再精简、加示例输出或补充每个函数的调用样例，我可以继续修改。


# 打分系统
`calculate_pairs.py` 
1. “能否参加”，“赛道”，“目标”，“作品期待”：追求越相似性，所以选项相同得分更高
```
if same:score+=x

```
2. 在“面对问题”的角色细分

- "面对问题”时候的角色：追求差异化，不同得分会高
``` 
if type different: score+=x
```
- “面对问题”时候的行为：追求两者选择相近（对于不同行为定义效益分数，希望效益分数相近），所以越相近分越高
```
score += (x-abs(delta))
```
3. “工具”：希望有重合，但也有可以有些多样，以此定义加分
```
score += (size(A∪B)/SIZE(A∩B))*x+size(A∪B)*y
```
4. “能力”：对于水平差不多高的，得分更高
```
score += (x-abs(delta))
```
# 贪心算法
'make_pairs.py'
1. 很不好的贪心
2. 将所有人两两间的score算出
3. 将所有两两组合按照score排序
4. 将人看成顶点；从高到低，针对每一对pair，先去尝试连一条边，使两个顶点（及其所在的连通块）变成连通的，再去检查这个大的连通块的大小,若人数<=4人，则继续，若人数>4人,则随机踢掉一个人，直到32个人全被划入8个4人小组。
