import os
import random
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import asc, desc
from tqdm import tqdm
import statistics

from database.models import TACOProblem, Solution, ValidSolution, InputOutput
from database.base import engine
from evaluate.code_runner import CodeRunner
from typing import List, Dict, Any, Optional


def create_db_session():
    """Create a database session"""
    Session = sessionmaker(bind=engine)
    return Session()


def get_problems_to_test(session: Session) -> List[TACOProblem]:
    """
    Select problems that are valid but not yet tested,
    ordered by problem id in ascending order
    """
    return session.query(TACOProblem).filter(
        TACOProblem.is_tested == 0,
        TACOProblem.is_valid == 1
    ).order_by(desc(TACOProblem.id)).all()


def get_random_solutions_for_problem(session: Session, problem_id: int, num_solutions: int = 20) -> List[Solution]:
    """
    Retrieve a random set of solutions for a given problem
    """
    solutions = session.query(Solution).filter(
        Solution.problem_id == problem_id
    ).all()

    # Randomly select solutions, or all if less than requested number
    random_solutions = random.sample(solutions, min(len(solutions), num_solutions))
    return random_solutions


def run_solution_tests(
        code_runner: CodeRunner,
        problem: TACOProblem,
        solution_text: str,
        test_cases: List[InputOutput]
) -> Optional[float]:
    """
    Run tests for a solution multiple times and calculate median runtime

    Returns:
    - Median runtime if tests are successful
    - None if tests fail
    """
    runtimes = []
    for _ in range(3):  # Run 3 times
        all_test_inputs = [
            {
                "input": test_case.input_text,
                "output": test_case.output_text
            } for test_case in test_cases
        ]

        success, elapsed_time = code_runner.run_tests(
            all_test_inputs,
            problem.fn_name,
            solution_text
        )

        if not success:
            return None

        runtimes.append(elapsed_time)

    # Calculate median runtime
    return statistics.median(runtimes)


def test_problems_solutions(commit_interval: int = 100):
    """
    Main function to test solutions for untested valid problems
    """
    session = create_db_session()
    code_runner = CodeRunner(debug=True)

    try:
        # Get problems to test
        problems = get_problems_to_test(session)

        for problem in tqdm(problems, desc="Testing Problems", unit="problem"):
            try:
                # Get test cases for this problem
                test_cases = session.query(InputOutput).filter(
                    InputOutput.problem_id == problem.id
                ).all() * problem.test_repeat_time

                # Get random solutions
                solutions_to_test = get_random_solutions_for_problem(session, problem.id)

                # Track valid solutions for this problem
                valid_solutions_for_problem = []

                # Test each solution
                for solution in solutions_to_test:
                    # Mark the solution as tested
                    solution.is_tested = 1

                    # Run tests
                    runtime = run_solution_tests(
                        code_runner,
                        problem,
                        solution.solution_text,
                        test_cases
                    )

                    # If solution passes tests, add to valid solutions
                    if runtime is not None:
                        valid_solution = ValidSolution(
                            problem_id=problem.id,
                            solution_id=solution.id,
                            solution_text=solution.solution_text,
                            run_time=runtime,
                            test_iterations=1
                        )
                        valid_solutions_for_problem.append(valid_solution)

                # Mark the problem as tested
                problem.is_tested = 1

                # Add valid solutions to session
                session.add_all(valid_solutions_for_problem)

                # Periodic commit
                if problem.id % commit_interval == 0:
                    session.commit()

            except Exception as e:
                print(f"Error processing problem {problem.id}: {e}")
                session.rollback()

        # Final commit
        session.commit()

    except Exception as e:
        print(f"An error occurred during testing: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    test_problems_solutions(commit_interval=1)