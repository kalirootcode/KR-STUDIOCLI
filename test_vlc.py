import vlc
import time
instance = vlc.Instance('--no-xlib', '--quiet')
player = instance.media_player_new()
media = instance.media_new('kr_studio/assets/default_bg.png')
player.set_media(media)
player.play()
time.sleep(1)
print(f"State after play(): {player.get_state()}")
try:
    player.set_pause(1)
    print(f"State after set_pause(1): {player.get_state()}")
except Exception as e:
    print(f"Error set_pause(1): {e}")

try:
    player.pause()
    print(f"State after pause(): {player.get_state()}")
except Exception as e:
    print(f"Error pause(): {e}")
