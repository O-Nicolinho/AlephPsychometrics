from app.services.scoring import return_question_map_filtered_by
from app.questions.csv_questions import LOWEST_QID, HIGHEST_QID
def validate_responses(responses: dict[int,int]) -> tuple[bool,str]:

    valid_count = 0

    # qid_dict contains a dict of every question.
    # at each iteration, we pop off the qid we see, and at the end
    # we expect it to be empty, otherwise there are questions in our
    # database that were not answered, so the submission is incomplete.

    qid_dict = return_question_map_filtered_by()


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



def reliability_score(responses:dict[int,int]) -> int:
    print("WIP")