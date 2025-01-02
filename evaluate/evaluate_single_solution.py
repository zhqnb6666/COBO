import os
from sqlalchemy.orm import sessionmaker
from database.models import Solution, InputOutput, TACOProblem
from database.base import engine
from evaluate.code_runner import CodeRunner


def create_db_session():
    """创建数据库会话"""
    Session = sessionmaker(bind=engine)
    return Session()


def run_solution_tests(solution_id: int):
    session = create_db_session()
    try:
        solution = session.query(Solution).filter(Solution.id == solution_id).first()
        if not solution:
            print(f"没有找到ID为 {solution_id} 的解决方案。")
            return

        # 获取相应的测试样例
        problem_id = solution.problem_id
        test_cases = session.query(InputOutput).filter(InputOutput.problem_id == problem_id).all()
        test_repeat_time = session.query(TACOProblem).filter(TACOProblem.id == problem_id).first().test_repeat_time
        fn_name = session.query(TACOProblem).filter(TACOProblem.id == problem_id).first().fn_name

        # 准备输入输出数据
        all_test_inputs = [
            {
                "input": test_case.input_text,
                "output": test_case.output_text
            } for test_case in test_cases
        ]*test_repeat_time

        # 创建代码运行器
        code_runner = CodeRunner(debug=True)

        # 执行测试
        success, elapsed_time = code_runner.run_tests(all_test_inputs,fn_name ,
                                                      solution.solution_text)

        # 打印结果
        if success:
            print(f"解决方案 {solution_id} 测试成功，运行时间: {elapsed_time:.4f} 秒")
        else:
            print(f"解决方案 {solution_id} 测试失败。")

    except Exception as e:
        print(f"处理解决方案 {solution_id} 时出错: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    run_solution_tests(493886)
