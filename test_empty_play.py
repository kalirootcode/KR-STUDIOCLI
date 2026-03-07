import vlc
import time
instance = vlc.Instance('--no-xlib', '--quiet')
player = instance.media_player_new()
# Play empty
player.play()
time.sleep(1)
print(f"State after empty play(): {player.get_state()}")

# Now set media
media = instance.media_new('kr_studio/assets/default_bg.png')
player.set_media(media)
player.play()
time.sleep(1)
print(f"State after media play(): {player.get_state()}")
