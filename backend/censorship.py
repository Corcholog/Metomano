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

# Función para detectar palabras clave (verbos, sustantivos, adjetivos)
def detectar_palabras_clave(doc):
    palabras_clave = []
    for token in doc:
        if token.pos_ in ["VERB", "NOUN", "ADJ", "ADV"]:
            palabras_clave.append(token.text)
    return palabras_clave

# Función para detectar frases nominales de más de una palabra
def detectar_frases_nominales(doc):
    frases_nominales = []
    for chunk in doc.noun_chunks:
        if len(chunk) > 1:  # Solo consideramos frases con más de una palabra
            frases_nominales.append(chunk.text)
    return frases_nominales

# Calcular el total de palabras en el texto
def calcular_total_palabras(letra):
    return sum(len(line.split()) for line in letra.split("\n"))

# Función que asigna un "peso" a cada línea basado en la cantidad de palabras
def calcular_pesos_lineas(letra):
    pesos = []
    for linea in letra.split("\n"):
        pesos.append(len(linea.split()))
    return pesos

# Nueva función para obtener una lista completa de las palabras a censurar (con su peso en cantidad de palabras)
def obtener_censura_completa(palabras_clave_filtradas, frases_nominales):
    censura_completa = [(palabra, 1) for palabra in palabras_clave_filtradas]
    for frase in frases_nominales:
        censura_completa.append((frase, len(frase.split())))  # El peso de la frase es el número de palabras
    return censura_completa

# Función para censurar el texto, permitiendo censura parcial dentro de frases nominales palabra por palabra
def censurar_por_distribucion_prioridad_final(letra, censura_completa, palabras_a_censurar):
    resultado = []
    censuras_efectuadas = []
    palabras_censuradas_set = set()  # Para evitar censurar la misma palabra/frase muchas veces

    lineas = letra.split("\n")
    pesos = calcular_pesos_lineas(letra)

    # Iterar sobre cada línea y distribuir la censura
    total_palabras = calcular_total_palabras(letra)
    palabras_censuradas_efectivas = 0  # Llevar el control de palabras efectivamente censuradas

    for idx, linea in enumerate(lineas):
        palabras_linea = linea.split()
        censuras_por_linea = max(1, int((pesos[idx] / total_palabras) * palabras_a_censurar))  # Al menos 1 censura por línea
        censuras_realizadas = 0
        nueva_linea = palabras_linea[:]  # Copia de la línea actual
        
        # Lista temporal para almacenar censuras en el orden correcto
        censuras_temporales = []

        # Procesar de derecha a izquierda para priorizar censura al final
        i = len(palabras_linea) - 1
        while i >= 0 and censuras_realizadas < censuras_por_linea:
            palabra_actual = palabras_linea[i]
            censurada = False

            # Intentar censurar primero frases nominales completas
            for frase, peso in censura_completa:
                frase_dividida = frase.split()

                # Verificamos si la palabra/frase coincide y si no ha sido censurada
                if palabras_linea[max(0, i - len(frase_dividida) + 1):i + 1] == frase_dividida:
                    if frase not in palabras_censuradas_set and censuras_realizadas + peso <= censuras_por_linea:
                        # Censurar palabra por palabra dentro de la frase nominal
                        for j in range(len(frase_dividida)-1, -1, -1):
                            nueva_linea[i - j] = "___"
                            censuras_temporales.insert(0, frase_dividida[j])  # Guardar cada palabra en el orden original
                        palabras_censuradas_set.add(frase)
                        censurada = True
                        censuras_realizadas += peso
                        palabras_censuradas_efectivas += peso
                        i -= len(frase_dividida)  # Saltar las palabras censuradas
                        break

            # Si no se censura la frase completa, intentar con las subpalabras (de derecha a izquierda)
            if not censurada:
                for frase, peso in censura_completa:
                    frase_dividida = frase.split()

                    # Si encontramos una frase, censuramos solo algunas palabras dentro de la frase
                    if frase in linea and len(frase_dividida) > 1:
                        for sub_palabra in reversed(frase_dividida):  # Procesar subpalabras de derecha a izquierda
                            if sub_palabra == palabra_actual and sub_palabra not in palabras_censuradas_set:
                                nueva_linea[i] = "___"  # Censurar solo la sub_palabra
                                censuras_temporales.insert(0, sub_palabra)  # Guardar en el orden original
                                palabras_censuradas_set.add(sub_palabra)
                                censuras_realizadas += 1
                                palabras_censuradas_efectivas += 1
                                censurada = True
                                break
            
            if not censurada:
                i -= 1  # Continuar hacia la palabra anterior

        # Agregar las censuras de la línea en el orden original
        censuras_efectuadas.extend(censuras_temporales)

        resultado.append(" ".join(nueva_linea))

    # Ajustar el resultado si se censuraron menos palabras de las necesarias
    if palabras_censuradas_efectivas < palabras_a_censurar:
        print(f"Advertencia: Se censuraron menos palabras de las esperadas: {palabras_censuradas_efectivas}/{palabras_a_censurar}")
        
    return "\n".join(resultado), censuras_efectuadas  # Devolvemos las censuras en el orden correcto

# Función principal de censura
def censurar(letra, LANG, save=False, debug=False, porcentaje_censura=0.5):
    # Procesamos el texto línea por línea
    frases_nominales, palabras_clave = procesar_lineas_con_spacy(letra, LANG)
    
    # Eliminamos las palabras clave que se superponen con las frases nominales
    palabras_clave_filtradas = eliminar_palabras_superpuestas(palabras_clave, frases_nominales)
    
    # Obtener la censura completa con frases nominales y palabras clave, y calcular los pesos
    censura_completa = obtener_censura_completa(palabras_clave_filtradas, frases_nominales)
    
    # Calcular el total de palabras a censurar basado en el porcentaje
    total_palabras = calcular_total_palabras(letra)
    palabras_a_censurar = int(total_palabras * porcentaje_censura)

    # Censuramos usando el enfoque de distribución priorizando la censura de derecha a izquierda pero manteniendo el orden original
    letra_censurada, censuras_efectuadas = censurar_por_distribucion_prioridad_final(letra, censura_completa, palabras_a_censurar)
    
    if debug:
        print(f"Las frases nominales son: {frases_nominales} \n")
        print(f"Las palabras clave son: {palabras_clave} \n")
        print(f"Las palabras clave filtradas son: {palabras_clave_filtradas} \n")
        print(f"Las palabras/frases censuradas son: \n{censuras_efectuadas} \n")
    
    if save:
        with open("letra_censurada.txt", 'w') as archivo:
            archivo.write(letra_censurada + "\n\n")
            archivo.write("Palabras censuradas en orden:\n")
            for palabra in censuras_efectuadas:
                archivo.write(f"- {palabra}\n")
        print(f"La letra censurada ha sido guardada en 'letra_censurada.txt'.")
    
    return letra_censurada, censuras_efectuadas


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


