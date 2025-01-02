import jsonlines
import multiprocessing as mp
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from database.models import TACOProblem, Solution, InputOutput
from evaluate.code_runner import CodeRunner
from database.base import engine

# Database setup
Session = sessionmaker(bind=engine)

def process_problem(problem_id):
    session = Session()
    code_runner = CodeRunner(debug=True)
    retries = 0
    data_entry = None

    while retries < 5:
        solution = session.query(Solution).filter(
            Solution.problem_id == problem_id
        ).order_by(func.random()).first()

        if not solution:
            break

        test_cases = session.query(InputOutput).filter(
            InputOutput.problem_id == problem_id
        ).all()

        elapsed_time = 0
        tested_ids = []

        for test_case in test_cases:
            test_input = {"input": test_case.input_text, "output": test_case.output_text}
            result = code_runner.run_test(test_input, None, solution.solution_text)

            if result is None or not result[0]:
                retries += 1
                break

            elapsed_time += result[1]
            tested_ids.append(test_case.id)

            if elapsed_time >= 2.0:
                break

        if retries >= 5 or not tested_ids:
            break

        repeat_count = max(1, int(2.0 / elapsed_time)) if elapsed_time < 2.0 else 1
        data_entry = {
            "problem_id": problem_id,
            "tested_ids": tested_ids,
            "repeat_count": repeat_count
        }
        break

    session.close()
    return data_entry


def test_problems():
    session = Session()
    problems = session.query(TACOProblem).filter(
        TACOProblem.fn_name.is_(None)
    ).all()
    problem_ids = [problem.id for problem in problems]

    batch_size = 100
    data_batch = []

    with mp.Pool(mp.cpu_count()) as pool:
        for data_entry in tqdm(pool.imap_unordered(process_problem, problem_ids), desc="Testing Problems", unit="problem"):
            if data_entry:
                data_batch.append(data_entry)
                if len(data_batch) >= batch_size:
                    with jsonlines.open("tmp_file/test_results_io.jsonl", mode="a") as writer:
                        writer.write_all(data_batch)
                    data_batch.clear()

    if data_batch:
        with jsonlines.open("tmp_file/test_results_io.jsonl", mode="a") as writer:
            writer.write_all(data_batch)

    session.close()


if __name__ == "__main__":
    test_problems()
