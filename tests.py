def dividir_por_secciones(lyrics):
    # Dividimos la letra en secciones usando líneas vacías como separadores
    secciones = lyrics.split("\n\n")  # Cada línea vacía separa una sección
    return secciones

# Ejemplo de uso con la letra proporcionada
lyrics = """Now he's thinkin' 'bout me every night, oh
Is it that sweet? I guess so
Say you can't sleep, baby, I know
That's that me espresso
Move it up, down, left, right, oh
Switch it up like Nintendo
Say you can't sleep, baby, I know
That's that me espresso

I can't relate to desperation
My 'give-a-fucks' are on vacation
And I got this one boy, and he won't stop calling
When they act this way, I know I got 'em

Too bad your ex don't do it for ya
Walked in and dream-came-trued it for ya
Soft skin and I perfumed it for ya (yes)
I know I Mountain Dew it for ya (yes)
That morning coffee, brewed it for ya (yes)
One touch and I brand-newed it for ya

Now he's thinkin' 'bout me every night, oh
Is it that sweet? I guess so
Say you can't sleep, baby, I know
That's that me espresso
Move it up, down, left, right, oh
Switch it up like Nintendo
Say you can't sleep, baby, I know
That's that me espresso

Is it that sweet? I guess so

I'm working late 'cause I'm a singer
Oh, he looks so cute wrapped around my finger
My twisted humor make him laugh so often
My honey bee, come and get this pollen

Too bad your ex don't do it for ya
Walked in and dream-came-trued it for ya
Soft skin and I perfumed it for ya (yes)
I know I Mountain Dew it for ya (yes)
That morning coffee, brewed it for ya (yes)
One touch and I brand-newed it for ya (stupid)

Now he's thinkin' 'bout me every night, oh
Is it that sweet? I guess so
Say you can't sleep, baby, I know
That's that me espresso
Move it up, down, left, right, oh
Switch it up like Nintendo
Say you can't sleep, baby, I know
That's that me espresso (yes)

Thinkin' 'bout me every night, oh
Is it that sweet? I guess so (yes)
Say you can't sleep, baby, I know
That's that me espresso (yes)
Move it up, down, left, right, oh
Switch it up like Nintendo (yes)
Say you can't sleep, baby, I know
That's that me espresso

Is it that sweet? I guess so
Mm, that's that me espresso"""

# Dividimos la letra en conjuntos de 4 líneas
secciones = dividir_por_secciones(lyrics)

# Imprimimos los conjuntos de 4 líneas
for i, seccion in enumerate(secciones, 1):
    print(f"Conjunto {i}:\n{seccion}\n")
    print()
