import json
import random
import sys
import time
from censorship import censurar
from dotenv import load_dotenv
from collections import Counter
import os, re
import spoti as sp
import scoresys as sc
from lyricsgenius import Genius
import lyrics as ly

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

playlist_id = "37i9dQZF1DWSo7PX7dbgH8"#"37i9dQZF1E36hA3DgVWZo8" #"37i9dQZF1DWSo7PX7dbgH8" #playlist rock nacional, tiene bugs je

#short_n_sweet = sp.get_album_tracks(token, album_id=album_play, artist_name=sp.get_artist_name(token, sp.get_artist_id(token, "sabrina carpenter")))

#art_id = sp.get_artist_id(token, input("Ingresa el nombre del artista para jugar: "))

#artists_ids = [art_id]

song_pool = sp.get_playlist_tracks_with_artists(token, playlist_id=playlist_id, limit=20)
#song_pool = get_song_pool(artists_ids)

game_length = 30
random_game = False  # Cambia este valor a False para obtener las canciones en orden de popularidad

if random_game:
    game_songs = random.sample(song_pool, min(game_length, len(song_pool)))
else:
    game_songs = song_pool[:game_length]

global_score = 0
max_global_score = 0
    
for song in game_songs:
    song_name = song['name']
    artist_name = song['artist_name']

    raw_lyrics = ly.get_lyrics(song['name'], song['artist_name'], genius)
    if raw_lyrics is None:
        continue
    lyrics = ly.clean_lyrics(raw_lyrics)
   
    secciones = ly.dividir_por_secciones(lyrics)
    idx = random.randint(0, len(secciones) - 1)
    chosen_section = secciones[idx]
    while len(chosen_section.split("\n")) <= 2:
        idx = random.randint(0, len(secciones) - 1)
        chosen_section = secciones[idx]
    
    censored_lyrics, censorship = censurar(chosen_section, percentage=0.5, LANG="EN")
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

    print(f"Acertaste {quantity}/{len(censorship)}\n")
    print(f"Las palabras censuradas eran: \n[ ")
    censors_str = ""
    for palabra in censorship:
        censors_str += f"({palabra}) "
    print(f"{censors_str}]\n")
    print(f"La letra sin censura es: \n{chosen_section}\n")
    
    user_answers = []
    user_answers.append(input(f"¿Cuál es el nombre de la canción?\n"))
    answers = [song_name]

    max_score += 5 * len(answers)
    question_output = sc.get_score_from_questions(user_input=user_answers, answers=answers)
    player_score += question_output[0]
    quantity_questions = question_output[1]
    print(f"La canción era {song['name']} de {song['artist_name']}\n")
    print(f"Respondiste bien {quantity_questions}/{len(answers)} preguntas\n")

    print(f"Has obtenido una puntuación de {player_score}/{max_score}!\n")
    
    
print(f"Obtuviste un puntaje global de {global_score}/{max_global_score}")