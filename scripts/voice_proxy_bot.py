# scripts/voice_proxy_bot.py - 语音命令代理 Bot
"""
独立 Telegram Bot，做语音命令的预处理旁路：
1. 收到语音 → Whisper GPU 转写
2. resolve() 识别意图
3. risk=low 自动执行，回复结果
4. 非命令消息 → 转发给 OpenClaw 主 Bot（或直接回复转写文本）

用法: python voice_proxy_bot.py
"""
import json, sys, os, io, time, logging, asyncio, tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'aios'))

from core.app_alias import resolve
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# 配置
VOICE_BOT_TOKEN = '8297495903:AAFwnRpSiBCo946x_NzK7kA10ToniDOium8'
ALLOWED_USER_ID = 7986452220  # 珊瑚海的 Telegram ID
COMMAND_DEDUP_WINDOW = 60

# Whisper 模型
_model = None
_command_cache = {}

logging.basicConfig(format='[proxy] %(asctime)s %(message)s', level=logging.INFO, datefmt='%H:%M:%S')
log = logging.getLogger(__name__)


def get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        log.info('加载 Whisper large-v3 GPU...')
        _model = WhisperModel('large-v3', device='cuda', compute_type='int8_float16')
        log.info('Whisper 就绪')
    return _model


def is_command_deduped(cmd_key):
    global _command_cache
    now = time.time()
    _command_cache = {k: v for k, v in _command_cache.items() if now - v < COMMAND_DEDUP_WINDOW * 2}
    last = _command_cache.get(cmd_key, 0)
    if now - last < COMMAND_DEDUP_WINDOW:
        return True
    _command_cache[cmd_key] = now
    return False


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
    exe_path = r.get('exe_path')
    proc_name = r.get('process_name')
    canonical = r.get('canonical', '')

    if action == 'open':
        if not exe_path:
            return False, f'未知路径: {canonical}'
        if proc_name and is_process_running(proc_name):
            return True, 'NOOP_ALREADY_RUNNING'
        try:
            subprocess.Popen([exe_path], shell=False)
            time.sleep(1.5)
            return True, 'SUCCESS'
        except Exception as e:
            return False, str(e)
    elif action == 'close':
        if not proc_name:
            return False, f'未知进程: {canonical}'
        if not is_process_running(proc_name):
            return True, 'NOOP_NOT_RUNNING'
        try:
            subprocess.run(['taskkill', '/IM', proc_name, '/F'], capture_output=True, timeout=5)
            return True, 'SUCCESS'
        except Exception as e:
            return False, str(e)
    return False, f'不支持: {action}'


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    voice = update.message.voice or update.message.audio
    if not voice:
        return

    log.info(f'收到语音 ({voice.duration}s, {voice.file_size}B)')

    # 下载语音文件
    file = await context.bot.get_file(voice.file_id)
    with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp:
        tmp_path = tmp.name
    await file.download_to_drive(tmp_path)

    # 转写
    try:
        model = get_model()
        segments, info = model.transcribe(tmp_path, language='zh', beam_size=1,
                                          no_speech_threshold=0.5, vad_filter=True)
        text = ''.join(seg.text for seg in segments).strip()
    except Exception as e:
        log.error(f'转写失败: {e}')
        await update.message.reply_text(f'转写失败: {e}')
        return
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass

    if not text:
        await update.message.reply_text('未识别到语音内容')
        return

    log.info(f'转写: {text}')

    # 识别意图
    r = resolve(text)

    if r.get('action') and r.get('matched') and r.get('risk') != 'high':
        # 可执行命令
        cmd_key = f"{r['action']}:{r['canonical']}"
        if is_command_deduped(cmd_key):
            await update.message.reply_text(f"{r['canonical']}刚刚已处理过")
            return

        ok, detail = exec_command(r)
        action_map = {'open': '已打开', 'close': '已关闭'}
        verb = action_map.get(r['action'], '已处理')

        if ok:
            reply = f"{verb}{r['canonical']}"
            if detail == 'NOOP_ALREADY_RUNNING':
                reply = f"{r['canonical']}已经在运行了"
            elif detail == 'NOOP_NOT_RUNNING':
                reply = f"{r['canonical']}没有在运行"
            log.info(reply)
        else:
            reply = f"执行失败: {detail}"
            log.error(reply)

        await update.message.reply_text(reply)

    elif r.get('risk') == 'high':
        await update.message.reply_text(f"⚠️ 高风险操作: {r.get('action')} {r['canonical']}，需要确认")
    else:
        # 非命令，回复转写文本（用户可以看到转写结果）
        await update.message.reply_text(f'🎙️ {text}')


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    text = update.message.text or ''
    r = resolve(text)

    if r.get('action') and r.get('matched') and r.get('risk') != 'high':
        cmd_key = f"{r['action']}:{r['canonical']}"
        if is_command_deduped(cmd_key):
            await update.message.reply_text(f"{r['canonical']}刚刚已处理过")
            return

        ok, detail = exec_command(r)
        action_map = {'open': '已打开', 'close': '已关闭'}
        verb = action_map.get(r['action'], '已处理')

        if ok:
            reply = f"{verb}{r['canonical']}"
            if detail == 'NOOP_ALREADY_RUNNING':
                reply = f"{r['canonical']}已经在运行了"
            elif detail == 'NOOP_NOT_RUNNING':
                reply = f"{r['canonical']}没有在运行"
        else:
            reply = f"执行失败: {detail}"

        await update.message.reply_text(reply)
    else:
        await update.message.reply_text('这个 Bot 只处理语音命令和应用控制。其他消息请发给小九主号 🐾')


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🐾 小九语音助手\n\n'
        '发语音或文字命令，我会自动执行：\n'
        '• 打开/关闭 应用\n'
        '• 播放/暂停\n\n'
        '低风险命令直接执行，高风险会确认。'
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    model_status = 'loaded' if _model else 'not loaded'
    await update.message.reply_text(f'Whisper: {model_status}\nDedup cache: {len(_command_cache)} entries')


def main():
    log.info('小九语音代理 Bot 启动')

    # 预加载 Whisper
    get_model()

    app = Application.builder().token(VOICE_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CommandHandler('status', cmd_status))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    log.info('Bot 就绪，开始轮询...')
    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log.error(f'致命错误: {e}')
        import traceback
        traceback.print_exc()
        input('按回车退出...')
