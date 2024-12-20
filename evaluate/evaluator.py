import os
import multiprocessing
import jsonlines
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker, Session

from tqdm import tqdm
from database.models import TACOProblem, Solution, InputOutput, ValidSolution
from database.base import engine
from evaluate.code_runner import CodeRunner
from typing import List, Dict, Any


def create_db_session():
    """创建数据库会话"""
    Session = sessionmaker(bind=engine)
    return Session()


def get_problems_to_test(session: Session) -> List[TACOProblem]:
    return session.query(TACOProblem).filter(
        TACOProblem.fn_name.is_(None),
        TACOProblem.is_tested == 0,
        TACOProblem.is_valid == 1
    ).all()


def process_problem(problem_id: int) -> List[Dict[str, Any]]:
    session = create_db_session()
    try:
        problem = session.query(TACOProblem).get(problem_id)
        solutions = session.query(Solution).filter(
            Solution.problem_id == problem.id,
            Solution.is_tested == 0
        ).order_by(func.random()).limit(20).all()
        test_cases = session.query(InputOutput).filter(
            InputOutput.problem_id == problem.id
        ).all()

        test_cases = test_cases * problem.test_repeat_time

        code_runner = CodeRunner(debug=True)
        valid_solutions = []

        for solution in solutions:
            try:
                all_test_inputs = [
                    {
                        "input": test_case.input_text,
                        "output": test_case.output_text
                    } for test_case in test_cases
                ]
                success, elapsed_time = code_runner.run_tests(all_test_inputs, problem.fn_name, solution.solution_text)
                if success:
                    valid_solution = ValidSolution(
                        problem_id=problem.id,
                        solution_id=solution.id,
                        solution_text=solution.solution_text,
                        run_time=elapsed_time
                    )
                    valid_solutions.append(valid_solution)
                    solution.is_tested = 1

            except Exception as e:
                print(f"Error testing solution for problem {problem.id}: {e}")
        problem.is_tested = 1
        session.add_all(valid_solutions)
        session.commit()

        return [
            {
                "problem_id": problem.id,
                "valid_solution_count": len(valid_solutions)
            }
        ]

    except Exception as e:
        print(f"Error processing problem {problem_id}: {e}")
        return []

    finally:
        session.close()


def parallel_test(num_processes: int = None):
    if num_processes is None:
        num_processes = os.cpu_count()
    session = create_db_session()
    try:
        problem_ids = [
            problem.id for problem in get_problems_to_test(session)
        ]
        with multiprocessing.Pool(processes=num_processes) as pool:
            results = list(tqdm(
                pool.imap(process_problem, problem_ids),
                total=len(problem_ids),
                desc="测试问题",
                unit="问题"
            ))
        with jsonlines.open("test_results.jsonl", mode="w") as writer:
            for result_list in results:
                writer.write_all(result_list)

    finally:
        session.close()


if __name__ == "__main__":
    parallel_test(num_processes=16)