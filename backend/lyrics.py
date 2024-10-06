import re
def get_lyrics(song, artist, genius):
    response = genius.search_song(song, artist)
    if response:
        return clean_lyrics(response.lyrics)
    return None

def clean_lyrics(lyrics):
    if lyrics:
        lyrics = re.sub(r'^.*?Lyrics', 'Lyrics', lyrics, flags=re.DOTALL)
        lyrics = re.sub(r"See .* LiveGet tickets as low as \$\d+\n?", "\n", lyrics)
        lyrics = re.sub(r"\d+Embed", "", lyrics)

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
