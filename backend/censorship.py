import spacy
import random


# Cargar el modelo de lenguaje en inglés
nlp = spacy.load("en_core_web_sm")
nlp_es = spacy.load("es_core_news_sm")

def get_nlp(LANG="EN"):
    if LANG == "EN":
        return nlp
    else:
        return nlp_es

# Fragmento de la canción
letra2 = """I'm working late 'cause I'm a singer
Oh, he looks so cute wrapped around my finger
My twisted humor make him laugh so often
My honey bee, come and get this pollen
Too bad your ex don't do it for ya
Walked in and dream-came-trued it for ya
Soft skin and I perfumed it for ya (yes)
I know I Mountain Dew it for ya (yes)
That morning coffee, brewed it for ya (yes)
One touch and I brand-newed it for ya (stupid)"""

letra = """Me quedo con vos, yo sigo de largo, voy a buscarte
Qué noche mágica ciudad de Buenos Aires
Se queman las horas, de esta manera nadie me espera
Cómo me gusta verte caminar así
Me quedo con vos, yo sigo de largo, voy a buscarte
Me mata cómo te movés por todas partes
Se queman las horas, de esta manera nadie me espera
Cómo me gusta verte caminar así"""

# Función para detectar palabras clave (verbos, sustantivos, adjetivos)
def detectar_palabras_clave(doc):
    palabras_clave = []
    for token in doc:
        if token.pos_ in ["VERB", "NOUN", "ADJ"]:
            palabras_clave.append(token.text)
    return palabras_clave

# Función para detectar frases nominales de más de una palabra
def detectar_frases_nominales(doc):
    frases_nominales = []
    for chunk in doc.noun_chunks:
        if len(chunk) > 1:  # Solo consideramos frases con más de una palabra
            frases_nominales.append(chunk.text)
    return frases_nominales

def censurar_palabras_en_texto_original(letra, palabras_censuradas):
    
    return censurar_palabras_en_texto_primera_ocurrencia(letra, palabras_censuradas)
    '''
    resultado = []
    censuras_efectuadas = []  # Lista para registrar las palabras/frases censuradas en el orden de aparición

    # Procesamos la letra línea por línea
    for linea in letra.split("\n"):
        nueva_linea = []
        palabras_linea = linea.split()  # Separamos cada línea en palabras
        
        i = 0
        while i < len(palabras_linea):
            palabra_actual = palabras_linea[i]
            censurada = False

            # Comprobamos si la palabra actual forma parte de una frase nominal o palabra a censurar
            for frase in palabras_censuradas:
                frase_dividida = frase.split()

                # Verificamos si la palabra actual coincide con el inicio de una frase nominal o palabra clave
                if palabras_linea[i:i + len(frase_dividida)] == frase_dividida:
                    # Añadimos un "___" por cada palabra de la frase censurada
                    nueva_linea.extend(["___"] * len(frase_dividida))
                    # Añadimos cada palabra de la frase censurada como elementos separados
                    censuras_efectuadas.extend(frase_dividida)
                    i += len(frase_dividida)  # Saltamos el resto de la frase censurada
                    censurada = True
                    break

            if not censurada:
                nueva_linea.append(palabra_actual)  # Si no está censurada, añadimos la palabra tal cual
                i += 1
        
        resultado.append(" ".join(nueva_linea))

    # Unimos todas las líneas censuradas
    return "\n".join(resultado), censuras_efectuadas
    '''
    
def censurar_palabras_en_texto_primera_ocurrencia(letra, palabras_censuradas):
    resultado = []
    censuras_efectuadas = []  # Lista para registrar las palabras/frases censuradas en el orden de aparición
    palabras_censuradas_set = set()  # Para verificar las palabras ya censuradas

    for linea in letra.split("\n"):
        nueva_linea = []
        palabras_linea = linea.split()

        i = 0
        while i < len(palabras_linea):
            palabra_actual = palabras_linea[i]
            censurada = False

            for frase in palabras_censuradas:
                frase_dividida = frase.split()

                # Verificamos si la palabra actual coincide con el inicio de una frase nominal o palabra clave
                if palabras_linea[i:i + len(frase_dividida)] == frase_dividida:
                    if frase not in palabras_censuradas_set:  # Censuramos solo la primera ocurrencia
                        nueva_linea.extend(["___"] * len(frase_dividida))
                        censuras_efectuadas.extend(frase_dividida)
                        palabras_censuradas_set.add(frase)
                        censurada = True
                        i += len(frase_dividida)
                        break

            if not censurada:
                nueva_linea.append(palabra_actual)
                i += 1

        resultado.append(" ".join(nueva_linea))

    return "\n".join(resultado), censuras_efectuadas

def censurar_palabras_en_texto_random(letra, palabras_censuradas):
    resultado = []
    censuras_efectuadas = []
    
    for frase in palabras_censuradas:
        # Contar todas las ocurrencias de la frase en el texto
        ocurrencias = []
        lineas = letra.split("\n")
        for linea_idx, linea in enumerate(lineas):
            palabras_linea = linea.split()
            i = 0
            while i < len(palabras_linea):
                if palabras_linea[i:i + len(frase.split())] == frase.split():
                    ocurrencias.append((linea_idx, i))
                i += 1

        if ocurrencias:
            # Escoger una ocurrencia aleatoria para censurar
            ocurrencia_random = random.choice(ocurrencias)
            linea_idx, palabra_idx = ocurrencia_random
            palabras_linea = lineas[linea_idx].split()
            palabras_linea[palabra_idx:palabra_idx + len(frase.split())] = ["___"] * len(frase.split())
            lineas[linea_idx] = " ".join(palabras_linea)
            censuras_efectuadas.append(frase)

    return "\n".join(lineas), censuras_efectuadas

# Función para eliminar las palabras clave que ya están incluidas en las frases nominales
def eliminar_palabras_superpuestas(palabras_clave, frases_nominales):
    palabras_a_eliminar = set()
    for frase in frases_nominales:
        palabras_frase = frase.split()  # Dividimos la frase en palabras
        for palabra in palabras_frase:
            palabras_a_eliminar.add(palabra)  # Añadimos las palabras de la frase nominal a eliminar de las palabras clave
    palabras_clave_filtradas = [palabra for palabra in palabras_clave if palabra not in palabras_a_eliminar]
    return palabras_clave_filtradas

# Función para procesar línea por línea con spaCy y evitar errores con saltos de línea
def procesar_lineas_con_spacy(letra, LANG="EN"):
    frases_nominales_totales = []
    palabras_clave_totales = []
    lineas = letra.split("\n")
    for linea in lineas:
        doc = get_nlp(LANG)(linea)
        frases_nominales = detectar_frases_nominales(doc)
        palabras_clave = detectar_palabras_clave(doc)
        frases_nominales_totales.extend(frases_nominales)
        palabras_clave_totales.extend(palabras_clave)
    return frases_nominales_totales, palabras_clave_totales

# Función para censurar y guardar el resultado en un archivo
def censurar(letra, save=False, debug=False, percentage=0.5, LANG="EN"):
    # Procesamos el texto línea por línea
    frases_nominales, palabras_clave = procesar_lineas_con_spacy(letra, LANG)
    
    
    
    # Eliminamos las palabras clave que se superponen con las frases nominales
    palabras_clave_filtradas = eliminar_palabras_superpuestas(palabras_clave, frases_nominales)
    
    
    
    # Combinamos las palabras clave filtradas y las frases nominales
    censura_total = palabras_clave_filtradas + frases_nominales
    
    # Censuramos un porcentaje de palabras y frases clave
    porcentaje_censura = percentage  # Ajusta el porcentaje de censura
    num_censurados = int(len(censura_total) * porcentaje_censura)
    palabras_censuradas = random.sample(censura_total, num_censurados)

    
    # Censurar directamente en el texto original
    letra_censurada, censuras_efectuadas = censurar_palabras_en_texto_original(letra, palabras_censuradas)
    
    if debug:
        print(f"Las frases nominales son: {frases_nominales} \n")
        print(f"Las palabras clave son: {palabras_clave} \n")
        print(f"Las palabras clave filtradas son: {palabras_clave_filtradas} \n")
        print(f"Las palabras a censurarse elegidas al azar son: \n{palabras_censuradas} \n")
    
    if save:
        # Guardar la salida en un archivo
        with open("letra_censurada.txt", 'w') as archivo:
            archivo.write(letra_censurada + "\n\n")
            archivo.write("Palabras censuradas en orden:\n")
            for palabra in censuras_efectuadas:
                archivo.write(f"- {palabra}\n")
        print(f"La letra censurada ha sido guardada en 'letra_censurada.txt'.")
    
    return letra_censurada, censuras_efectuadas

# Censurar y guardar
#letra_censurada, censuras = censurar_y_guardar_en_archivo(letra)

# Mostrar confirmación en la consola
