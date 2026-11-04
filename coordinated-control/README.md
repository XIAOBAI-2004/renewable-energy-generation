# coordinated-control：运行与展示

本文件夹可单独复制或提交，无需“optimal-dispatch”文件夹。

## 最方便的运行方式（不需要 Python）

1. 安装 MATLAB R2025a、Simulink、Simscape、Simscape Electrical，包含 Specialized Power Systems / powergui。
2. MATLAB 当前文件夹切换到本文件夹，输入：
   ```matlab
   start_demo
   ```
3. 自动运行三组 48 s 对照，弹出有功、频率、电压和 SOC 曲线，并生成 `results/control_overview.png` 与 `results/demo_metrics.json`。

缓存默认 `/temp`。若不可创建，MATLAB 桌面会弹框让你选择可写目录；本 MATLAB 会话内无需重复设置。命令行模式可显式设置 `COURSE_TEMP_DIR`，或调用 `start_demo('run','可写缓存目录的绝对路径')`。

## 直接展示（无需重算）

- 双击 `index.html`：浏览器离线展示已保存曲线，无需 MATLAB 或 Python。
- MATLAB 输入 `show_results`：用包内 CSV 打开四幅对照图。
- 讲解顺序：模型源荷连接 → 储能补偿缺额 → 二次控制恢复频率 → 电压和 SOC。

## 其他入口

- 已安装 Python 时，也可双击 `run.bat`（Windows）或 `run.command`（macOS），仿真后自动打开展示页。
- `run_all`：运行三组仿真并重做原详细统计、六张results图；此额外功能需要先用 Python 3.12 执行 `python run.py setup`（或双击“安装依赖”）。macOS 可用 `python3.12`。
- `build_course_model` 会重建并覆盖 SLX；日常演示不需要调用。

核心算法 `course_controller.m`；主模型 `WindPVStorage_AC_Island.slx`；仿真入口 `run_course_case.m`。已有原始results均保留。运行覆盖同名数据，PPT 不自动更新。总览和 demo_metrics 随 start_demo 更新；原详细 PNG、metrics.json 和汇总 CSV 随 run_all 更新。瞬态最低电压尚未随步长收敛。其他 MATLAB 版本、Windows/Linux 尚未实机验证。

依赖安装默认使用已验证可下载的清华 PyPI 镜像；可通过 `run.py setup --index-url https://pypi.org/simple` 改用官方软件源。
