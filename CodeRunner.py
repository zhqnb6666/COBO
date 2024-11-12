import signal
import sys
import os
import json
import tempfile
import subprocess
import time

import numpy as np
from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional, Union
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


class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutException("Code execution timed out")


if os.name == 'nt':
    # Windows specific signal setup
    signal.signal(signal.SIGTERM, timeout_handler)
else:
    signal.signal(signal.SIGALRM, timeout_handler)

TIMEOUT_SECONDS = 4


class RuntimeCodeExecutor:
    """Handles dynamic code execution in a controlled environment"""

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

    def run_test(self, sample: Dict[str, Any], test_code: Optional[str] = None) -> Optional[Tuple[bool, float]]:
        """Main entry point for running code tests"""
        if self.debug:
            print(f"Starting evaluation at {datetime.now().time()}")

        try:
            in_outs = json.loads(sample["input_output"])
        except (ValueError, KeyError):
            return None

        code_type = self._determine_code_type(in_outs)
        method_name = in_outs.get("fn_name")
        inputs_list, outputs_list = self._process_test_cases(in_outs)

        if test_code is None:
            return None

        if code_type == CodeType.CALL_BASED:
            return self._evaluate_call_based(test_code, method_name, inputs_list, outputs_list)
        else:
            return self._evaluate_standard_input(test_code, inputs_list, outputs_list)

    def _determine_code_type(self, in_outs: Dict[str, Any]) -> CodeType:
        """Determines whether the test is call-based or standard input based"""
        return CodeType.CALL_BASED if "fn_name" in in_outs else CodeType.STANDARD_INPUT

    def _process_test_cases(self, in_outs: Dict[str, Any]) -> Tuple[List[Any], List[Any]]:
        """Processes input and output test cases"""
        inputs_list = []
        outputs_list = []

        if len(in_outs["inputs"])<3:
            for i, inputs in enumerate(in_outs["inputs"]):
                outputs = in_outs["outputs"][i]
                processed_inputs = self._process_input(inputs)
                processed_outputs = self._process_output(outputs)
                inputs_list.append(processed_inputs)
                outputs_list.append(processed_outputs)
        else:
            for i in range(3):
                inputs = in_outs["inputs"][i]
                outputs = in_outs["outputs"][i]
                processed_inputs = self._process_input(inputs)
                processed_outputs = self._process_output(outputs)
                inputs_list.append(processed_inputs)
                outputs_list.append(processed_outputs)

        return inputs_list, outputs_list

    def _process_input(self, inputs: Any) -> Any:
        """Processes input data, converting dictionary keys to integers if needed"""
        if isinstance(inputs, list) and inputs and isinstance(inputs[0], dict):
            return [{int(k): v for k, v in inputs[0].items()}]
        return inputs

    def _process_output(self, outputs: Any) -> Any:
        """Processes output data, converting dictionary keys to integers if needed"""
        if isinstance(outputs, dict):
            return [{int(k): v for k, v in outputs.items()}]
        if isinstance(outputs, list) and outputs and isinstance(outputs[0], dict):
            return [{int(k): v for k, v in outputs[0].items()}]
        return outputs

    def _evaluate_call_based(self, test_code: str, method_name: str,
                             inputs_list: List[Any], outputs_list: List[Any]) -> Tuple[bool, float]:
        """Evaluates function-based code and returns a tuple of (is_all_passed, total_time)."""
        synthesized_code = self._prepare_call_based_code(test_code)
        method = self._compile_and_get_function(synthesized_code, method_name)

        if not method:
            return False, 0.0

        total_time = 0.0
        for inputs, expected_outputs in zip(inputs_list, outputs_list):
            start_time = time.time()
            try:
                actual_output = method(*inputs)
                elapsed_time = time.time() - start_time
                total_time += elapsed_time
                if not self._compare_outputs(actual_output, expected_outputs):
                    return False, total_time
            except Exception as e:
                if self.debug:
                    print(f"Runtime error: {e}")
                return False, total_time

        return True, total_time

    def _evaluate_standard_input(self, test_code: str,
                                 inputs_list: List[Any], outputs_list: List[Any]) -> Tuple[bool, float]:
        """Evaluates standard input/output based code and returns a tuple of (is_all_passed, total_time)."""
        temp_file = self._create_temp_file(test_code)
        total_time = 0.0

        for inputs, expected_outputs in zip(inputs_list, outputs_list):
            input_str = "\n".join(inputs) if isinstance(inputs, list) else str(inputs)
            start_time = time.time()
            try:
                result = subprocess.run(['python', temp_file],
                                        input=input_str,
                                        text=True,
                                        capture_output=True,
                                        timeout=TIMEOUT_SECONDS)
                elapsed_time = time.time() - start_time
                total_time += elapsed_time

                if result.returncode == 0:
                    actual_output = result.stdout.strip()
                    if not self._compare_outputs(actual_output, expected_outputs):
                        os.unlink(temp_file)
                        return False, total_time
                else:
                    os.unlink(temp_file)
                    return False, total_time

            except subprocess.TimeoutExpired:
                os.unlink(temp_file)
                return False, total_time
            except Exception as e:
                if self.debug:
                    print(f"Execution error: {e}")
                os.unlink(temp_file)
                return False, total_time

        os.unlink(temp_file)
        return True, total_time

    def _compare_outputs(self, actual: Any, expected: Any) -> bool:
        """Compares actual output with expected output"""
        # Handle basic equality
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

        # Handle string comparisons
        if isinstance(actual, str) and isinstance(expected, str):
            return actual.strip() == expected.strip()

        return False

    def _prepare_call_based_code(self, code: str) -> str:
        """Prepares code for call-based evaluation"""
        imports = [
            "import sys", "import itertools", "import collections", "import math",
            "import numpy as np", "import random", "import heapq",
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
        """Compiles code and returns the specified function"""
        try:
            module = RuntimeCodeExecutor.create_module_from_string("solution", code)
            if "class Solution" in code:
                return getattr(module.Solution(), method_name)
            return getattr(module, method_name)
        except Exception as e:
            if self.debug:
                print(f"Compilation error: {e}")
            return None


def disable_dangerous_functions():
    """Disables potentially dangerous built-in functions"""
    import builtins

    DISABLED_BUILTINS = ['exit', 'quit', 'help']
    for func in DISABLED_BUILTINS:
        setattr(builtins, func, None)

    DISABLED_OS_FUNCTIONS = [
        'system', 'remove', 'removedirs', 'rmdir', 'unlink',
        'rename', 'renames', 'truncate', 'replace', 'chmod', 'chown'
    ]
    for func in DISABLED_OS_FUNCTIONS:
        setattr(os, func, None)

    # Disable potentially dangerous modules
    sys.modules['subprocess'] = None
    sys.modules['shutil'] = None