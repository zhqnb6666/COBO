# services/database_operations.py
import json

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from database.models import TACOProblem, Solution, InputOutput, ValidSolution
from loader import load_taco_dataset
from database.base import Base, engine


def create_tables():
    Base.metadata.create_all(bind=engine)


def store_taco_dataset(db: Session, data_files: str):
    try:
        dataset = load_taco_dataset(data_files)
        for idx, sample in enumerate(dataset):
            try:
                for key, value in sample.items():
                    if isinstance(value, str):
                        sample[key] = value.replace("\x00", "")

                sample["solutions"] = json.loads(sample["solutions"])
                sample["input_output"] = json.loads(sample["input_output"])
                problem = TACOProblem(
                    question=sample['question'],
                    starter_code=sample['starter_code'],
                    difficulty=sample['difficulty'],
                    raw_tags=json.dumps(sample.get('raw_tags', [])),
                    name=sample['name'],
                    source=sample['source'],
                    tags=json.dumps(sample.get('tags', [])),
                    skill_types=json.dumps(sample.get('skill_types', [])),
                    url=sample['url'],
                    expected_auxiliary_space=sample.get('Expected Auxiliary Space'),
                    time_limit=sample['time_limit'],
                    date=sample['date'],
                    picture_num=sample['picture_num'],
                    memory_limit=sample['memory_limit'],
                    expected_time_complexity=sample.get('Expected Time Complexity'),
                    fn_name=sample.get('input_output', {}).get('fn_name')
                )
                db.add(problem)
                db.flush()
                if sample.get('solutions'):
                    solutions = [
                        Solution(problem_id=problem.id, solution_text=sol)
                        for sol in sample['solutions']
                    ]
                    db.add_all(solutions)
                if sample.get('input_output', {}).get('inputs'):
                    input_outputs = [
                        InputOutput(
                            problem_id=problem.id,
                            input_text=str(inp) if inp else None,
                            output_text=str(out) if out else None
                        )
                        for inp, out in zip(
                            sample['input_output']['inputs'],
                            sample['input_output']['outputs']
                        )
                    ]
                    db.add_all(input_outputs)

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Data processing error in sample {idx}: {e}")
                db.rollback()
                continue
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error occurred: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        db.rollback()
        raise



def retrieve_problems(db: Session, limit: int = 5):
    problems = db.query(TACOProblem).limit(limit).all()
    detailed_problems = []
    for problem in problems:
        detailed_problem = {
            'id': problem.id,
            'question': problem.question,
            'difficulty': problem.difficulty,
            'solutions': [sol.solution_text for sol in problem.solutions],
            'input_outputs': [
                {
                    'input': io.input_text,
                    'output': io.output_text
                } for io in problem.input_outputs
            ],
            'fn_name': problem.fn_name
        }
        detailed_problems.append(detailed_problem)

    return detailed_problems