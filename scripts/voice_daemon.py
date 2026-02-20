# scripts/voice_daemon.py - 语音命令守护进程
"""
监听 OpenClaw inbound media 目录，检测新 ogg 文件：
1. Whisper GPU 转写
2. app_alias.resolve() 识别意图
3. risk=low 自动执行
4. 结果写入 voice_results.jsonl 供主会话读取

不干扰 OpenClaw 消息链路，纯旁路执行。
"""
import json, sys, os, io, time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'aios'))

from core.app_alias import resolve

WATCH_DIR = Path(os.environ['USERPROFILE']) / '.openclaw' / 'media' / 'inbound'
RESULTS_FILE = Path(__file__).resolve().parent.parent / 'memory' / 'voice_results.jsonl'
PROCESSED_FILE = Path(__file__).resolve().parent.parent / 'memory' / 'voice_processed.json'
HEALTH_FILE = Path(__file__).resolve().parent.parent / 'memory' / 'voice_daemon_health.json'
COMMAND_DEDUP_WINDOW = 60  # 同一命令60秒去重
PROCESSED_MAX_AGE = 86400  # 24小时后清理已处理记录
FILE_STABLE_CHECKS = 3     # 文件大小稳定检查次数
FILE_STABLE_INTERVAL = 0.5 # 每次检查间隔秒数

# Whisper 模型（延迟加载）
_model = None
# 命令去重缓存: {command_key: epoch}
_command_cache = {}


def get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel('large-v3', device='cuda', compute_type='int8_float16')
        print('[daemon] Whisper large-v3 GPU loaded')
    return _model


def load_processed():
    if PROCESSED_FILE.exists():
        try:
            return json.loads(PROCESSED_FILE.read_text(encoding='utf-8'))
        except:
            pass
    return {}


def save_processed(state):
    # 清理超过24小时的旧记录
    now = time.time()
    state = {k: v for k, v in state.items()
             if now - v.get('ts', 0) < PROCESSED_MAX_AGE}
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def append_result(result):
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_FILE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False) + '\n')


def update_health(status, detail=''):
    health = {
        'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'epoch': int(time.time()),
        'status': status,
        'detail': detail,
        'pid': os.getpid(),
    }
    HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    HEALTH_FILE.write_text(json.dumps(health, ensure_ascii=False, indent=2), encoding='utf-8')


def wait_file_stable(path, checks=FILE_STABLE_CHECKS, interval=FILE_STABLE_INTERVAL):
    """等文件大小稳定（写入完成）"""
    prev_size = -1
    stable_count = 0
    for _ in range(checks * 3):  # 最多等 checks*3 轮
        try:
            size = path.stat().st_size
        except:
            time.sleep(interval)
            continue
        if size == prev_size and size > 0:
            stable_count += 1
            if stable_count >= checks:
                return True
        else:
            stable_count = 0
        prev_size = size
        time.sleep(interval)
    return prev_size > 0  # 超时但文件非空也继续


def is_command_deduped(command_key):
    """同一命令60秒内去重"""
    global _command_cache
    now = time.time()
    # 清理过期
    _command_cache = {k: v for k, v in _command_cache.items()
                      if now - v < COMMAND_DEDUP_WINDOW * 2}
    last = _command_cache.get(command_key, 0)
    if now - last < COMMAND_DEDUP_WINDOW:
        return True
    _command_cache[command_key] = now
    return False


def transcribe(ogg_path):
    model = get_model()
    segments, info = model.transcribe(
        str(ogg_path), language='zh', beam_size=1,
        no_speech_threshold=0.5, vad_filter=True,
    )
    return ''.join(seg.text for seg in segments).strip()


def is_process_running(name):
    import subprocess
    try:
        r = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {name}', '/NH'],
                           capture_output=True, timeout=5, encoding='gbk', errors='replace')
        return name.lower() in r.stdout.lower()
    except:
        return False


def exec_command(r):
    import subprocess
    action = r.get('action')
    canonical = r.get('canonical', '')
    exe_path = r.get('exe_path')
    proc_name = r.get('process_name')

    if action == 'open':
        if not exe_path:
            return False, f'未知路径: {canonical}'
        if proc_name and is_process_running(proc_name):
            return True, 'NOOP_ALREADY_RUNNING'
        try:
            subprocess.Popen([exe_path], shell=False)
            time.sleep(1.5)
            if proc_name and is_process_running(proc_name):
                return True, 'SUCCESS'
            return True, 'STARTED_UNVERIFIED'
        except Exception as e:
            return False, str(e)

    elif action == 'close':
        if not proc_name:
            return False, f'未知进程: {canonical}'
        if not is_process_running(proc_name):
            return True, 'NOOP_NOT_RUNNING'
        try:
            subprocess.run(['taskkill', '/IM', proc_name, '/F'],
                           capture_output=True, timeout=5)
            time.sleep(0.5)
            if not is_process_running(proc_name):
                return True, 'SUCCESS'
            return False, 'KILL_FAILED'
        except Exception as e:
            return False, str(e)

    return False, f'不支持的动作: {action}'


def process_ogg(ogg_path):
    """处理单个 ogg 文件"""
    state = load_processed()
    file_key = ogg_path.name

    # 文件去重
    if file_key in state:
        return

    print(f'[daemon] 新语音: {file_key}')

    # 转写
    t0 = time.monotonic()
    try:
        text = transcribe(ogg_path)
    except Exception as e:
        print(f'[daemon] 转写失败: {e}')
        state[file_key] = {'ts': time.time(), 'error': str(e)}
        save_processed(state)
        update_health('error', f'转写失败: {e}')
        return
    transcribe_ms = round((time.monotonic() - t0) * 1000)

    if not text:
        print('[daemon] 无语音内容')
        state[file_key] = {'ts': time.time(), 'text': '', 'action': None}
        save_processed(state)
        return

    print(f'[daemon] 转写({transcribe_ms}ms): {text}')

    # 识别意图
    r = resolve(text)

    result = {
        'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'file': file_key,
        'raw_text': text,
        'canonical': r.get('canonical', text),
        'action': r.get('action'),
        'risk': r.get('risk', 'low'),
        'matched': r.get('matched', False),
        'executed': False,
        'exec_result': None,
        'transcribe_ms': transcribe_ms,
    }

    # 低风险 + 有动作 + 匹配成功 → 自动执行
    if r.get('action') and r.get('matched') and r.get('risk') != 'high':
        # 命令去重
        cmd_key = f"{r['action']}:{r['canonical']}"
        if is_command_deduped(cmd_key):
            result['exec_result'] = 'NOOP_DEDUP'
            result['executed'] = True
            print(f'[daemon] 命令去重: {cmd_key}')
        else:
            ok, detail = exec_command(r)
            result['executed'] = ok
            result['exec_result'] = detail
            action_map = {'open': '已打开', 'close': '已关闭'}
            verb = action_map.get(r['action'], '已处理')
            if ok:
                print(f'[daemon] {verb}{r["canonical"]} ({detail})')
            else:
                print(f'[daemon] 执行失败: {detail}')
    elif r.get('risk') == 'high':
        result['exec_result'] = 'NEEDS_CONFIRMATION'
        print(f'[daemon] 高风险，跳过: {r.get("action")} {r.get("canonical")}')
    else:
        print(f'[daemon] 非命令: {text}')

    append_result(result)
    state[file_key] = {'ts': time.time(), 'text': text, 'action': r.get('action')}
    save_processed(state)
    update_health('ok', f'处理完成: {text}')


class OggHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() == '.ogg':
            # 等文件写入完成
            if wait_file_stable(path):
                try:
                    process_ogg(path)
                except Exception as e:
                    print(f'[daemon] 处理异常: {e}')
                    update_health('error', str(e))


def scan_existing():
    """启动时扫描已有但未处理的 ogg"""
    state = load_processed()
    now = time.time()
    count = 0
    for ogg in sorted(WATCH_DIR.glob('*.ogg'), key=lambda p: p.stat().st_mtime):
        age = now - ogg.stat().st_mtime
        if age < 300 and ogg.name not in state:
            try:
                process_ogg(ogg)
                count += 1
            except Exception as e:
                print(f'[daemon] 扫描异常: {e}')
    if count:
        print(f'[daemon] 启动扫描处理了 {count} 个文件')


def main():
    print(f'[daemon] 语音命令守护进程启动 (pid={os.getpid()})')
    print(f'[daemon] 监听: {WATCH_DIR}')
    print(f'[daemon] 结果: {RESULTS_FILE}')

    update_health('starting', 'loading whisper model')

    # 预加载 Whisper
    get_model()

    update_health('ok', 'model loaded, scanning existing')

    # 扫描已有文件（不阻塞启动）
    try:
        scan_existing()
    except Exception as e:
        print(f'[daemon] 扫描异常，跳过: {e}')

    # 监听新文件
    handler = OggHandler()
    observer = Observer()
    observer.schedule(handler, str(WATCH_DIR), recursive=False)
    observer.start()

    update_health('ok', 'watching')
    print('[daemon] 监听中... Ctrl+C 退出')

    try:
        heartbeat_interval = 300  # 5分钟心跳
        last_heartbeat = time.time()
        while True:
            time.sleep(1)
            if time.time() - last_heartbeat > heartbeat_interval:
                update_health('ok', 'alive')
                last_heartbeat = time.time()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    update_health('stopped', 'user interrupt')
    print('[daemon] 已停止')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'[daemon] 致命错误: {e}')
        import traceback
        traceback.print_exc()
        input('按回车退出...')
