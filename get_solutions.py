import json

from datasets import load_dataset


def save_first_solutions(start_idx=0, end_idx=10):
    """
    提取指定范围的数据集样例的第一个 solution，并保存到 JSON 文件中。
    """
    taco = load_dataset('arrow', split='train', data_files='data-00000-of-00001.arrow')
    taco_subset = taco.select(range(start_idx, end_idx))

    first_solutions = []

    for idx, sample in enumerate(taco_subset):
        try:
            solutions = json.loads(sample['solutions'])
            first_solution = solutions[0] if solutions else None
            if first_solution:
                first_solutions.append({
                    "index": start_idx + idx,
                    "solution": first_solution
                })
        except Exception as e:
            print(f"Error processing sample at index {start_idx + idx}: {str(e)}")

    with open('first_solutions.json', 'w', encoding='utf-8') as f:
        json.dump(first_solutions, f, indent=4, ensure_ascii=False)
    print(f"提取完成，共保存了 {len(first_solutions)} 条记录至 first_solutions.json")

if __name__ == "__main__":
    save_first_solutions(start_idx=1, end_idx=3)
