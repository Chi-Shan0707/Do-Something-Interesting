import csv
from pathlib import Path
import numpy as np
import random


def load_matrix(path: Path):
    """Load matrix.csv (square) and return ids list and numpy matrix."""
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return [], np.zeros((0, 0))
    header = rows[0]
    ids = header[1:]
    n = len(ids)
    mat = np.zeros((n, n), dtype=float)
    for i, row in enumerate(rows[1:1 + n]):
        for j in range(n):
            mat[i, j] = float(row[j + 1])
    return ids, mat


def greedy_grouping(ids, mat, group_size=4):
    """
    Greedy grouping by descending pair scores.

    Strategy:
    - Build list of all pairs (i,j,score), sort by score desc.
    - Iterate pairs, try to form/extend groups as described by user rules.
    - Maintain groups as sets; when conflict (both i and j already in different groups),
      decide by removing the 'least important' member from one group and reassigning.
    - 'Least important' heuristic: for a member x in a group G, compute sum of similarities
      between x and other members of G; lower sum -> less important.
    - Stop when no more groups can be formed and return list of groups (each list of ids).
    """
    n = len(ids)
    # pair list
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((i, j, mat[i, j]))
    pairs.sort(key=lambda x: x[2], reverse=True)

    groups = []  # list of sets of indices
    member_to_group = {}  # idx -> group_idx

    def least_important_member(group_set):
        # return member idx with smallest sum similarity to other members in group
        best_idx = None
        best_score = None
        for x in group_set:
            s = sum(mat[x, y] for y in group_set if y != x)
            if best_score is None or s < best_score:
                best_score = s
                best_idx = x
        return best_idx

    for i, j, score in pairs:
        gi = member_to_group.get(i)
        gj = member_to_group.get(j)

        # neither in group -> make new group with i,j
        if gi is None and gj is None:
            g = {i, j}
            groups.append(g)
            gidx = len(groups) - 1
            member_to_group[i] = gidx
            member_to_group[j] = gidx
            continue

        # one in group -> try to add other if group not full
        if gi is not None and gj is None:
            g = groups[gi]
            if len(g) < group_size:
                g.add(j)
                member_to_group[j] = gi
            else:
                # group full: randomly evict one member and replace if beneficial
                if g:
                    li = random.choice(list(g))
                    sum_j = sum(mat[j, y] for y in g)
                    sum_li = sum(mat[li, y] for y in g if y != li)
                    if sum_j > sum_li:
                        if li in g:
                            g.remove(li)
                        if li in member_to_group:
                            del member_to_group[li]
                        g.add(j)
                        member_to_group[j] = gi
            continue

        if gj is not None and gi is None:
            g = groups[gj]
            if len(g) < group_size:
                g.add(i)
                member_to_group[i] = gj
            else:
                if g:
                    lj = random.choice(list(g))
                    sum_i = sum(mat[i, y] for y in g)
                    sum_lj = sum(mat[lj, y] for y in g if y != lj)
                    if sum_i > sum_lj:
                        if lj in g:
                            g.remove(lj)
                        if lj in member_to_group:
                            del member_to_group[lj]
                        g.add(i)
                        member_to_group[i] = gj
            continue

        # both in groups
        if gi == gj:
            # already same group; maybe need to expand if group not full
            g = groups[gi]
            if len(g) < group_size:
                # nothing to add
                pass
            continue
        # conflict: i in group A, j in group B
        A = groups[gi]
        B = groups[gj]
        # if combined size <= group_size, merge
        if len(A) + len(B) <= group_size:
            # merge B into A
            A.update(B)
            for member in B:
                member_to_group[member] = gi
            # mark B as empty
            groups[gj] = set()
            continue

        # else need to evict randomly from one of the groups to accommodate
        # randomly choose which group to evict from
        evict_from_A = random.choice([True, False])
        if evict_from_A:
            if A:
                la = random.choice(list(A))
                if la in A:
                    A.remove(la)
                if la in member_to_group:
                    del member_to_group[la]
            # try to add j to A if space
            if len(A) < group_size:
                A.add(j)
                member_to_group[j] = gi
            else:
                # otherwise try to add i to B
                if len(B) < group_size:
                    B.add(i)
                    member_to_group[i] = gj
        else:
            if B:
                lb = random.choice(list(B))
                if lb in B:
                    B.remove(lb)
                if lb in member_to_group:
                    del member_to_group[lb]
            if len(B) < group_size:
                B.add(i)
                member_to_group[i] = gj
            else:
                if len(A) < group_size:
                    A.add(j)
                    member_to_group[j] = gi

    # finalize: rebuild groups from authoritative member_to_group mapping
    # This guarantees each person ends up in exactly one group (and only one).
    grouped = {}
    for member_idx, gidx in member_to_group.items():
        grouped.setdefault(gidx, []).append(member_idx)

    result = []
    # convert each gathered group, splitting if it exceeds group_size
    for members in grouped.values():
        members_sorted = sorted(members)
        for k in range(0, len(members_sorted), group_size):
            chunk = members_sorted[k:k + group_size]
            result.append([ids[x] for x in chunk])

    # collect any indices not present in member_to_group (unassigned) and pack them
    assigned = set(member_to_group.keys())
    unassigned_idxs = [i for i in range(n) if i not in assigned]
    for k in range(0, len(unassigned_idxs), group_size):
        chunk = unassigned_idxs[k:k + group_size]
        result.append([ids[x] for x in chunk])

    return result


def force_grouping_exact(ids, mat, group_size=4, max_iters=10_000_000):
    """
    Force groups of exactly `group_size` by repeatedly picking a seed person
    and greedily filling their group with highest-similarity unassigned people.

    The process repeats until all people are assigned or `max_iters` is reached.
    Returns a list of groups (each list of ids). If total number of people is not
    divisible by `group_size`, the final group may be smaller.
    """
    n = len(ids)
    if n == 0:
        return []

    # precompute preference lists for each person
    prefs = [None] * n
    for i in range(n):
        others = list(range(n))
        others.remove(i)
        others.sort(key=lambda j: mat[i, j], reverse=True)
        prefs[i] = others

    unassigned = set(range(n))
    groups = []
    iters = 0

    # pick seed by total similarity to others (descending)
    total_sim = [sum(mat[i, j] for j in range(n) if j != i) for i in range(n)]

    while unassigned and iters < max_iters:
        iters += 1
        # choose highest-total-sim unassigned as seed
        seed = max(unassigned, key=lambda x: total_sim[x])
        unassigned.remove(seed)
        group_idxs = [seed]

        # pick top preferences that are still unassigned
        for cand in prefs[seed]:
            if cand in unassigned:
                group_idxs.append(cand)
                unassigned.remove(cand)
                if len(group_idxs) >= group_size:
                    break

        # if still short, fill with smallest-index unassigned (deterministic)
        if len(group_idxs) < group_size and unassigned:
            for cand in sorted(unassigned):
                group_idxs.append(cand)
                unassigned.remove(cand)
                if len(group_idxs) >= group_size:
                    break

        groups.append([ids[i] for i in group_idxs])

    # if we stopped due to max_iters but still have unassigned, pack the rest
    if unassigned:
        rem = sorted(unassigned)
        for k in range(0, len(rem), group_size):
            chunk = rem[k:k + group_size]
            groups.append([ids[i] for i in chunk])

    return groups


if __name__ == '__main__':
    base = Path(__file__).resolve().parent
    # use the canonical matrix file `matrix.csv` only
    mat_path = base.joinpath('matrix.csv')
    if not mat_path.exists():
        raise FileNotFoundError('matrix.csv not found - run make.py first')
    ids, mat = load_matrix(mat_path)
    groups = force_grouping_exact(ids, mat, group_size=4, max_iters=10_000_000)
    for gi, g in enumerate(groups, start=1):
        print(f'Group {gi}:', g)

