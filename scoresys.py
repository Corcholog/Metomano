def get_score_from_words(user_input, censorship, score_add = 3) -> float:
    score = 0
    streak = True
    well_answered=0
    #tener en cuenta tambien el tiempo para sumar
    
    for i in range(0, len(censorship)):
        if user_input[i] == censorship[i]:
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
    score = 0
    
    for i in range(0, len(answers)):
        if user_input[i] == answers[i]:
            score += score_add
        else:
            score+=0
            
def get_score(user_lyrics, user_answers, censorship, answers):
    return get_score_from_words(user_lyrics, censorship) #+ get_score_from_questions(user_answers, answers)
        