import pygame
import time
import os
import re

class MusicPlayer:
    def __init__(self, freq=44100, size=-16, channels=2, buffer=512):
        
        pygame.mixer.init(frequency=freq, size=size, channels=channels, buffer=buffer)
        
        music_dir = os.path.expanduser("~/Music/2018_Music_for_Reading")
        if not os.path.isdir(music_dir):
            raise ValueError(f"Music directory not found: {music_dir}")
        
        audio_exts = (".mp3", ".wav", ".ogg", ".flac")
        tracks = [f for f in os.listdir(music_dir)
                  if f.lower().endswith(audio_exts) and re.match(r"^\d+", f)]
        def _sort_key(f):
            m = re.match(r"^(\d+)", f)
            return int(m.group(1)) if m else float('inf')
        tracks.sort(key=_sort_key)
        
        self.playlist = []
        for track in tracks:
            path = os.path.join(music_dir, track)
            try:
                sound = pygame.mixer.Sound(path)
                duration = sound.get_length()
            except Exception as e:
                print(f"Warning: Could not load {path}: {e}")
                continue
            self.playlist.append((path, duration))
        if not self.playlist:
            raise ValueError(f"No audio tracks found in {music_dir}")

        self.current_index = 0
        self.resumed = None
        self.paused = None
        self.current_pos = 0.0

    def play_music(self, fade_in_ms=2000):
        if self.resumed is not None:
            elapsed = time.time() - self.resumed + self.current_pos
            duration = self.playlist[self.current_index][1]
            if elapsed >= duration:
                # Advance to next track (wrap around)
                self.current_index = (self.current_index + 1) % len(self.playlist)
                self.current_pos = 0.0
            else:
                # Resume at the correct position
                self.current_pos = elapsed
    
        path, duration = self.playlist[self.current_index]
        print(f"Playing track {self.current_index+1}/{len(self.playlist)}: {os.path.basename(path)} ({duration:.2f}s)")
        pygame.mixer.music.load(path)
        self.resumed = time.time()
        pygame.mixer.music.play(loops=0, start=self.current_pos, fade_ms=fade_in_ms)

    def stop_music(self, fade_out_ms=2000):
        pygame.mixer.music.fadeout(fade_out_ms)
        self.paused = time.time()

if __name__ == '__main__':
    player = MusicPlayer()
    # example usage: play for 10s, pause, wait, then resume
    player.play_music()
    time.sleep(10)
    player.stop_music()
    time.sleep(5)
    player.play_music()
    time.sleep(10)
    player.stop_music()
