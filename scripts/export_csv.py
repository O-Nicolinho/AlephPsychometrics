# scripts/export_csv.py
import csv
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models import QuizSession, ItemResponse


def export():
    db = SessionLocal()

    sessions = db.query(QuizSession).all()

    if not sessions:
        print("No sessions found.")
        db.close()
        return

    # get all question IDs from first session
    sample_responses = db.query(ItemResponse).filter(
        ItemResponse.session_id == sessions[0].id
    ).order_by(ItemResponse.question_id).all()
    question_ids = [r.question_id for r in sample_responses]

    with open("export.csv", "w", newline="") as f:
        writer = csv.writer(f)

        header = [
            "session_id",
            "started_at",
            "completed_at",
            "credibility_score",
            "is_repeat",
            "self_reported_jung",
            "type_confidence",
            "reddit_username",
            "openness",
            "conscientiousness",
            "extraversion",
            "agreeableness",
            "neuroticism",
            "animal",
            "summary",
        ]
        header += [f"q_{qid}" for qid in question_ids]
        writer.writerow(header)

        for session in sessions:
            row = [
                str(session.id),
                session.started_at,
                session.completed_at,
                session.credibility_score,
                session.is_repeat,
                session.self_reported_jung,
                session.type_confidence,
                session.reddit_username,
            ]

            if session.big_five_score:
                row += [
                    session.big_five_score.openness,
                    session.big_five_score.conscientiousness,
                    session.big_five_score.extraversion,
                    session.big_five_score.agreeableness,
                    session.big_five_score.neuroticism,
                ]
            else:
                row += [None, None, None, None, None]

            if session.personality_summary:
                row += [
                    session.personality_summary.animal,
                    session.personality_summary.summary,
                ]
            else:
                row += [None, None]

            responses = db.query(ItemResponse).filter(
                ItemResponse.session_id == session.id
            ).order_by(ItemResponse.question_id).all()
            response_map = {r.question_id: r.answer for r in responses}

            for qid in question_ids:
                row.append(response_map.get(qid, None))

            writer.writerow(row)

    db.close()
    print(f"Exported {len(sessions)} sessions to export.csv")


if __name__ == "__main__":
    export()