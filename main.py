import json
import random
import sys
from censorship import censurar
from dotenv import load_dotenv
from collections import Counter
import os, re
import spoti as sp
import scoresys as sc
from lyricsgenius import Genius

def get_lyrics(song, artist):
    return genius.search_song(song, artist).lyrics

def clean_lyrics(lyrics):
    lyrics = re.sub(r'^.*?Lyrics', 'Lyrics', lyrics, flags=re.DOTALL)
    #lyrics = lyrics.splitlines()[1:]  # Divide en líneas y elimina la primera, que contiene lyrics
    #lyrics = "\n".join(lyrics)  # Vuelve a unir el texto con saltos de línea
    # Ahora, eliminamos la primera línea (que podría ser vacía o no)
    lyrics = lyrics.split("\n", 1)[1]  # Divide en 2 partes, manteniendo todo excepto la primera línea

    # Preservar líneas vacías
    lyrics = "\n".join(lyrics.split("\n"))
    keywords = ['Translations', 'Embed', 'You might also like']
    for keyword in keywords:
        lyrics = lyrics.replace(keyword, '')
    
    return lyrics

def dividir_por_secciones(lyrics):
    # Dividimos la letra en secciones usando líneas vacías como separadores
    secciones = lyrics.split("\n\n")  # Cada línea vacía separa una sección
    return secciones

def imprimir_secciones(secciones):
    # Imprimimos los conjuntos de 4 líneas
    for i, seccion in enumerate(secciones, 1):
        print(f"Conjunto {i}:\n{seccion}\n")
        print()

def get_song_pool(artist_list, playlists=None):
    song_pool = []  # Inicializamos una lista vacía
    for artist_id in artist_list:
        song_pool.extend(sp.get_all_tracks_by_artist(token, artist_id))  # Usamos extend para añadir múltiples canciones
    return song_pool

load_dotenv()

genius_access_token = os.getenv("GENIUS_ACCESS")
genius = Genius(genius_access_token, remove_section_headers=True,verbose=False, retries=5)
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

token = sp.get_token(client_id, client_secret)

album_play = "3iPSVi54hsacKKl1xIR2eH" # id del album short n sweet de sabrina carpenter

playlist_id = "37i9dQZF1DWSo7PX7dbgH8"

#short_n_sweet = sp.get_album_tracks(token, album_id=album_play, artist_name=sp.get_artist_name(token, sabrina_carpenter_id))

#art_id = sp.get_artist_id(token, input("Ingresa el nombre del artista para jugar: "))

#artists_ids = [art_id]





song_pool = sp.get_playlist_tracks_with_artists(token, playlist_id=playlist_id, limit=20)
#song_pool = get_song_pool(artists_ids)


#for song in song_pool:
 #   print(f"{song['name']} (Popularidad: {song['popularity']})")

game_length = 10
random_game = True  # Cambia este valor a False para obtener las canciones en orden de popularidad

# Seleccionar canciones al azar si random_game es True
if random_game:
    game_songs = random.sample(song_pool, min(game_length, len(song_pool)))
else:
    game_songs = song_pool[:game_length]

global_score = 0
max_global_score = 0
    
for song in game_songs:
    lyrics = clean_lyrics(get_lyrics(song['name'], song['artist_name']))
    secciones = dividir_por_secciones(lyrics)
    idx = random.randint(0, len(secciones) - 1)
    chosen_section = secciones[idx]
    
    censored_lyrics, censorship = censurar(chosen_section, percentage=0.5, LANG="ES")
    print(f"La letra que debes adivinar es: \n{censored_lyrics}\n")

    player_words = []
    skip = False

    for _ in censorship:
        print(f"Ingrese la palabra: ", end='', flush=True)  # No hacer un salto de línea
        word = input()
        sys.stdout.write("\033[F\033[K")  # Mover hacia arriba y borrar la línea anterior
        if word == "/skip":
            skip = True
            break
        player_words.append(word)

    if not skip:
        player_score, quantity = sc.get_score_from_words(player_words, censorship)
    else:
        player_score, quantity = 0, 0

    max_score = len(censorship) * 3
    max_global_score += max_score
    global_score += player_score

    print(f"Has obtenido una puntuación de {player_score}/{max_score}!\n")
    print(f"Acertaste {quantity}/{len(censorship)}\n")
    print(f"La canción era {song['name']} de {song['artist_name']}\n")
    print(f"Las palabras censuradas eran:")
    for palabra in censorship:
        print(f"- {palabra}\n")
    print(f"La letra sin censura es: \n{chosen_section}\n")

print(f"Obtuviste un puntaje global de {global_score}/{max_global_score}")