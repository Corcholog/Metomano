import random
import spotify_lyrics_scraper as spotify
from dotenv import load_dotenv
import os

load_dotenv()

sp_dc = os.getenv("SP_DC")
sp_key = os.getenv("SP_KEY")

# Obtener el token de Spotify
token = spotify.getToken(sp_dc, sp_key)  # SP Key puede dar hasta un año de tokens de Spotify.

# Obtener las letras de la canción
lyrics = spotify.getLyrics(token, trackId="5G2f63n7IPVPPjfNIGih7Q")

# Verificar que las letras se obtuvieron correctamente
if type(lyrics) == spotify.spotifyDict:
    # Formatear las letras para obtener el contenido en un diccionario
    formatted_lyrics = lyrics.formatLyrics(mode=0)  # El modo 0 es solo las letras

    # Verificar que 'message' es una lista con las líneas de la letra
    if isinstance(formatted_lyrics['message'], list):
        lines = formatted_lyrics['message']  # Aquí tenemos las líneas de la letra

        # Si hay más de 6 líneas, selecciona entre 4, 5 o 6 líneas consecutivas
        if len(lines) > 6:
            num_lines = random.choice([4, 5, 6])  # Elegir aleatoriamente cuántas líneas tomar
            start_idx = random.randint(0, len(lines) - num_lines)  # Elegir el índice de inicio
            chosen_section = "\n".join(lines[start_idx:start_idx + num_lines])  # Obtener el subconjunto de líneas
        else:
            chosen_section = "\n".join(lines)  # Si no hay más de 6 líneas, tomar todas

        print(chosen_section)
    else:
        print("Error: Formato inesperado en las letras.")
else:
    print(f"Error: {lyrics}")
