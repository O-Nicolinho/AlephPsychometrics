from app.questions.csv_questions import csv_questions, Question


# By default (After loading the questions), we have access to a Question array.
# Since we're going to need to be searching for a matching Question ID every iteration
# in the scoring functions, we need a more efficient way than just going through the array each time.
# So we turn the Question array into a dict where the keys are the QIDs and the values are the Question objects
def return_question_map_filtered_by(filt) -> dict[int, Question]:
    result = {}
    filt = filt.lower()
    for q in csv_questions:
        match filt:
            case "big5":
                if q.category == "big5":
                    result[q.id] = q
                else:
                    continue
            case "jung":
                if q.category == "jung":
                    result[q.id] = q
                else:
                    continue
            case "filter":
                if q.category == "filter":
                    result[q.id] = q
                else:
                    continue
            case _:
                result[q.id] = q
    return result


# responses include qid: answer (1-5)
# Here we take a dict of responses {QID:ans}, and we need to give it  abig 5 score.
def score_big_five(responses: dict[int,int]) -> dict[str, float]:

    # First we get a dict of only questions that are relevant (have the big5 category)
    bigfivedict = return_question_map_filtered_by("big5")

    # we create the dict where we will be keeping track of each trait's score
    output = {"o": 0, "c": 0, "e": 0, "a":0, "n": 0}

    # we iterate over the response to all questions (Coming from the frontend)
    for qid, ans in responses.items():

        # we check that the QID of the response corresponds to a big5 question
        if qid not in bigfivedict:
            continue

        # for reverse questions, higher ans (5) corresponds to the lowest increase in the trait,
        # and vice versa
        elif bigfivedict[qid].reverse == True:
            output[bigfivedict[qid].trait] = output[bigfivedict[qid].trait] + (6-ans)
        else:
            output[bigfivedict[qid].trait] = output[bigfivedict[qid].trait] + ans

    return output

def score_jung(responses: dict[int,int]) -> dict[str, float]:
    # a dictionary indexed by qid with only questions with the jungian category
    jungdict = return_question_map_filtered_by("jung")

    output = {"ne": 0, "ni": 0, "se": 0, "si": 0, "te": 0, "ti": 0, "fe": 0, "fi": 0}

    for qid, ans in responses.items():
        if qid not in jungdict:
            continue
        else:
            output[jungdict[qid].trait] = output[jungdict[qid].trait] + ans

    for key in output:
        output[key] = float((output[key])-4)/ 16
    return output





