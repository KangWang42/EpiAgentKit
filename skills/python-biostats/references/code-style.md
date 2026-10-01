# Python 代码组织与可读性规范

与 R 端 `r-biostats/references/code-style.md` 遵循同样的原则：代码先让研究者看见数据怎样变成分析集、模型和表图；检查放在能拦住错误的位置；函数只用于重复、批处理或复杂算法。项目已有规范时沿用项目规范。以下写法已在 pandas 2.3、statsmodels 0.14 下实跑验证。

## 1 脚本结构

- 顶部集中 `import`，只导入实际使用的包；标准库、第三方、项目内部依次分组。
- 按“数据导入、清洗、分析、导出”分节，用 `# Cleaning ----` 这类注释标记。一次性步骤不包装成函数，不写“先定义全部函数、最后在 `main()` 里依次调用”的形式；命令行工具除外。
- 路径相对项目根，用 `pathlib.Path` 拼接；不写绝对路径，不调用 `os.chdir()`。
- 不留调试 `print()`、注释掉的旧代码或 Notebook 式的逐步对象展示。

## 2 读入与类型

- `pd.read_csv()` 为标识符、分类变量和容易被猜错的列写 `dtype=`，ID 读为 `"string"` 以保留前导零；日期用 `parse_dates=` 或读入后 `pd.to_datetime(..., format=...)` 按实际格式解析。
- 已从数据字典核实的缺失码写进 `na_values=`；不确定时回原始来源核对。
- 读入后紧接一次 `.rename(columns={...})`，把代码中使用的列名统一为英文 `snake_case`；中文原名保留在标签和表图中。已有项目沿用原有列名。

## 3 链式写法作为主线

连续的数据变换写成一条用括号包裹的方法链，每步一行：`.assign()` 新增或改写列（用 `lambda d:` 引用链中当前数据）、`.query()` 或布尔索引筛行、`.merge()` 连接、`.pipe()` 接入自定义步骤。

```python
data_neat = (
    data_raw
    .assign(
        age_group=lambda d: pd.cut(d["age"], bins=[0, 60, np.inf], right=False, labels=["<60", ">=60"]),
        smoking=lambda d: d["smoking"].map({0: "No", 1: "Yes"}).astype("category"),
    )
    .merge(hospital, on="hospital_id", how="left", validate="many_to_one", indicator=True)
)
```

- 不写 `df["x"][mask] = value` 这类链式赋值，改用 `.assign()`、`.loc[mask, "x"] = value` 或 `np.where()` / `np.select()`。
- 不用 `inplace=True`；每步返回新对象，便于放进方法链。
- 分组汇总用 `.groupby(..., observed=True).agg(n=("id", "size"), deaths=("death", "sum"))` 的命名聚合；分类变量分组时显式写 `observed=True`。
- 逐行 `.apply(axis=1)` 和 `iterrows()` 只在确实无法向量化时使用。

## 4 连接的防错

- `.merge()` 写明 `on=`、`how=` 和 `validate=`（`"one_to_one"`、`"many_to_one"` 等），键重复时立即抛出 `MergeError`。
- 需要知道哪些记录没有匹配时加 `indicator=True`，在运行检查中报告 `_merge != "both"` 的行数；每条记录都必须匹配时用 `how="inner"` 前先核对这个数目，不静默丢行。

## 5 批处理

- 多个模型设定或变量写成字典或 DataFrame 参数表，用字典推导或列表推导批量完成，结果用 `pd.concat({name: frame, ...}, names=[...])` 合并成一张带来源列的表。
- 只产生文件的任务直接循环写出，不先收集无用的返回列表。
- 个别元素可能合理失败时，只捕获该调用的具体异常类型并记录失败元素，事后报告；不写裸 `except:` 或 `except Exception: pass`。

## 6 模型结果提取

- statsmodels 用 formula API（`smf.logit`、`smf.poisson`、`smf.ols`），分类变量用 `C(var, Treatment("参照水平"))` 写明参照组。
- 需要稳健标准误时在 `.fit(cov_type="HC0")` 中指定；修正 Poisson 估计 RR 时必须使用稳健方差。
- 系数和区间按名称从 `fit.params`、`fit.conf_int()` 取出，比值类用 `np.exp()` 转换；不按位置索引。
- 关键结果用 `scripts/emit_summary.py` 按固定名称写入 `results/results.yaml`。

## 7 反模式对照

| 不要这样写 | 改为 |
|---|---|
| `df["x"][mask] = v` | `df.loc[mask, "x"] = v` 或 `.assign()` |
| `inplace=True` | 返回新对象，放入方法链 |
| `merge()` 后比较行数 | `validate=` + `indicator=True` |
| `groupby(cat_col)` 不写 `observed` | `groupby(cat_col, observed=True)` |
| `for i in range(len(df))` / `iterrows()` | 向量化运算或 `np.select()` |
| `except: pass` | 捕获具体异常并记录 |
| `fit.params[1]` | `fit.params["C(smoking, Treatment('No'))[T.Yes]"]` |
| 全局 `warnings.filterwarnings("ignore")` | 定位警告原因，只在确认无害的具体调用处窄范围处理 |

## 8 检查

修改后先运行 `python -m py_compile <脚本>`，再实跑。项目环境已有 `ruff` 时运行 `ruff check <脚本>` 和 `ruff format --diff <脚本>` 做只读检查；没有时按本文件人工检查，不自行安装。
