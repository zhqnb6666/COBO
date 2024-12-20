import json
from sqlalchemy.orm import sessionmaker
from database.models import TACOProblem,InputOutput,ValidSolution
from database.base import engine

Session = sessionmaker(bind=engine)
session = Session()

def expand_time_difference(json_data):
    problem_id = json_data['problem_id']
    fast_solution_id = json_data['fast_solution_id']
    slow_solution_id = json_data['slow_solution_id']

    # Query TACOProblem excluding is_tested and is_valid
    problem_data = session.query(TACOProblem).filter_by(id=problem_id).one()
    problem_dict = {
        col: getattr(problem_data, col)
        for col in TACOProblem.__table__.columns.keys()
        if col not in ('is_tested', 'is_valid')
    }

    # Query InputOutput
    io_data = session.query(InputOutput).filter_by(problem_id=problem_id).all()
    io_list = [
        {'input': io.input_text, 'output': io.output_text}
        for io in io_data
    ]

    # Query ValidSolution for fast and slow solutions
    fast_solution = session.query(ValidSolution).filter_by(id=fast_solution_id).one()
    slow_solution = session.query(ValidSolution).filter_by(id=slow_solution_id).one()

    # Build expanded JSON
    expanded_json = {
        "problem_details": problem_dict,
        "input_outputs": io_list,
        "fast_solution_text": fast_solution.solution_text,
        "slow_solution_text": slow_solution.solution_text
    }

    return expanded_json

# File reading and writing
input_file = 'tmp_file/significant_time_differences.json'
output_file = 'optimizable_dataset.json'

#utf-8
with open(input_file, 'r', encoding='utf-8') as f:
    json_input_list = json.load(f)

expanded_json_list = [expand_time_difference(json_input) for json_input in json_input_list]

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(expanded_json_list, f, indent=2, ensure_ascii=False)

# Close session
session.close()
