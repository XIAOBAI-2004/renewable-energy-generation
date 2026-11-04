# Renewable Energy Generation and Control

ZJU 新能源发电与控制课程项目：风、光、储多源协同孤岛运行与优化调度。

## 课程考察要求

以下内容根据课程“考核要求”图片整理。

> **重点：多源协同、交流端协同为加分关键，请务必重视。**

- **考核形式：** Simulink 仿真 + 论文报告 + PPT 汇报。
- **系统构建：** 构建多源联合协同孤岛运行系统，包含光伏交流并网（5 MW，功率因数 0.9）、风电（5 MW）、储能三类要素。
- **协同方式：** 要求 AC 端协同或直流端协同；直流端协同起评分低 10 分。
- **汇报提交：** 题目自拟，提交 Word 文档，并做 5 分钟 PPT 汇报。
- **重点考查：** 难度、新意（需讲述已有工作并说明不同）、理论分析、仿真或实验，以及报告是否翔实。
- **课程安排：** 第 7 次课答疑和解答作业问题，准备好的也可以考察；第 8 次课考察。

## 仓库内容

| 目录 | 内容 |
| --- | --- |
| [coordinated-control](coordinated-control/README.md) | MATLAB/Simulink 风光储交流孤岛协同控制模型、控制代码及三组对照仿真结果 |
| [optimal-dispatch](optimal-dispatch/README.md) | Python 小时级优化调度、五类教学场景、两种调度方案及结果 |
| [docs/assessment-requirements.png](docs/assessment-requirements.png) | 课程考察要求原图 |

所有目录和文件均采用英文名称；说明内容保留中文，便于课程阅读。结果目录包含已有 CSV、MAT、图表及历史日志。虚拟环境、系统与编译缓存、本机路径配置不纳入版本管理。

## 快速使用

### 查看已有结果

下载仓库后，用浏览器打开以下文件即可离线查看，无需重新仿真：

- `coordinated-control/index.html`
- `optimal-dispatch/index.html`

### 协同控制

需要 MATLAB R2025a、Simulink、Simscape、Simscape Electrical（含 Specialized Power Systems / powergui）。在 MATLAB 中进入 `coordinated-control` 后运行：

```matlab
start_demo
```

主模型为 `WindPVStorage_AC_Island.slx`，核心控制器为 `course_controller.m`。进一步统计与绘图操作见该模块 README。

### 优化调度

安装 Python 3.12，进入 `optimal-dispatch` 后执行：

```sh
python3.12 run.py run
```

首次运行自动建立环境并安装依赖，需要联网。也可使用 macOS 的 `run.command` 或 Windows 的 `run.bat`。执行已有测试：

```sh
python3.12 run.py tests
```

临时文件默认使用 `/temp`；不可写时按提示指定其他可写绝对路径。运行操作会覆盖同名结果。

## 项目范围与已有限制

- 调度输入为合成教学场景，小时级调度尚未闭环接入秒级 Simulink 控制；MAT 文件用于数据交换准备。
- 本仓库整理了代码、模型与已有结果；Word 论文和 PPT 汇报文件不在本次上传文件夹中。
- 控制模块的瞬态最低电压尚未完成步长收敛验证。原有验证说明见各模块 `validation-notes.txt`。
- 原项目已在 macOS / Apple Silicon、MATLAB R2025a 与 Python 3.12 下验证；其他平台与版本的适配情况见模块说明。
