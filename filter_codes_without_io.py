import json
import re

from datasets import load_dataset

not_io_files = {}

def contains_io_operations(content):
    # Check for standard input/output
    if re.search(r'\b(input\s*\(|print\s*\()', content):
        return True
    # Check for file IO operations
    if re.search(r'\b(open\s*\(|read\s*\(|write\s*\(|close\s*\()', content):
        return True
    return False

def filter_solutions():
    taco = load_dataset('arrow', split='train', data_files='data-00000-of-00001.arrow')
    for idx, sample in enumerate(taco):
        solutions_str = sample.get('solutions')
        if not solutions_str:
            continue
        try:
            solutions = json.loads(solutions_str)
        except json.JSONDecodeError:
            continue
        for solution in solutions:
            if not solution:
                continue
            if contains_io_operations(solution):
                break
            if idx not in not_io_files:
                not_io_files[idx] = []
            not_io_files[idx].append(solution)

if __name__ == '__main__':
    filter_solutions()
    not_io_solution_count = sum(len(solutions) for solutions in not_io_files.values())
    print(f'Found {not_io_solution_count} solutions without IO operations')
    with open('not_io_files.json', 'w') as f:
        json.dump(not_io_files, f)