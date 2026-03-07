import vlc
import time
instance = vlc.Instance('--no-xlib', '--quiet')
player = instance.media_player_new()
media = instance.media_new('kr_studio/assets/default_bg.mp4')
player.set_media(media)
player.play()
time.sleep(1)
print(f"State after play(): {player.get_state()}")
