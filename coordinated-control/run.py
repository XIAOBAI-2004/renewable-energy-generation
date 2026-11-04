"""Standalone entry point; project type is configured below."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import webbrowser

KIND = 'control'
ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description='Run or display this standalone project.')
    modes = ['run', 'show', 'setup', 'plots']
    parser.add_argument('mode', nargs='?', default='run', choices=modes)
    parser.add_argument('--cache-dir', help='Writable absolute directory for temporary files')
    parser.add_argument('--matlab', help='Full path to the MATLAB R2025a executable')
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
    python = str(python) if python.is_file() else sys.executable

    def run(command, cwd=ROOT, child_env=None):
        subprocess.run(command, cwd=cwd, env=child_env or env, check=True)

    if args.mode == 'setup':
        if sys.version_info[:2] != (3, 12):
            parser.error('Please run setup with Python 3.12.')
        if not (ROOT / '.venv').exists():
            run([sys.executable, '-m', 'venv', str(ROOT / '.venv')])
        python = str(ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python'))
        run([python, '-m', 'pip', 'install', '--no-cache-dir', '--index-url', args.index_url, '-r', str(ROOT / 'requirements.txt')])
        print('依赖安装完成。现在可以双击运行脚本。')
        return

    if args.mode == 'run':
        matlab = args.matlab or env.get('MATLAB_BIN') or shutil.which('matlab')
        if not matlab and sys.platform == 'darwin':
            candidates = sorted(Path('/Applications').glob('MATLAB_*.app/bin/matlab'))
            preferred = [p for p in candidates if p.parents[1].name == 'MATLAB_R2025a.app']
            if candidates:
                matlab = str(preferred[0] if preferred else candidates[-1])
        if not matlab and os.name == 'nt':
            candidates = sorted((Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'MATLAB').glob('R*/bin/matlab.exe'))
            preferred = [p for p in candidates if p.parents[1].name == 'R2025a']
            if candidates:
                matlab = str(preferred[0] if preferred else candidates[-1])
        if not matlab:
            parser.error('MATLAB not found; pass --matlab, or run start_demo directly in MATLAB.')
        script = "restoredefaultpath; addpath('" + str(ROOT).replace("'", "''") + "'); set(0,'DefaultFigureVisible','off'); start_demo;"
        matlab_env = env.copy()
        if os.name == 'posix':
            matlab_env['TMPDIR'] = matlab_env['TEMP'] = matlab_env['TMP'] = '.'
        run([matlab, '-batch', script], cache, matlab_env)
    elif args.mode == 'plots':
        run([python, str(ROOT / 'analyze_course_results.py')])
    if args.mode == 'run' and not args.no_show:
        webbrowser.open((ROOT / 'index.html').as_uri())


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
