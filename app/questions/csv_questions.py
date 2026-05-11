from dataclasses import dataclass

import csv

import os

@dataclass
class Question:
    id: int
    q: str
    trait: str
    reverse: bool
    category: str # type of q, so Big 5, Quality Check, jungian

def load_questions(filepath: str) -> list[Question]:
    questions = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(
                Question(
                    id=row["id"],
                    q=row["question"],
                    trait=row["trait"],
                    reverse=row["reverse"].lower() == "true",
                    category=row["category"]

                )
            )
    return questions


QUESTIONS_DIR = os.path.dirname(__file__)
big_five_questions = load_questions(os.path.join(QUESTIONS_DIR))