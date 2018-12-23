from utils.autoadmin import generate_and_register_admin
from .models import User, Playlist, Track

generate_and_register_admin(User)
generate_and_register_admin(Playlist)
generate_and_register_admin(Track)
