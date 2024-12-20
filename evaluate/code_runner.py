import ast
import os
import tempfile
import subprocess
import threading
import time

import numpy as np
from enum import Enum
from typing import  Dict, Any, Tuple, Optional
import importlib.util


class CodeType(Enum):
    CALL_BASED = "call_based"  # Function-based evaluation
    STANDARD_INPUT = "standard_input"  # Input/output based evaluation


class ExecutionStatus:
    PASSED = (True, "passed")
    FAILED = (False, "failed")
    TIMEOUT = (False, "timeout")
    RUNTIME_ERROR = (False, "runtime_error")
    COMPILE_ERROR = (False, "compile_error")

    @staticmethod
    def return_code_error(code: int) -> Tuple[bool, str]:
        return (False, f"returncode:{code}")

TIMEOUT_SECONDS = 8


class RuntimeCodeExecutor:
    @staticmethod
    def create_module_from_string(module_name: str, code: str) -> Any:
        """Creates a module from a string of code"""
        spec = importlib.util.spec_from_loader(module_name, loader=None)
        if spec is None:
            raise ImportError(f"Failed to create spec for module {module_name}")

        module = importlib.util.module_from_spec(spec)
        exec(code, module.__dict__)
        return module


class CodeRunner:
    def __init__(self, debug: bool = False):
        self.debug = debug

    def run_tests(self, test_cases: list[Dict[str, Any]], fn_name: Optional[str] = "",
                  test_code: Optional[str] = None) -> Optional[Tuple[bool, float]]:
        success = True
        run_time = 0.0
        if not test_code:
            if self.debug:
                print("未提供测试代码。")
            return None
        for test_case in test_cases:
            result = self.run_test(test_case, fn_name, test_code)
            if result is None:
                return None
            success, elapsed_time = result
            if not success:
                success = False
                break
            run_time += elapsed_time
        return success, run_time

    def run_test(self, test_case: Dict[str, Any], fn_name: Optional[str] = "", test_code: Optional[str] = None) -> \
    Optional[Tuple[bool, float]]:
        if not test_code:
            if self.debug:
                print("No test code provided.")
            return None
        inputs = self._process_input(test_case.get("input"))
        expected_output = self._process_output(test_case.get("output"))
        code_type = CodeType.CALL_BASED if fn_name else CodeType.STANDARD_INPUT

        if code_type == CodeType.CALL_BASED:
            return self._evaluate_single_call_based(test_code, fn_name, inputs, expected_output)
        else:
            return self._evaluate_single_standard_input(test_code, inputs, expected_output)

    def _evaluate_single_call_based(self, test_code: str, fn_name: str,
                                    inputs: Any, expected_output: Any) -> Tuple[bool, float]:
        synthesized_code = self._prepare_call_based_code(test_code)
        method = self._compile_and_get_function(synthesized_code, fn_name)
        try:
            parsed_inputs = ast.literal_eval(inputs)
            parsed_outputs = ast.literal_eval(expected_output)
        except:
            return False, 0.0

        if not method:
            return False, 0.0

        result = None
        exception = None
        elapsed_time = 0.0
        timeout_occurred = False
        def runner():
            nonlocal result, exception, elapsed_time
            start_time = time.perf_counter()
            try:
                result = method(*parsed_inputs)
            except Exception as e:
                exception = e
            finally:
                elapsed_time = time.perf_counter() - start_time

        thread = threading.Thread(target=runner)
        thread.start()

        thread.join(timeout=TIMEOUT_SECONDS)

        if thread.is_alive():
            timeout_occurred = True
            thread.join()  # Ensure the thread finishes

        if timeout_occurred:
            if self.debug:
                print("Timeout occurred!")
            return False, 0.0
        if exception:
            if self.debug:
                print(f"Runtime error occurred: {exception}")
            return False, 0.0
        success = self._compare_outputs(result, parsed_outputs)
        return success, elapsed_time

    def _evaluate_single_standard_input(self, test_code: str, inputs: Any, expected_output: Any) -> Tuple[bool, float]:
        temp_file = self._create_temp_file(test_code)
        input_str = "\n".join(inputs) if isinstance(inputs, list) else str(inputs)
        start_time = time.time()
        try:
            result = subprocess.run(['python', temp_file],
                                    input=input_str,
                                    text=True,
                                    capture_output=True,
                                    timeout=TIMEOUT_SECONDS)
            elapsed_time = time.time() - start_time

            if result.returncode == 0:
                actual_output = result.stdout.strip()
                success = self._compare_outputs(actual_output, expected_output)
            else:
                success = False

        except subprocess.TimeoutExpired:
            if self.debug:
                print("Execution timed out.")
            success = False
            elapsed_time = 0.0
        except Exception as e:
            if self.debug:
                print(f"Execution error: {e}")
            success = False
            elapsed_time = 0.0
        finally:
            os.unlink(temp_file)

        return success, elapsed_time

    def _process_input(self, inputs: Any) -> Any:
        if isinstance(inputs, list) and inputs and isinstance(inputs[0], dict):
            return [{int(k): v for k, v in inputs[0].items()}]
        return inputs

    def _process_output(self, outputs: Any) -> Any:
        if isinstance(outputs, dict):
            return [{int(k): v for k, v in outputs.items()}]
        if isinstance(outputs, list) and outputs and isinstance(outputs[0], dict):
            return [{int(k): v for k, v in outputs[0].items()}]
        return outputs


    def _compare_outputs(self, actual: Any, expected: Any) -> bool:
        if actual == expected:
            return True

        if isinstance(expected, list):
            if actual == expected[0]:
                return True

        try:
            actual_float = [float(x) for x in actual] if isinstance(actual, list) else float(actual)
            expected_float = [float(x) for x in expected] if isinstance(expected, list) else float(expected)
            return np.allclose(actual_float, expected_float)
        except (ValueError, TypeError):
            pass

        if isinstance(actual, str) and isinstance(expected, str):
            return actual.strip() == expected.strip()

        return False

    def _prepare_call_based_code(self, code: str) -> str:
        imports = [
            "import sys", "import itertools", "import collections", "import math",
            "import numpy as np", "import random", "import heapq", "from typing import List, Tuple, Dict, Any",
            "from itertools import accumulate, product, permutations, combinations",
            "from collections import Counter, OrderedDict, deque, defaultdict",
            "from functools import lru_cache",
            "from math import sqrt, sin, cos, tan, ceil, floor, gcd"
        ]
        return "\n".join(imports) + "\n" + code

    def _create_temp_file(self, content: str) -> str:
        """Creates a temporary file with the given content"""
        normal_import_lines = "import sys\nimport time\nimport itertools\nfrom itertools import accumulate, product, permutations, combinations\nimport collections\nfrom collections import Counter, OrderedDict, deque, defaultdict, ChainMap\nfrom functools import lru_cache\nimport math\nfrom math import sqrt, sin, cos, tan, ceil, fabs, floor, gcd, exp, log, log2\nimport fractions\nfrom typing import List, Tuple\nimport numpy as np\nimport random\nimport heapq\nfrom heapq import *\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(normal_import_lines)
            f.write(content)
            return f.name

    def _compile_and_get_function(self, code: str, method_name: str) -> Optional[callable]:
        try:
            module = RuntimeCodeExecutor.create_module_from_string("solution", code)
            if "class Solution" in code:
                return getattr(module.Solution(), method_name)
            return getattr(module, method_name)
        except Exception as e:
            if self.debug:
                print(f"Compilation error: {e}")
            return None