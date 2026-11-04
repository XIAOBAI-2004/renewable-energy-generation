# optimal-dispatch：运行与展示

本文件夹可单独复制或提交，不需要 MATLAB，也不依赖“coordinated-control”文件夹。

## 最方便的运行方式

1. 安装 Python 3.12。
2. 直接双击 `run.bat`（Windows）或 `run.command`（macOS）。首次运行自动建立本模块 `.venv` 并安装缺少的依赖，需要联网，请等待终端提示完成。
3. 以后仍双击同一文件：自动使用本模块独立环境计算五场景、十方案，算完打开 `index.html`。无需先手动执行“安装依赖”。

默认缓存 `/temp`；若不可写，终端会让你输入一次可写缓存目录的绝对路径，选择保存在本机 `local_settings.json`。Windows 可使用 `C:\temp`。依赖安装后，算例计算和展示均可离线完成。

## 命令行方式

在本文件夹中打开终端：
```sh
python run.py setup
python run.py run
```
macOS 将 `python` 换为 `python3.12`。也可追加 `--cache-dir "可写缓存目录绝对路径"`。运行入口始终使用本文件夹的 `.venv`，缺少依赖时自动补装，不会回退到缺少软件包的系统 Python。若 Python 3.12 安装在自定义位置，可用 `--python "Python3.12可执行文件完整路径"` 指定。

## 直接展示与测试

- 双击 `index.html`：立即查看已保存results，无需 Python，也不重新计算。
- 展示顺序：正常日的柔性负荷移时 → 储能 SOC → 两方案代价 → 高负荷/低风速与组合压力的供能边界。完整指标见 `results/summary.csv`。
- `python run.py tests`：运行四项测试。
- 终端出现 `COMPLETED: 5 scenarios, 10 schedules, all physical checks passed.` 表示计算完成。

核心代码 `dispatch.py`，测试 `test_dispatch.py`，依赖见 `requirements.txt`（含 CVXPY、PySCIPOpt/SCIP）。`results/` 含输入 CSV、逐时results、汇总、figures和 MAT 接口。重新计算覆盖同名results；浏览器已打开时请刷新页面。

输入为合成教学场景；小时级调度尚未闭环接入秒级控制。MAT 接口仅为数据交换准备。首次下载依赖失败时可换可用的软件源重试。双击脚本用于 Windows/macOS，Windows 尚未实机验证。

依赖安装默认使用已验证可下载的清华 PyPI 镜像；可通过 `run.py setup --index-url https://pypi.org/simple` 改用官方软件源。
