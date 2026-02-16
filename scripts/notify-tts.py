"""
Claude Code Hook Handler - Single Voice TTS Notifications

One configurable voice for all events:
- Stop -> Full announcement (what was done)
- Notification -> Context announcement (permission, idle, etc.)
- TaskCompleted -> Quick short "Task completata. X di Y."

Voice and settings read from ~/.claude/cache/tts/tts_config.json
"""

import asyncio
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

# === CONFIG ===
CHIME_GAP_MS = 250
CACHE_DIR = Path.home() / ".claude" / "cache" / "tts"
DYNAMIC_CACHE_DIR = CACHE_DIR / "dynamic"
SOUNDS_DIR = CACHE_DIR / "sounds"
TTS_CONFIG = CACHE_DIR / "tts_config.json"
TRACKER_FILE = CACHE_DIR / "subtask_tracker.json"

# R2-D2 semantic chime mapping
R2D2_CHIMES = {
    "task_done": ["acknowledged.mp3", "acknowledged-2.mp3"],
    "stop": ["excited.mp3", "excited-2.mp3"],
    "permission": ["worried.mp3", "8.mp3"],
    "question": ["chat.mp3", "3.mp3"],
    "idle": ["12.mp3", "19.mp3"],
    "auth": ["7.mp3", "18.mp3"],
    "default": ["13.mp3", "6.mp3"],
}

# Fallback voice
_FALLBACK_VOICE = {"voice": "it-IT-IsabellaNeural", "rate": "-4%", "pitch": "-8Hz"}


# ══════════════════════════════════════════════════
# CONFIG LOADERS
# ══════════════════════════════════════════════════

def load_config() -> dict:
    try:
        if TTS_CONFIG.is_file():
            return json.loads(TTS_CONFIG.read_text())
    except Exception:
        pass
    return {"sound_pack": "r2d2", "volume": 200}


def get_voice() -> dict:
    """Get the single voice profile from config."""
    config = load_config()
    return config.get("voice", _FALLBACK_VOICE)


def get_volume() -> int:
    return load_config().get("volume", 200)


def get_sound_pack() -> str:
    return load_config().get("sound_pack", "r2d2")


# ══════════════════════════════════════════════════
# PHRASE TEMPLATES
# ══════════════════════════════════════════════════

# TaskCompleted: short with task name
TASK_PHRASES = {
    "progress_detail": "{completed} di {total}. {detail}",
    "progress": "{completed} di {total}. Task completata.",
    "detail": "{detail}",
    "simple": "Task completata.",
}

# Stop: full announcement with activity name
STOP_PHRASES = {
    None: "Progetto {repo}. {detail}{plan_info}",
    "hook_active": "Progetto {repo}. Ciclo completato. {detail}{plan_info}",
    "no_detail": "Progetto {repo}. Attivita' completata.{plan_info}",
    "hook_no_detail": "Progetto {repo}. Ciclo completato.{plan_info}",
}

# Notification: context-aware
NOTIF_PHRASES = {
    "permission_prompt": "Progetto {repo}. Ho bisogno del tuo permesso. {detail}",
    "idle_prompt": "Progetto {repo}. In attesa del tuo input.",
    "auth_success": "Progetto {repo}. Autenticazione completata.",
    "elicitation_dialog": "Progetto {repo}. Ho una domanda. {detail}",
    None: "Progetto {repo}. Notifica. {detail}",
}


# ══════════════════════════════════════════════════
# SUBTASK TRACKER
# ══════════════════════════════════════════════════

def load_tracker() -> dict:
    try:
        if TRACKER_FILE.is_file():
            return json.loads(TRACKER_FILE.read_text())
    except Exception:
        pass
    return {"total": 0, "completed": 0, "session_id": ""}


def update_tracker(data: dict) -> tuple[int, int]:
    tracker = load_tracker()
    session_id = data.get("session_id", "")

    if session_id and session_id != tracker.get("session_id", ""):
        tracker = {"total": 0, "completed": 0, "session_id": session_id}

    total = (
        data.get("total_tasks")
        or data.get("parallel_count")
        or data.get("total_subtasks")
        or tracker.get("total", 0)
    )
    completed = tracker.get("completed", 0) + 1

    if total and completed > total:
        total = completed

    tracker.update({"total": total, "completed": completed, "session_id": session_id})

    try:
        TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
        TRACKER_FILE.write_text(json.dumps(tracker))
    except Exception:
        pass

    return completed, total


# ══════════════════════════════════════════════════
# AUDIO PLAYBACK
# ══════════════════════════════════════════════════

def play_chime(chime_key: str) -> None:
    pack_name = get_sound_pack()
    pack_dir = SOUNDS_DIR / pack_name

    if pack_name == "r2d2" and pack_dir.is_dir():
        pool = R2D2_CHIMES.get(chime_key, R2D2_CHIMES.get("default", []))
        if pool:
            filepath = pack_dir / random.choice(pool)
            if filepath.is_file():
                play_mp3_sync(str(filepath))
                return
    elif pack_dir.is_dir():
        sounds = list(pack_dir.glob("*.mp3"))
        if sounds:
            play_mp3_sync(str(random.choice(sounds)))
            return

    try:
        import winsound
        winsound.Beep(800, 200)
    except Exception:
        pass


def play_mp3_sync(filepath: str) -> None:
    if not os.path.isfile(filepath):
        return
    try:
        CREATE_NO_WINDOW = 0x08000000
        proc = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
             "-volume", str(get_volume()), filepath],
            creationflags=CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        proc.wait(timeout=5)
    except Exception:
        pass


def play_mp3(filepath: str) -> None:
    if not os.path.isfile(filepath):
        return
    try:
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
             "-volume", str(get_volume()), filepath],
            creationflags=CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════
# TTS GENERATION
# ══════════════════════════════════════════════════

def get_cached_path(text: str, profile: dict) -> Path:
    key = f"{profile['voice']}:{profile.get('rate','')}:{profile.get('pitch','')}:{text}"
    text_hash = hashlib.md5(key.encode()).hexdigest()[:12]
    return DYNAMIC_CACHE_DIR / f"dyn_{text_hash}.mp3"


async def generate_tts(text: str, profile: dict, output_path: Path) -> bool:
    try:
        import edge_tts
        output_path.parent.mkdir(parents=True, exist_ok=True)
        communicate = edge_tts.Communicate(
            text, profile["voice"],
            rate=profile.get("rate", "+0%"),
            pitch=profile.get("pitch", "+0Hz"),
        )
        await communicate.save(str(output_path))
        return True
    except Exception:
        return False


def resolve_audio(text: str, profile: dict) -> str | None:
    cached = get_cached_path(text, profile)
    if cached.is_file():
        return str(cached)
    ok = asyncio.run(generate_tts(text, profile, cached))
    if ok and cached.is_file():
        return str(cached)
    return None


# ══════════════════════════════════════════════════
# EXTRACTORS
# ══════════════════════════════════════════════════

def extract_repo_name(data: dict) -> str:
    cwd = data.get("cwd") or data.get("working_directory") or os.environ.get("CLAUDE_CWD") or os.getcwd()
    if cwd:
        name = Path(cwd).name
        if name and name.lower() not in ("", "users", "fra", "home", "c:\\"):
            return name
    return "sconosciuto"


def extract_task_detail(data: dict) -> str:
    """Extract task/activity name from hook event data."""
    # Try multiple possible field names
    for key in ("task_subject", "subject", "description", "task_description",
                "task_name", "name", "result", "output"):
        val = data.get(key)
        if val and isinstance(val, str) and len(val.strip()) > 0:
            text = val.strip().rstrip(".")
            return text[:90] + "..." if len(text) > 93 else text
    return ""


def extract_notification_detail(data: dict) -> str:
    msg = data.get("message", "")
    if msg and isinstance(msg, str) and len(msg.strip()) > 0:
        text = msg.strip()
        return text[:77] + "..." if len(text) > 80 else text
    return ""


def extract_plan_info(data: dict) -> str:
    plan = data.get("plan_title") or data.get("plan_name") or data.get("plan")
    if plan and isinstance(plan, str):
        return f" Piano: {plan}."
    return ""


# ══════════════════════════════════════════════════
# MESSAGE BUILDERS
# ══════════════════════════════════════════════════

def build_task_message(completed: int, total: int, detail: str) -> str:
    """Task completion message with activity name."""
    if total > 1 and detail:
        return TASK_PHRASES["progress_detail"].format(completed=completed, total=total, detail=detail)
    if total > 1:
        return TASK_PHRASES["progress"].format(completed=completed, total=total)
    if detail:
        return TASK_PHRASES["detail"].format(detail=detail)
    return TASK_PHRASES["simple"]


def build_stop_message(sub_type: str | None, repo: str, plan_info: str, detail: str) -> str:
    if detail:
        key = "hook_active" if sub_type == "hook_active" else None
        template = STOP_PHRASES.get(key, STOP_PHRASES[None])
        return template.format(repo=repo, plan_info=plan_info, detail=detail)
    key = "hook_no_detail" if sub_type == "hook_active" else "no_detail"
    template = STOP_PHRASES[key]
    return template.format(repo=repo, plan_info=plan_info)


def build_notif_message(sub_type: str | None, repo: str, detail: str) -> str:
    template = NOTIF_PHRASES.get(sub_type, NOTIF_PHRASES[None])
    return template.format(repo=repo, detail=detail)


# ══════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════

def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        data = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        return

    event_name = data.get("hook_event_name", "")
    sub_type = data.get("notification_type") or data.get("type") or data.get("sub_type")
    repo = extract_repo_name(data)
    voice = get_voice()

    if event_name == "TaskCompleted":
        # === QUICK: chime + "X di Y. [task name]" ===
        completed, total = update_tracker(data)
        detail = extract_task_detail(data)
        message = build_task_message(completed, total, detail)
        chime_key = "task_done"

    elif event_name == "Stop":
        # === FULL: chime + "Progetto X. [what was done]" ===
        plan_info = extract_plan_info(data)
        detail = extract_task_detail(data)
        stop_type = "hook_active" if data.get("stop_hook_active") else None
        message = build_stop_message(stop_type, repo, plan_info, detail)
        chime_key = "stop"

    elif event_name == "Notification":
        # === CONTEXT: chime + notification detail ===
        detail = extract_notification_detail(data)
        message = build_notif_message(sub_type, repo, detail)
        chime_map = {
            "permission_prompt": "permission",
            "elicitation_dialog": "question",
            "idle_prompt": "idle",
            "auth_success": "auth",
        }
        chime_key = chime_map.get(sub_type, "default")
    else:
        return

    # Check TTS mode: "full" (default), "semi-silent", "silent"
    tts_mode = load_config().get("tts_mode", "full")

    # 1) Chime (always plays)
    play_chime(chime_key)

    # 2) Voice (depends on mode)
    if tts_mode == "silent":
        return
    if tts_mode == "semi-silent" and event_name != "Stop":
        return

    audio_path = resolve_audio(message, voice)
    if not audio_path:
        return

    time.sleep(CHIME_GAP_MS / 1000)
    play_mp3(audio_path)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
