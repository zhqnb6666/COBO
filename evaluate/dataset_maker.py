import json
from sqlalchemy.orm import sessionmaker
from database.models import TACOProblem,InputOutput,ValidSolution
from database.base import engine

Session = sessionmaker(bind=engine)
session = Session()

# 查询问题数据
problems = session.query(TACOProblem).filter(
    TACOProblem.is_tested == 1,
    TACOProblem.is_valid == 1
).all()

dataset = []

for problem in problems:
    # 查找对应的输入输出数据
    io_samples = session.query(InputOutput).filter(
        InputOutput.problem_id == problem.id
    ).all()

    io_data = [{"input": io.input_text, "output": io.output_text} for io in io_samples]

    # 查找运行时间的解决方案
    fast_solution = session.query(ValidSolution).filter(
        ValidSolution.problem_id == problem.id
    ).order_by(ValidSolution.run_time).first()

    slow_solution = session.query(ValidSolution).filter(
        ValidSolution.problem_id == problem.id
    ).order_by(ValidSolution.run_time.desc()).first()

    # 确保两个解决方案都存在
    if not fast_solution or not slow_solution:
        continue

    # 构建问题数据
    problem_data = {
        "id": problem.id,
        "question": problem.question,
        "starter_code": problem.starter_code,
        "difficulty": problem.difficulty,
        "raw_tags": problem.raw_tags,
        "name": problem.name,
        "source": problem.source,
        "tags": problem.tags,
        "skill_types": problem.skill_types,
        "url": problem.url,
        "expected_auxiliary_space": problem.expected_auxiliary_space,
        "time_limit": problem.time_limit,
        "date": problem.date,
        "picture_num": problem.picture_num,
        "memory_limit": problem.memory_limit,
        "expected_time_complexity": problem.expected_time_complexity,
        "fn_name": problem.fn_name,
        "is_tested": problem.is_tested,
        "is_valid": problem.is_valid,
        "test_repeat_time": problem.test_repeat_time,
        "input_outputs": io_data,
        "fast_solution": {
            "solution_id": fast_solution.id,
            "solution_text": fast_solution.solution_text,
            "run_time": fast_solution.run_time
        },
        "slow_solution": {
            "solution_id": slow_solution.id,
            "solution_text": slow_solution.solution_text,
            "run_time": slow_solution.run_time
        }
    }

    dataset.append(problem_data)
print(f"共找到 {len(dataset)} 个问题")
# 保存到 JSON 文件
output_file = "dataset.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=4)

print(f"数据集已成功保存到 {output_file}")
