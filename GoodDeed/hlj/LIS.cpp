#include <bits/stdc++.h>
using namespace std;

// 二分DP算法：O(n log n)
int lis_binary_dp(const vector<int>& nums) {
    if (nums.empty()) return 0;
    vector<int> tails;
    for (int num : nums) {
        auto it = lower_bound(tails.begin(), tails.end(), num);
        if (it == tails.end()) {
            tails.push_back(num);
        } else {
            *it = num;
        }
    }
    return tails.size();
}

// 线段树类，用于维护最大值
class SegmentTree {
private:
    vector<int> tree;
    int n;
    void build(int node, int start, int end) {
        if (start == end) {
            tree[node] = 0;
            return;
        }
        int mid = (start + end) / 2;
        build(2 * node, start, mid);
        build(2 * node + 1, mid + 1, end);
        tree[node] = max(tree[2 * node], tree[2 * node + 1]);
    }
    void update(int node, int start, int end, int idx, int val) {
        if (start == end) {
            tree[node] = max(tree[node], val);
            return;
        }
        int mid = (start + end) / 2;
        if (idx <= mid) {
            update(2 * node, start, mid, idx, val);
        } else {
            update(2 * node + 1, mid + 1, end, idx, val);
        }
        tree[node] = max(tree[2 * node], tree[2 * node + 1]);
    }
    int query(int node, int start, int end, int l, int r) {
        if (r < start || end < l) return 0;
        if (l <= start && end <= r) return tree[node];
        int mid = (start + end) / 2;
        int p1 = query(2 * node, start, mid, l, r);
        int p2 = query(2 * node + 1, mid + 1, end, l, r);
        return max(p1, p2);
    }
public:
    SegmentTree(int _n) : n(_n), tree(4 * _n) {
        build(1, 1, n);
    }
    void update(int idx, int val) {
        update(1, 1, n, idx, val);
    }
    int query(int l, int r) {
        return query(1, 1, n, l, r);
    }
};

// 线段树算法：O(n log n)
int lis_segment_tree(const vector<int>& nums) {
    if (nums.empty()) return 0;
    // 离散化
    set<int> unique_nums(nums.begin(), nums.end());
    vector<int> sorted_unique(unique_nums.begin(), unique_nums.end());
    map<int, int> rank;
    for (int i = 0; i < sorted_unique.size(); ++i) {
        rank[sorted_unique[i]] = i + 1;
    }
    int max_rank = sorted_unique.size();
    SegmentTree st(max_rank);
    int ans = 0;
    for (int num : nums) {
        int r = rank[num];
        int prev = st.query(1, r - 1);
        int curr = prev + 1;
        st.update(r, curr);
        ans = max(ans, curr);
    }
    return ans;
}

// 树状数组类，用于维护最大值
class FenwickTree {
private:
    vector<int> tree;
    int n;
public:
    FenwickTree(int _n) : n(_n), tree(_n + 1, 0) {}
    void update(int idx, int val) {
        while (idx <= n) {
            tree[idx] = max(tree[idx], val);
            idx += idx & -idx;
        }
    }
    int query(int idx) {
        int res = 0;
        while (idx > 0) {
            res = max(res, tree[idx]);
            idx -= idx & -idx;
        }
        return res;
    }
};

// 树状数组算法：O(n log n)
int lis_fenwick_tree(const vector<int>& nums) {
    if (nums.empty()) return 0;
    // 离散化
    set<int> unique_nums(nums.begin(), nums.end());
    vector<int> sorted_unique(unique_nums.begin(), unique_nums.end());
    map<int, int> rank;
    for (int i = 0; i < sorted_unique.size(); ++i) {
        rank[sorted_unique[i]] = i + 1;
    }
    int max_rank = sorted_unique.size();
    FenwickTree ft(max_rank);
    int ans = 0;
    for (int num : nums) {
        int r = rank[num];
        int prev = ft.query(r - 1);
        int curr = prev + 1;
        ft.update(r, curr);
        ans = max(ans, curr);
    }
    return ans;
}

// 朴素DP算法：O(n^2)，作为对比
int lis_dp(const vector<int>& nums) {
    int n = nums.size();
    if (n == 0) return 0;
    vector<int> dp(n, 1);
    for (int i = 1; i < n; ++i) {
        for (int j = 0; j < i; ++j) {
            if (nums[i] > nums[j]) {
                dp[i] = max(dp[i], dp[j] + 1);
            }
        }
    }
    return *max_element(dp.begin(), dp.end());
}

int main() {
    vector<int> nums = {10, 9, 2, 5, 3, 7, 101, 18};
    cout << "Binary DP: " << lis_binary_dp(nums) << endl;
    cout << "Segment Tree: " << lis_segment_tree(nums) << endl;
    cout << "Fenwick Tree: " << lis_fenwick_tree(nums) << endl;
    cout << "DP: " << lis_dp(nums) << endl;
    return 0;
}