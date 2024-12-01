import json
import concurrent.futures
from datasets import load_dataset
from CodeRunner import CodeRunner
from typing import Dict, Any, List

# Define the timeout for running solutions (in seconds)
TIMEOUT = 10

def run_solution(sample):
    """
    Run the given sample's code solution and record the execution time.
    """
    runner = CodeRunner(False)

    try:
        solutions = json.loads(sample['solutions'])
        if len(solutions) > 10:
            solutions = solutions[:10]
    except Exception:
        return 0, 0, False, -1, -1

    max_elapsed_time = float('-inf')
    min_elapsed_time = float('inf')
    success = False
    slowest_solution_index = -1
    fastest_solution_index = -1

    for index, solution in enumerate(solutions):
        try:
            current_success = []
            current_time = []
            for _ in range(3):
                a, b = runner.run_test(sample, solution)
                current_success.append(a)
                current_time.append(b)
            current_time = sum(current_time) / len(current_time)
            current_success = all(current_success)
            print(f'current solution {index} current time {current_time}')

            if current_success:
                # Update the longest running time and corresponding index
                if current_time > max_elapsed_time:
                    max_elapsed_time = current_time
                    slowest_solution_index = index

                # Update the shortest running time and corresponding index
                if current_time < min_elapsed_time:
                    min_elapsed_time = current_time
                    fastest_solution_index = index

                success = True
        except Exception as e:
            continue

    # If no successful solution, return the shortest time as 0
    if not success:
        min_elapsed_time = 0

    return max_elapsed_time, min_elapsed_time, success, slowest_solution_index, fastest_solution_index

def process_sample(sample_id: int, sample: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single sample, execute run_solution and return the result.
    """
    slowest_time, fastest_time, success, slowest_solution_id, fastest_solution_id = run_solution(sample)
    result = {
        "task_id": sample_id,
        "success": success,
        "slowest_solution_id": slowest_solution_id,
        "fastest_solution_id": fastest_solution_id,
        "slowest_time": slowest_time,
        "fastest_time": fastest_time
    }
    print(
        f"Task {sample_id} - Success: {success} - Slowest Time: {slowest_time:.4f}s - Fastest Time: {fastest_time:.4f}s"
    )

    if not success:
        try:
            question = sample['question']
            solution = json.loads(sample['solutions'])[0]
            source = sample['source']

            fail_data = {
                "question": question,
                "solution": solution if solution else "",
                "source": source
            }

            fail_file_path = f'Fail/sample{sample_id}.json'
            with open(fail_file_path, "w", encoding="utf-8") as f:
                json.dump(fail_data, f, indent=4, ensure_ascii=False)
            print(f"Sample {sample_id} failed, written to {fail_file_path}")
        except Exception as e:
            print(f"Error while writing fail data for sample {sample_id}: {str(e)}")

    return result

def evaluate_taco_subset(start_idx=0, end_idx=10):
    """
    Evaluate the dataset samples in the specified range and output the execution time and result for each sample.
    """
    taco = load_dataset('arrow', split='train', data_files='data-00000-of-00001.arrow')

    taco_subset = taco
    # .select(range(start_idx, end_idx))

    results = []

    # Adjust the value of max_workers to be less than the number of CPU cores
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(process_sample, start_idx + i, sample): start_idx + i
            for i, sample in enumerate(taco_subset)
        }

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)

    with open('taco_train_results.json', 'w') as f:
        json.dump(results, f, indent=4)
    print("Testing completed, results saved to taco_train_results.json")

if __name__ == "__main__":
    evaluate_taco_subset(start_idx=1, end_idx=100)