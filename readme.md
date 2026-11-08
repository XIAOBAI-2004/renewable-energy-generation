# ZJU-Course · Renewable Energy Generation and Control / 新能源发电与控制

[简体中文](#中文) | [English](#english)

## 中文

浙江大学《新能源发电与控制》课程项目，涵盖风电、光伏与储能的交流孤岛协同控制和优化调度。

### 课程考察要求

以下要求整理自[课程考核要求原图](docs/assessment-requirements.png)。

> **考核重点为多源协同，交流端协同是关键加分项。**

- **考核形式**：Simulink 仿真、论文报告与 PPT 汇报。
- **系统构建**：构建多源协同孤岛运行系统，包含交流并网光伏（5 MW，功率因数 0.9）、风电（5 MW）和储能。
- **协同方式**：可选择交流端或直流端协同。直流端协同的起评分低 10 分。
- **提交与汇报**：自拟题目，提交 Word 文档，并进行 5 分钟的 PPT 汇报。
- **评分关注点**：难度、新意（说明已有工作及本项目的区别）、理论分析、仿真或实验，以及报告的详实程度。
- **课程安排**：第 7 次课答疑并解答作业问题，已准备好的同学也可参加考察。第 8 次课安排考察。

### 仓库内容

| 路径 | 内容 |
| --- | --- |
| [coordinated-control](coordinated-control/README.md) | MATLAB/Simulink 风光储交流孤岛协同控制模型、控制代码及三组对照仿真结果 |
| [optimal-dispatch](optimal-dispatch/README.md) | Python 小时级优化调度、五类教学场景、两种调度方案及结果 |
| [docs/assessment-requirements.png](docs/assessment-requirements.png) | 课程考核要求原图 |

仓库的目录和文件采用英文命名，模块说明以中文为主。结果目录收录 CSV、MAT、图表和历史日志。虚拟环境、系统和编译缓存、本机路径配置均排除在版本管理之外。

### 快速使用

**查看已有结果**。下载仓库后，在浏览器中打开以下文件即可离线查看，无需重新仿真。

- `coordinated-control/index.html`
- `optimal-dispatch/index.html`

**协同控制**。需要 MATLAB R2025a、Simulink、Simscape 和 Simscape Electrical（含 Specialized Power Systems 和 `powergui`）。在 MATLAB 中切换到 `coordinated-control` 目录并运行以下命令。

```matlab
start_demo
```

主模型为 `WindPVStorage_AC_Island.slx`，核心控制器为 `course_controller.m`。统计与绘图方法见[协同控制模块说明](coordinated-control/README.md)。

**优化调度**。安装 Python 3.12，进入 `optimal-dispatch` 目录并运行以下命令。

```sh
python3.12 run.py run
```

首次运行会自动创建环境并安装依赖，需要联网。也可在 macOS 上使用 `run.command`，或在 Windows 上使用 `run.bat`。运行已有测试的命令如下。

```sh
python3.12 run.py tests
```

临时文件默认存放在 `/temp`。若该目录不可写，请按提示指定其他可写的绝对路径。重新运行会覆盖同名结果。

### 项目范围与限制

- 调度输入为合成教学场景。小时级调度尚未与秒级 Simulink 控制形成闭环，MAT 文件用于为数据交换做准备。
- 仓库收录代码、模型及已有结果。课程 Word 论文和 PPT 汇报文件未随仓库上传。
- 控制模块的瞬态最低电压尚未完成仿真步长收敛验证。验证记录见各模块的 `validation-notes.txt`。
- 原项目已在搭载 Apple Silicon 的 macOS 环境中使用 MATLAB R2025a 和 Python 3.12 验证。其他平台和版本的适配情况见各模块说明。

## English

A Zhejiang University course project on renewable energy generation and control. It covers coordinated control and optimal dispatch for an islanded AC system with wind power, solar photovoltaics (PV), and energy storage.

### Course Assessment

These requirements are based on the [original course assessment sheet](docs/assessment-requirements.png).

> **The assessment emphasizes coordination among multiple energy sources. AC-side coordination is a key opportunity to earn extra points.**

- **Format** — Simulink simulation, a written report, and a PowerPoint presentation.
- **System design** — Build a coordinated multi-source islanded system with AC-connected PV (5 MW at a power factor of 0.9), wind generation (5 MW), and energy storage.
- **Coordination approach** — Use AC-side or DC-side coordination. The starting score for DC-side coordination is 10 points lower.
- **Submission and presentation** — Choose your own project title, submit a Word document, and give a five-minute PowerPoint presentation.
- **Grading criteria** — Difficulty, originality (explain related work and how your project differs), theoretical analysis, simulation or experiments, and the level of detail in the report.
- **Schedule** — Session 7 covers questions and homework. Students who are ready may also complete their assessment then. The scheduled assessment takes place in session 8.

### Repository Contents

| Path | Contents |
| --- | --- |
| [coordinated-control](coordinated-control/README.md) | MATLAB/Simulink model and control code for coordinated operation of the islanded wind–PV–storage AC system, with results from three comparison simulations |
| [optimal-dispatch](optimal-dispatch/README.md) | Python implementation of hourly optimal dispatch, with five teaching scenarios and results for two dispatch schemes |
| [docs/assessment-requirements.png](docs/assessment-requirements.png) | Original course assessment sheet |

Files and directories use English names, and the module documentation is primarily in Chinese. The results directories contain CSV and MAT files, plots, and historical logs. Version control excludes virtual environments, system and build caches, and machine-specific path settings.

### Quick Start

**View existing results.** After downloading the repository, open the following files in a browser to view the results offline without rerunning the simulations.

- `coordinated-control/index.html`
- `optimal-dispatch/index.html`

**Coordinated control.** This module requires MATLAB R2025a, Simulink, Simscape, and Simscape Electrical (including Specialized Power Systems and `powergui`). In MATLAB, switch to the `coordinated-control` directory and run the following command.

```matlab
start_demo
```

The main model is `WindPVStorage_AC_Island.slx` and the core controller is `course_controller.m`. See the [coordinated control README](coordinated-control/README.md) for statistics and plotting instructions.

**Optimal dispatch.** Install Python 3.12, switch to the `optimal-dispatch` directory, and run the following command.

```sh
python3.12 run.py run
```

The first run creates an environment and installs dependencies automatically, so it requires an internet connection. You can also use `run.command` on macOS or `run.bat` on Windows. To run the existing tests, use the following command.

```sh
python3.12 run.py tests
```

Temporary files default to `/temp`. If that directory is unwritable, follow the prompt to specify another writable absolute path. Rerunning overwrites results with the same filenames.

### Scope and Limitations

- Dispatch inputs are synthetic teaching scenarios. The hourly dispatch and the second-scale Simulink controller have yet to be integrated into a closed loop. The MAT files support preparation for data exchange.
- The repository contains code, models, and existing results. The course report (Word) and presentation (PowerPoint) are outside the scope of this upload.
- Time-step convergence for the minimum transient voltage in the control module remains unverified. See each module’s `validation-notes.txt` for the existing validation records.
- The original project was verified on macOS with Apple Silicon using MATLAB R2025a and Python 3.12. See the module documentation for compatibility details on other platforms and versions.
