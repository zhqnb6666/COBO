import json

from datasets import load_dataset

def filter_successful_tasks(input_file: str, output_file: str, start_idx: int = 0, end_idx: int = 1000):
    taco = load_dataset('arrow', split='train', data_files='data-00000-of-00001.arrow')
    taco_subset = taco.select(range(start_idx, end_idx))
    with open(input_file, 'r') as infile:
        data = json.load(infile)

    successful_tasks = []
    try:
        for task in data:
            if task.get('success'):
                task.pop('success', None)
                task_id = task.get('task_id')
                solutions_str = taco_subset[task_id - 1]['solutions']
                if not solutions_str:
                    print(f"No solutions found for task {task_id}")
                    continue
                try:
                    solutions = json.loads(solutions_str)
                except json.JSONDecodeError as e:
                    print(f"Error decoding solutions for task {task_id}: {str(e)}")
                    print(solutions_str)
                    continue
                try:
                    fastest_solution_id = task.get('fastest_solution_id')
                    slowest_solution_id = task.get('slowest_solution_id')
                    task['fastest_solution'] = solutions[fastest_solution_id]
                    task['slowest_solution'] = solutions[slowest_solution_id] if slowest_solution_id != -1 else \
                        'The running time of all solutions to this problem is 0s, and the time dif between them is hard to estimate.'
                except IndexError as e:
                    print(f"The array of solutions for task {task_id} is too short, the wrong length is {len(solutions)}: {str(e)}")
                    continue
                successful_tasks.append(task)
    except Exception as e:
        print(f"Error processing sample at index {task_id}: {str(e)}")

    with open(output_file, 'w') as outfile:
        json.dump(successful_tasks, outfile, indent=4)

# Usage example
input_file = 'taco_test_results.json'
output_file = 'successful_tasks.json'

filter_successful_tasks(input_file, output_file)