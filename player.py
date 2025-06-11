from pytgcalls import PyTgCalls
from pyrogram import Client
from pytgcalls.types.input_stream import InputAudioStream, InputStream
import asyncio
import yt_dlp
from dotenv import load_dotenv
import os

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_string = os.getenv("SESSION_STRING")
group_chat_id = int(os.getenv("GROUP_CHAT_ID"))

client = Client(session_string, api_id, api_hash)
group_call = PyTgCalls(client)

queue = []
current_audio = None
current_title = None
is_playing = False

async def start_bot():
    await client.start()
    await group_call.start()

def download_audio(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=True)['entries'][0]
        return ydl.prepare_filename(info), info['title']

async def join_and_play(file_path):
    global is_playing, current_audio
    is_playing = True
    current_audio = file_path
    await group_call.join_group_call(
        group_chat_id,
        InputStream(InputAudioStream(file_path))
    )

def play_audio(query):
    file_path, title = download_audio(query)
    queue.append((file_path, title))
    if not is_playing:
        asyncio.get_event_loop().create_task(play_next())
    return title

async def play_next():
    global is_playing, current_audio, current_title
    if queue:
        file_path, title = queue.pop(0)
        current_audio = file_path
        current_title = title
        is_playing = True
        await join_and_play(file_path)
        await client.send_message(group_chat_id, f"🎧 Sedang memutar: {title}")

@group_call.on_stream_end()
async def on_stream_end(_, __):
    global is_playing, current_audio, current_title
    is_playing = False
    current_audio = None
    current_title = None
    if queue:
        await play_next()
    else:
        await client.send_message(group_chat_id, "✅ Semua lagu selesai.")
        await group_call.leave_group_call(group_chat_id)

async def skip():
    global is_playing, current_audio
    if is_playing:
        await group_call.leave_group_call(group_chat_id)
        is_playing = False
        current_audio = None
        if queue:
            await play_next()

async def stop():
    global is_playing, current_audio, current_title, queue
    queue.clear()
    current_audio = None
    current_title = None
    is_playing = False
    await client.send_message(group_chat_id, "⏹️ Dihentikan & antrean dihapus.")
    await group_call.leave_group_call(group_chat_id)

def get_queue():
    return [title for _, title in queue]

def get_now_playing():
    return current_title if current_title else "Tidak ada yang diputar."
