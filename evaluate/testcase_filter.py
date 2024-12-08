import jsonlines
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from database.models import TACOProblem, Solution, InputOutput
from evaluate.code_runner import CodeRunner
from database.base import engine

# Database setup
Session = sessionmaker(bind=engine)
session = Session()


def test_problems():
    problems = session.query(TACOProblem).filter(
        TACOProblem.fn_name.is_(None)
    ).all()

    code_runner = CodeRunner(debug=True)
    batch_size = 100
    data_batch = []

    # 修改后的测试循环
    for problem in tqdm(problems, desc="Testing Problems", unit="problem"):
        retries = 0
        while retries < 5:
            solution = session.query(Solution).filter(
                Solution.problem_id == problem.id
            ).order_by(func.random()).first()

            if not solution:
                break

            test_cases = session.query(InputOutput).filter(
                InputOutput.problem_id == problem.id
            ).all()

            elapsed_time = 0
            tested_ids = []
            for test_case in test_cases:
                test_input = {"input": test_case.input_text, "output": test_case.output_text}
                result = code_runner.run_test(test_input, problem.fn_name, solution.solution_text)
                if result is None or not result[0]:
                    retries += 1
                    break

                elapsed_time += result[1]
                tested_ids.append(test_case.id)

                if elapsed_time >= 1.0:
                    break

            if retries >= 5:
                break

            if tested_ids:
                repeat_count = max(1, int(1.0 / elapsed_time)) if elapsed_time < 1.0 else 1
                data_batch.append({
                    "problem_id": problem.id,
                    "tested_ids": tested_ids,
                    "repeat_count": repeat_count
                })
                if len(data_batch) >= batch_size:
                    with jsonlines.open("test_results_io.jsonl", mode="a") as writer:
                        writer.write_all(data_batch)
                    data_batch.clear()

            break
    if data_batch:
        with jsonlines.open("test_results_io.jsonl", mode="a") as writer:
            writer.write_all(data_batch)

    session.close()


if __name__ == "__main__":
    test_problems()
