import json
from concurrent.futures import as_completed, ProcessPoolExecutor
from typing import *

from datasets import load_dataset

from CodeRunner import CodeRunner


def run_solution(solution: str, sample: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    运行单个代码解决方案，并记录运行时间。
    """
    runner = CodeRunner(False)
    try:
        success = []
        time = []
        for _ in range(3):
            current_success, current_time = runner.run_test(sample, solution)
            success.append(current_success)
            time.append(current_time)
        print(f'current solution {index} current time {sum(time) / len(time)}')

        return {
            'index': index,
            'solution': solution,
            'elapsed_time': sum(time) / len(time) if all(success) else -1,
            'success': all(success)
        }
    except Exception:
        return {
            'index': index,
            'solution': solution,
            'elapsed_time': -1,
            'success': False
        }

def run_solutions_concurrently(solutions: List[str], sample: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    使用多进程并发运行所有代码解决方案。
    """
    results = []
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_solution, solution, sample, index) for index, solution in enumerate(solutions)]
        for future in as_completed(futures):
            results.append(future.result())
    return results

def main() -> None:
    with open('not_io_files.json') as f:
        not_io_files = json.load(f)
    taco = load_dataset('arrow', split='train', data_files='data-00000-of-00001.arrow')
    final_results = []
    for index, solutions in not_io_files.items():
        sample = taco[int(index)]
        results = run_solutions_concurrently(solutions, sample)
        testcase = json.loads(sample["input_output"])
        final_results.append({
            'question_id': int(index),
            'testcase': testcase,
            'results': results
        })

    with open('test_questions_withoutIO.json', 'w') as f:
        json.dump(final_results, f, indent = 4, separators=(',', ':'))
    print(f"Finished running {len(final_results)} questions.")
if __name__ == '__main__':
    main()