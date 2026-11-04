"""Standalone entry point; project type is configured below."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import webbrowser

KIND = 'dispatch'
ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description='Run or display this standalone project.')
    modes = ['run', 'show', 'setup', 'tests']
    parser.add_argument('mode', nargs='?', default='run', choices=modes)
    parser.add_argument('--cache-dir', help='Writable absolute directory for temporary files')
    parser.add_argument('--python', help='Python 3.12 executable used to create the local environment')
    parser.add_argument('--index-url', default=os.environ.get('PIP_INDEX_URL', 'https://pypi.tuna.tsinghua.edu.cn/simple'), help='Python package index for setup')
    parser.add_argument('--no-show', action='store_true', help='Do not open a browser after running')
    args = parser.parse_args()
    if args.mode == 'show':
        webbrowser.open((ROOT / 'index.html').as_uri())
        return

    config_path = ROOT / 'local_settings.json'
    config = json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
    cache = Path(args.cache_dir or os.environ.get('COURSE_TEMP_DIR') or config.get('cache_dir') or '/temp').expanduser()
    while True:
        try:
            if not cache.is_absolute():
                raise OSError('Use an absolute path.')
            cache.mkdir(parents=True, exist_ok=True)
            break
        except OSError as exc:
            if not sys.stdin.isatty():
                parser.error(f'Cannot use cache directory {cache}: {exc}. Supply --cache-dir.')
            print('默认缓存目录不可写，请输入另一处可写目录的完整路径（只需设置一次）：')
            cache = Path(input().strip().strip('"')).expanduser()
    config['cache_dir'] = str(cache)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
    env = os.environ.copy()
    env['COURSE_TEMP_DIR'] = str(cache)
    env['TMPDIR'] = env['TEMP'] = env['TMP'] = str(cache)
    env['MPLCONFIGDIR'] = str(cache / 'renewable-energy' / KIND / 'matplotlib')
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONNOUSERSITE'] = '1'
    env.pop('PYTHONPATH', None)
    python = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')

    def run(command, cwd=ROOT, child_env=None):
        subprocess.run(command, cwd=cwd, env=child_env or env, check=True)

    if not python.is_file():
        candidates = [[p] for p in [args.python, config.get('python_executable'), sys.executable,
                                   shutil.which('python3.12'), shutil.which('python3')]
                      if p]
        if sys.platform == 'darwin':
            candidates += [[p] for p in [
                '/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12',
                '/opt/homebrew/bin/python3.12', '/usr/local/bin/python3.12']]
        if os.name == 'nt':
            if shutil.which('py'):
                candidates.append([shutil.which('py'), '-3.12'])
            candidates += [[str(Path(os.environ.get('LOCALAPPDATA', '')) /
                                    'Programs/Python/Python312/python.exe')]]
        base_python = None
        for candidate in candidates:
            try:
                probe = subprocess.run(candidate + ['-c',
                    'import sys; sys.exit(0 if sys.version_info[:2] == (3,12) else 1)'],
                    env=env, capture_output=True)
            except OSError:
                continue
            if probe.returncode == 0:
                base_python = candidate
                break
        if base_python is None:
            parser.error('未找到 Python 3.12。请先安装 Python 3.12，或用 --python 指定其完整路径。')
        print('首次运行：正在为本模块创建独立 Python 环境…', flush=True)
        run(base_python + ['-m', 'venv', str(ROOT / '.venv')])
    python = str(python)
    # Probe the interpreter used by the application, never the system Python.
    probe_code = (
        'import numpy, pandas, matplotlib, scipy, cvxpy, pyscipopt; '
        'assert "SCIP" in cvxpy.installed_solvers(), "SCIP is unavailable"'
    )
    probe = subprocess.run([python, '-c', probe_code], cwd=ROOT, env=env,
                           capture_output=True, text=True)
    if args.mode == 'setup' or probe.returncode != 0:
        print('正在安装本模块依赖（首次运行需要联网，请等待）…', flush=True)
        run([python, '-m', 'pip', 'install', '--no-cache-dir', '--index-url', args.index_url,
             '-r', str(ROOT / 'requirements.txt')])
        print('安装完成，正在检查数值软件包与 SCIP 求解器…', flush=True)
        run([python, '-c', probe_code])
        print('依赖准备完成，开始计算。', flush=True)
    if args.mode == 'setup':
        return

    if args.mode == 'tests':
        run([python, '-m', 'unittest', '-v', 'test_dispatch.py'])
    else:
        run([python, str(ROOT / 'dispatch.py')])
    if args.mode == 'run' and not args.no_show:
        webbrowser.open((ROOT / 'index.html').as_uri())


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
