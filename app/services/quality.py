from app.questions.csv_questions import csv_questions

def validate_responses(responses: dict[int,int]) -> tuple[bool,str]:
    print()