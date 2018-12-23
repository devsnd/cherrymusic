from playlist.models import Playlist, Track
from utils.autoadmin import generate_and_register_admin

generate_and_register_admin(Playlist)
generate_and_register_admin(Track)
