from app.services.scoring import return_question_map_filtered_by
from app.questions.csv_questions import LOWEST_QID, HIGHEST_QID

#thresholds:
THRESHOLD1 = 0.62
THRESHOLD2 = 0.6
THRESHOLD3 = 0.95


def validate_responses(responses: dict[int,int]) -> tuple[bool,str]:

    valid_count = 0

    # qid_dict contains a dict of every question.
    # at each iteration, we pop off the qid we see, and at the end
    # we expect it to be empty, otherwise there are questions in our
    # database that were not answered, so the submission is incomplete.

    qid_dict = return_question_map_filtered_by("_")


    for qid, ans in responses.items():
        if not isinstance(qid, int):
            return (False, f"Non integer QID detected. QID: {qid}")
        if not isinstance(ans, int):
            return (False, f"Non integer answer detected. ans: {ans}")
        if ans > 5 or ans < 1:
            return (False, f"Invalid response, outside 1-5. (QID, Ans): ({qid}, {ans})")

        if qid < LOWEST_QID or qid > HIGHEST_QID:
            return (False, f"Invalid QID. QID: {qid}")

        pop = qid_dict.pop(qid, "empty")
        if pop == "empty":
            return (False, f"Invalid QID: {qid}")


    if qid_dict:
        return (False, "Some questions have no answers.")


    return True, ""


def crit_one_score(responses:dict[int,int]) -> float:

    # qid 64 and 65 are main filter questions
    # almost all people will answer strongly disagree to both of them,
    # so a score of 5 on both of them is highly suspicious.

    q1_ans = responses[64]
    q2_ans = responses[65]

    # formula:
    # (q1^2 + q2^2) / 25

    return (q1_ans**2 + q2_ans**2) / 50



def crit_two_score(responses:dict[int,int]) -> float:
    # we have two consistency checks:
    # 12 & 66, which are inverses of each other
    # 17 & 22, are also inverses of each other.

    qa1 = responses[12]
    qa2 = 6-responses[66] # we reverse the score

    qb1 = responses[17]
    qb2 = 6-responses[22]

    return ( (qa1-qa2)**2 + (qb1-qb2)**2 ) / 32


def crit_three_score(responses:dict[int,int]) -> dict[int,float]:
    # answer counts:
    count1 = sum(1 for v in responses.values() if v == 1)
    count2 = sum(1 for v in responses.values() if v == 2)
    count3 = sum(1 for v in responses.values() if v == 3)
    count4 = sum(1 for v in responses.values() if v == 4)
    count5 = sum(1 for v in responses.values() if v == 5)

    total = len(responses)

    return {1 : count1/total, 2: count2/total, 3: count3/total, 4: count4/total, 5: count5/total}

def reliability_score(responses:dict[int,int]) -> bool:
    crit1 = crit_one_score(responses)
    crit2 = crit_two_score(responses)
    crit3 = crit_three_score(responses)

    if crit1 >= THRESHOLD1 or crit2 >= THRESHOLD2 or max(crit3) >= THRESHOLD3:
        return False
    else:
        return True

