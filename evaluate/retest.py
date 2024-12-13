import os
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import asc, desc
from tqdm import tqdm
from database.models import TACOProblem, ValidSolution, InputOutput
from database.base import engine
from evaluate.code_runner import CodeRunner
from typing import List, Dict, Any, Type


def create_db_session():
    """创建数据库会话"""
    Session = sessionmaker(bind=engine)
    return Session()


def get_valid_solutions_to_test(session: Session) -> list[Type[ValidSolution]]:
    """选择test_iterations为0的valid_solution，按problem_id分组，按id递减排序"""
    return session.query(ValidSolution).filter(ValidSolution.test_iterations == 0).order_by(
        desc(ValidSolution.problem_id), asc(ValidSolution.id)
    ).all()


def average_runtime(code_runner: CodeRunner, all_test_inputs: List[Dict[str, Any]], fn_name: str, solution_text: str,
                    repeats: int = 3) -> float:
    times = []
    for _ in range(repeats):
        success, elapsed_time = code_runner.run_tests(all_test_inputs, fn_name, solution_text)
        if not success:
            return -1  # Indicate failure
        times.append(elapsed_time)
    return sum(times) / repeats


def serial_test(commit_interval: int = 10):
    session = create_db_session()
    try:
        # 获取待测试的解决方案
        valid_solutions = get_valid_solutions_to_test(session)

        # 使用tqdm显示进度
        for idx, valid_solution in enumerate(tqdm(valid_solutions, desc="重新测试运行时间", unit="解决方案"), 1):
            try:
                # 获取对应的问题
                problem = session.query(TACOProblem).get(valid_solution.problem_id)

                # 准备测试用例
                test_cases = session.query(InputOutput).filter(
                    InputOutput.problem_id == problem.id
                ).all() * problem.test_repeat_time

                # 创建代码运行器
                code_runner = CodeRunner(debug=True)
                all_test_inputs = [
                    {
                        "input": test_case.input_text,
                        "output": test_case.output_text
                    } for test_case in test_cases
                ]

                # 测量运行时间
                avg_time = average_runtime(code_runner, all_test_inputs, problem.fn_name, valid_solution.solution_text)

                # 更新解决方案信息
                if avg_time != -1:
                    valid_solution.run_time = avg_time
                    valid_solution.test_iterations = 1  # 标记已测试

                # 定期提交
                if idx % commit_interval == 0:
                    session.commit()

            except Exception as e:
                print(f"Error processing valid solution {valid_solution.id}: {e}")
                session.rollback()

        # 最后提交剩余的更改
        session.commit()

    except Exception as e:
        print(f"An error occurred during testing: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    serial_test(commit_interval=100)
