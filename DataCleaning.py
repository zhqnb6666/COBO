# 测试次数
test_times = 3
def run_solution(args):
    from CodeRunner import CodeRunner
    import numpy as np
    solution_id, solution, input_list, output_list, fn_name = args
    try:
        codeRunner = CodeRunner()
        successes = np.zeros(test_times, dtype=bool)
        total_times = np.zeros(test_times)
        for i in range(test_times):
            success, total_time = codeRunner.evaluate_call_based(solution, fn_name, input_list, output_list)
            successes[i] = success
            total_times[i] = total_time
        if successes.all():
            return {"solution_id": solution_id, "solution_text": solution, "total_time": total_times.mean()}
    except Exception as e:
        pass
    return None

def execute_code(solutions, input_list, output_list, fn_name):
    import multiprocessing
    timeout_seconds = 2
    results = []
    pool_size = 6  # 设置进程池大小
    with multiprocessing.Pool(processes=pool_size) as pool:
        async_results = [pool.apply_async(run_solution, args=((solution_id, solution, input_list, output_list, fn_name),)) for solution_id, solution in solutions]
        for async_result in async_results:
            try:
                result = async_result.get(timeout=timeout_seconds * test_times)
                if result:
                    results.append(result)
            except multiprocessing.TimeoutError:
                continue
    return results

def test_database_code():
    import json
    import ast
    import psycopg2
    from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    cur = connection.cursor()
    cur.execute("SELECT id, fn_name FROM taco_problems0_2 WHERE fn_name is not null")
    problem_IDs = cur.fetchall()
    for ID in problem_IDs:
        problem_id = ID[0]
        fn_name = ID[1]
        cur.execute("SELECT id, solution_text FROM solutions0_2 WHERE problem_id = %s", (problem_id,))
        solutions = cur.fetchall()
        cur.execute("SELECT input_text, output_text FROM input_outputs0_2 WHERE problem_id = %s", (problem_id,))
        tests = cur.fetchall()[0:20]
        input_list = []
        output_list = []
        for input_text, output_text in tests:
            try:
                input_list.append(ast.literal_eval(input_text))
                output_list.append(ast.literal_eval(output_text))
            except (ValueError, SyntaxError):
                continue
        if not input_list or not output_list:
            continue
        results = execute_code(solutions, input_list, output_list, fn_name)
        #如果全部失败，就不用写到json文件里了
        if not results:
            continue
        with open("results.jsonl", "a") as f:
            json.dump({"question_id": problem_id, "fn_name": fn_name, "results": results}, f)
            f.write("\n")
        print(f"The problem {problem_id} has been tested")
    cur.close()
    connection.close()
if __name__ == "__main__":
    test_database_code()


