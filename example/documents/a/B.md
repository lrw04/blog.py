---
title: B
modification: 2050/1/1 12:00
---

# 2020/10/23 模拟赛

## A

给出 $n$ 个正整数 $a_1,a_2,\cdots,a_n$, 求使得 $\prod_{i=l}^ra_i$ 是完全平方数的 $l\le r$ 的个数。$n,a_i\le10^5$.

对所有数中的质因数考虑其次数，只有奇偶性对是否为完全平方数有影响。给所有出现过奇数次的质因数分配编号，就可以把每个数变成不损失信息的 0-1 串。

对这些串求出前缀和，并求出插入之前有多少相同的并累加即为所求。总时间复杂度为 $\mathrm{O}(n\log\max_i a_i + p\log p)$ ($p$ 为质因数个数).

代码如下：

```c++
#include <bitset>
#include <cstring>
#include <functional>
#include <iostream>
#include <unordered_map>
#include <vector>
using namespace std;
using ll = long long;

const int MAXN = 1e5 + 20, MAXV = 2e3;
int n, a[MAXN], minp[MAXN], cc = 0;
unordered_map<int, int> cnt[MAXN], pnum;
vector<int> prime;
bitset<MAXV> s;
unordered_map<size_t, int> cint;

void sieve(int n) {
  memset(minp, 0, sizeof minp);
  for (int i = 2; i <= n; i++) {
    if (!minp[i]) {
      minp[i] = i;
      prime.push_back(i);
    }
    for (int p : prime) {
      if (minp[i] < p || p > n / i) break;
      minp[i * p] = p;
    }
  }
}

int main() {
  sieve(1e5);
  ios::sync_with_stdio(false);
  cin.tie(nullptr);

  cin >> n;
  for (int i = 1; i <= n; i++) cin >> a[i];
  for (int i = 1; i <= n; i++) {
    int t = a[i];
    while (t != 1) {
      cnt[i][minp[t]] ^= 1;
      t /= minp[t];
    }
  }
  for (int i = 1; i <= n; i++)
    for (auto [p, c] : cnt[i])
      if (c && !pnum.count(p)) pnum[p] = cc++;

  hash<bitset<MAXV>> hash_fn;
  cint[hash_fn(s)]++;
  ll ans = 0;
  cerr << s << endl;
  for (int i = 1; i <= n; i++) {
    // [?, i]
    for (auto [p, c] : cnt[i])
      if (c) s.flip(pnum[p]);
    size_t cur_hash = hash_fn(s);
    ans += cint[cur_hash];
    cint[cur_hash]++;
  }
  cout << ans << endl;
}
```

## B

维护一个正整数集，支持插入和取出第 $k$ 大的数。$k$ 在操作之间 不变。操作数 $n\le2\times10^5$.

对顶堆可以做到，但 Treap 也能通过。总时间复杂度 $\mathrm{O}(n\log n)$.

代码如下：

```c++
#include <cstdlib>
#include <iostream>
using namespace std;

#define MAXN 200020

class Treap {
  int l[MAXN], r[MAXN], val[MAXN], dup[MAXN], rnd[MAXN], siz[MAXN];
  int s, ans, rt;
  void pushup(int i) { siz[i] = siz[l[i]] + siz[r[i]] + dup[i]; }
  void lrot(int& k) {
    int t = r[k];
    r[k] = l[t];
    l[t] = k;
    siz[t] = siz[k];
    pushup(k);
    k = t;
  }
  void rrot(int& k) {
    int t = l[k];
    l[k] = r[t];
    r[t] = k;
    siz[t] = siz[k];
    pushup(k);
    k = t;
  }
  void insert(int& k, int x) {
    if (!k) {
      s++;
      k = s;
      siz[k] = 1;
      dup[k] = 1;
      val[k] = x;
      rnd[k] = rand();
      return;
    }
    siz[k]++;
    if (val[k] == x) {
      dup[k]++;
    } else if (val[k] < x) {
      insert(r[k], x);
      if (rnd[r[k]] < rnd[k]) lrot(k);
    } else {
      insert(l[k], x);
      if (rnd[l[k]] < rnd[k]) rrot(k);
    }
  }
  void del(int& k, int x) {
    if (!k) return;
    if (val[k] == x) {
      if (dup[k] > 1) {
        dup[k]--;
        siz[k]--;
        return;
      }
      if (!l[k] || !r[k])
        k = l[k] + r[k];
      else if (rnd[l[k]] < rnd[r[k]]) {
        rrot(k);
        del(k, x);
      } else {
        lrot(k);
        del(k, x);
      }
    } else if (val[k] < x) {
      siz[k]--;
      del(r[k], x);
    } else {
      siz[k]--;
      del(l[k], x);
    }
  }
  int rank(int k, int x) {
    if (!k) return 0;
    if (val[k] == x)
      return siz[l[k]] + 1;
    else if (x > val[k])
      return siz[l[k]] + dup[k] + rank(r[k], x);
    else
      return rank(l[k], x);
  }
  int num(int k, int x) {
    if (!k) return 0;
    if (x <= siz[l[k]])
      return num(l[k], x);
    else if (x > siz[l[k]] + dup[k])
      return num(r[k], x - siz[l[k]] - dup[k]);
    else
      return val[k];
  }
  void pre(int k, int x) {
    if (!k) return;
    if (val[k] < x) {
      ans = k;
      pre(r[k], x);
    } else {
      pre(l[k], x);
    }
  }
  void nxt(int k, int x) {
    if (!k) return;
    if (val[k] > x) {
      ans = k;
      nxt(l[k], x);
    } else {
      nxt(r[k], x);
    }
  }

 public:
  void insert(int x) { insert(rt, x); }
  void del(int x) { del(rt, x); }
  int rank(int x) { return rank(rt, x); }
  int num(int x) { return num(rt, x); }
  int pre(int x) {
    ans = 0;
    pre(rt, x);
    return val[ans];
  }
  int nxt(int x) {
    ans = 0;
    nxt(rt, x);
    return val[ans];
  }
  int size() { return siz[rt]; }
};
Treap t;

int main() {
  ios::sync_with_stdio(false);
  cin.tie(nullptr);

  srand(39845617);
  int n, k, p, lastans = 0;
  cin >> n >> k >> p;
  while (n--) {
    int op, x;
    cin >> op;
    if (op == 1) {
      cin >> x;
      if (p) x ^= lastans;
      t.insert(x);
    } else if (op == 2) {
      lastans = t.num(t.size() + 1 - k);
      t.del(lastans);
      cout << lastans << "\n";
    }
  }
  return 0;
}

```

## C

给出一张有向图，其中每条边的权值可能是 0 或 1. 以 $t_0=0$,
$t_{2n}=t_n$ 和 $t_{2n+1}=1-t_n$ 定义 $(t_i)$，第 $i$ 步只能走过一条权值为 $t_{i-1}$ 的边。求走最大步数能够达到的节点的距离（步数），如果大于 $10^{18}$ 视为不存在。$n:=|V|\le500$.

我也不知道怎么想出来的，总之最后是想出来了。

我们只关心若干步后的连通性，将其转化为两个邻接矩阵相乘（乘积和加和转化为按位与和按位或，这里相乘的矩阵可以是边权为 0 或 1 的子图的邻接矩阵），乘积中的元素。我们只要能求出 $e_1\prod_{i=1}^qG_{t_{q-i}}$ 即可. 

注意到 $t$ 的自相似性，我们可以倍增求出整 $2^k$ 步之内两种邻接矩阵，然后倍增求出答案，尝试乘上更大的指数。总时间复杂度 $\mathrm{O}(n^3\log\text{maxans})$. 注意到矩阵中有大量的 0 元素，我们在计算乘积时特殊判断这样的元素。

在实现上，因为是 0-1 矩阵，有人可能想到用 `std::bitset` 存储每一位，但这里对元素的访问并不能对齐，因此会比其他类型更慢。

另外，因为答案只取决于矩阵乘积的第一行，我们用 $e_1$ 左乘这个矩阵，把求得答案的时间复杂度除 $n$.

```c++
#include <cstring>
#include <iostream>
using namespace std;
using ll = long long;

const int MAXN = 500;
int n, m;

struct Matrix {
  char d[MAXN][MAXN];
  Matrix() { memset(d, 0, sizeof d); }
  char& operator()(int i, int j) { return d[i][j]; }
  Matrix operator*(Matrix& rhs) {
    Matrix ans;
    for (int i = 0; i < n; i++)
      for (int k = 0; k < n; k++)
        if ((*this)(i, k))
          for (int j = 0; j < n; j++) ans(i, j) |= rhs(k, j);
    return ans;
  }
};

struct Vector {
  char row[MAXN];
  Vector() { memset(row, 0, sizeof row); }
  char& operator()(int i) { return row[i]; }
  bool any() {
    for (int i = 0; i < n; i++)
      if (row[i]) return true;
    return false;
  }
  Vector operator*(Matrix& b) {
    Vector ans;
    for (int i = 0; i < n; i++)
      for (int j = 0; j < n; j++) ans(i) |= (*this)(j)&b(j, i);
    return ans;
  }
};

Matrix t[65][2];

int main() {
  cin >> n >> m;
  for (int i = 0; i < m; i++) {
    int u, v, w;
    cin >> u >> v >> w;
    u--;
    v--;
    t[0][w](u, v) = 1;
  }
  for (int i = 1; i < 61; i++) {
    t[i][0] = t[i - 1][0] * t[i - 1][1];
    t[i][1] = t[i - 1][1] * t[i - 1][0];
  }
  ll ans = 0;
  int s = 0;
  Vector v;
  v(0) = 1;
  for (int i = 61; i >= 0; i--) {
    auto w = v * t[i][s];
    if (w.any()) {
      ans |= 1ll << i;
      v = w;
      s ^= 1;
    }
  }
  cout << (ans > 1e18 ? -1 : ans) << endl;
}

```
