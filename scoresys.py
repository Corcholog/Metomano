import unicodedata

def quitar_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFKD', texto) 
        if not unicodedata.combining(c)
    )

def get_score_from_words(user_input, censorship, score_add = 3) -> float:
    score = 0
    streak = True
    well_answered=0
    #tener en cuenta tambien el tiempo para sumar
    
    for i in range(0, len(censorship)):
        us_in = user_input[i].lower()
        cens = censorship[i].lower()
        if (us_in == cens) or (quitar_acentos(us_in) == quitar_acentos(cens)):
            if streak:
                score += score_add
            else:
                score+=1
            well_answered+=1
        else:
            streak = False
            score+=0
    return score, well_answered
            
def get_score_from_questions(user_input, answers, score_add = 5) -> float:
    # hacer mejor, diciendo a cual pregunta le pegaste
    score = 0
    quantity = 0
    
    for i in range(0, len(answers)):
        if user_input[i].lower() == answers[i].lower():
            quantity+=1
            score += score_add
        else:
            score+=0
    return score, quantity
            
def get_score(user_lyrics, user_answers, censorship, answers):
    return get_score_from_words(user_lyrics, censorship) #+ get_score_from_questions(user_answers, answers)
        