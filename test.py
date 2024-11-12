import json
import concurrent.futures
from datasets import load_dataset
from CodeRunner import CodeRunner
from typing import Dict, Any, List

# 定义运行超时时间（秒）
TIMEOUT = 10


def run_solution(sample):
    """
    运行给定样例的代码解决方案，并记录运行时间。
    """
    runner = CodeRunner(False)

    try:
        solutions = json.loads(sample['solutions'])
        if len(solutions) > 10:
            solutions = solutions[:10]
    except Exception:
            return 0, 0, False, -1, -1

    max_elapsed_time = 0
    min_elapsed_time = float('inf')
    success = False
    slowest_solution_index = -1
    fastest_solution_index = -1

    for index, solution in enumerate(solutions):
        try:
            current_success, current_time = runner.run_test(sample, solution)
            print(f'current solution {index} current time {current_time}')

            if current_success:
                # 更新最长运行时间和对应的索引
                if current_time > max_elapsed_time:
                    max_elapsed_time = current_time
                    slowest_solution_index = index

                # 更新最短运行时间和对应的索引
                if current_time < min_elapsed_time:
                    min_elapsed_time = current_time
                    fastest_solution_index = index

                success = True
        except Exception as e:
            continue

    # 如果没有成功的解决方案，返回最短时间为 0
    if not success:
        min_elapsed_time = 0

    return max_elapsed_time, min_elapsed_time, success, slowest_solution_index, fastest_solution_index


def evaluate_taco_subset(start_idx=0, end_idx=10):
    """
    评估指定范围的数据集样例，并输出每个样例的运行时间和结果。
    """
    taco = load_dataset('arrow', split='train', data_files='data-00000-of-00001.arrow')

    taco_subset = taco
    # .select(range(start_idx, end_idx))

    results = []

    def process_sample(sample_id: int, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个样例，执行 run_solution 并返回结果。
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

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(process_sample, start_idx + i, sample): start_idx + i
            for i, sample in enumerate(taco_subset)
        }

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)

    with open('taco_train_results.json', 'w') as f:
        json.dump(results, f, indent=4)
    print("测试完成，结果已保存至 taco_train_results.json")


if __name__ == "__main__":
    evaluate_taco_subset(start_idx=1, end_idx=100)
