import os
import sys
import time
import numpy as np
import sounddevice as sd
import plotext as plt
import threading
import keyboard
import shutil
from pydub import AudioSegment

def clear_screen():
    os.system("clear")

def get_terminal_size():
    try:
        size = shutil.get_terminal_size()
        return size.columns, size.lines
    except OSError:
        return 50, 20

clear_screen()
song_path = input("Enter song file full path: ").strip()
if not os.path.isfile(song_path):
    print("Error: File not found!")
    sys.exit()

audio = AudioSegment.from_file(song_path)
samples = np.array(audio.get_array_of_samples()).astype(np.float32)
samplerate = audio.frame_rate
samples = samples / np.max(np.abs(samples))

if audio.channels == 2:
    samples = samples.reshape(-1, 2)
    samples = np.mean(samples, axis=1)

is_paused = False
playback_pos = 0
total_samples = len(samples)
total_duration = total_samples / samplerate

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

def visualize_audio():
    global playback_pos, is_paused

    plt.title("@y-nabeelxd | Music Player")

    while playback_pos < total_samples:
        if is_paused:
            time.sleep(0.5)
            continue

        term_width, term_height = get_terminal_size()
        max_bar_length = max(10, term_width - 30)
        wave_height = max(10, term_height - 7)

        current_time = playback_pos / samplerate

        progress = int((current_time / total_duration) * max_bar_length)
        progress_bar = f"({format_time(current_time)}) {'-' * progress}•{'_' * (max_bar_length - progress)} ({format_time(total_duration)})"

        clear_screen()
        print ("")
        print("@y-nabeelxd | Music Player")
        print("")
        print("")
        print(progress_bar[:term_width])
        print("")
        print("")

        chunk_size = samplerate // 20
        chunk = samples[playback_pos:playback_pos + chunk_size]

        display_width = max(30, term_width - 10)
        downsample_factor = max(1, len(chunk) // display_width)
        chunk = chunk[::downsample_factor]

        if len(chunk) > 2:
            chunk = np.convolve(chunk, np.ones(5)/5, mode="same")
            
        if len(chunk) > 0:
            chunk = chunk / np.max(np.abs(chunk))

        plt.clear_data()
        plt.plot(chunk, marker="braille", color="red")
        plt.ylim(-1, 1)
        plt.xlim(0, len(chunk))
        plt.plotsize(display_width, wave_height)
        plt.show()

        time.sleep(0.05)

def play_audio():
    global playback_pos, is_paused

    with sd.OutputStream(samplerate=samplerate, channels=1, dtype="float32") as stream:
        while playback_pos < total_samples:
            if is_paused:
                time.sleep(0.1)
                continue

            chunk_size = samplerate // 20
            chunk = samples[playback_pos:playback_pos + chunk_size]
            stream.write(chunk.reshape(-1, 1))
            playback_pos += chunk_size

def handle_keys():
    global is_paused
    while True:
        key = keyboard.read_event().name
        if key == "up":
            if not is_paused:
                is_paused = True
                sd.stop()
        elif key == "down":
            if is_paused:
                is_paused = False

visualize_thread = threading.Thread(target=visualize_audio, daemon=True)
play_thread = threading.Thread(target=play_audio, daemon=True)
keyboard_thread = threading.Thread(target=handle_keys, daemon=True)

visualize_thread.start()
play_thread.start()
keyboard_thread.start()

try:
    while playback_pos < total_samples:
        time.sleep(1)
except KeyboardInterrupt:
    sd.stop()
    clear_screen()
    print("Playback stopped.")
    sys.exit()