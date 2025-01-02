import json

from sqlalchemy.orm import sessionmaker

from database.models import TACOProblem, InputOutput
from database.base import engine

# Database setup
Session = sessionmaker(bind=engine)
session = Session()

jsonl_file_path = "tmp_file/test_results_io.jsonl"
def main():
    valid_problem_ids = []
    with open(jsonl_file_path, "r") as file:
        for line in file:
            data = json.loads(line)
            problem_id = data["problem_id"]
            valid_problem_ids.append(problem_id)
            tested_ids = set(data["tested_ids"])
            repeat_count = data["repeat_count"]
            problem = session.query(TACOProblem).filter_by(id=problem_id).first()
            if problem:
                problem.test_repeat_time = repeat_count
            session.query(InputOutput).filter(
                InputOutput.problem_id == problem_id,
                InputOutput.id.notin_(tested_ids)
            ).delete(synchronize_session="fetch")
    session.query(TACOProblem).filter(
        TACOProblem.id.in_(valid_problem_ids)
    ).update({"is_valid": 1}, synchronize_session="fetch")
    session.commit()
    session.close()

if __name__ == "__main__":
    main()