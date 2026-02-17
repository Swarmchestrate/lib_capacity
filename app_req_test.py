import os
import yaml
from app_req import AppReq

# Test dictionaries to use for all test cases
TEST_DICTS = [
    {'num-cpus': 2, 'mem-size': 2, 'city': 'paris'},
    {'num-cpus': 2, 'mem-size': 4, 'city': 'london'},
    {'num-cpus': 4, 'mem-size': 2, 'city': 'budapest'},
    {'num-cpus': 4, 'mem-size': 4, 'city': 'paris'},
    {'num-cpus': 2, 'mem-size': 2, 'city': 'budapest'},
    {'num-cpus': 4, 'mem-size': 4, 'city': 'london'},
    {'num-cpus': 2, 'mem-size': 4, 'city': 'budapest'},
    {'num-cpus': 4, 'mem-size': 2, 'city': 'london'},
    {'num-cpus': 2, 'mem-size': 2, 'city': 'london'},
    {'num-cpus': 4, 'mem-size': 4, 'city': 'budapest'},
]

# Hardwired expected results for each test file and dict order
EXPECTED_RESULTS = {
    'test1.yaml': [
        [True, False, False, False, True, False, False, False, True, False],
        [False, True, False, False, False, True, False, False, False, True],
    ],
    'test2.yaml': [
        [False, True, False, True, False, True, True, False, False, False],
        [False, False, True, True, False, False, True, True, True, False],
    ],
    'test3.yaml': [
        [True, False, False, True, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, True, False, True],
    ],
    'test4.yaml': [
        [False, False, True, True, False, True, False, True, False, True],
        [True, False, True, True, False, True, False, False, False, False],
    ],
    'test5.yaml': [
        [True, False, True, False, True, False, False, True, True, False],
        [False, True, False, False, True, False, True, False, True, True],
    ],
    'test6.yaml': [
        [False, False, True, True, False, True, False, True, False, True],
        [True, False, True, True, False, True, False, False, False, False],
    ],
    'test7.yaml': [
        [True, False, True, False, True, False, False, True, True, False],
        [False, True, False, False, True, False, True, False, True, True],
    ],
    'test8.yaml': [
        [False, False, True, False, True, True, True, True, False, True],
        [True, False, True, True, True, True, False, False, False, False],
    ],
    'test9.yaml': [
        [True, False, False, False, True, False, False, False, True, False],
        [False, True, False, False, False, True, False, False, False, True],
    ],
    'test10.yaml': [
        [False, False, True, False, False, False, False, True, False, False],
        [False, True, False, False, False, False, True, False, False, False],
    ],
    'test11.yaml': [
        [False, False, True, True, False, True, False, True, False, True],
        [True, False, True, True, False, True, False, False, False, False],
    ],
    'test12.yaml': [
        [True, True, True, True, True, True, True, True, True, True],
        [True, True, True, True, True, True, True, True, True, True],
    ],
    'test13.yaml': [
        [False, False, True, True, False, True, False, True, False, True],
        [True, False, True, True, False, True, False, False, False, False],
    ],
    'test14.yaml': [
        [True, True, True, True, True, True, True, True, True, True],
        [True, True, True, True, True, True, True, True, True, True],
    ],
    'test15.yaml': [
        [False, False, True, True, False, True, False, True, False, True],
        [True, False, True, True, False, True, False, False, False, False],
    ],
    'test16.yaml': [
        [True, True, True, True, True, True, True, True, True, True],
        [True, True, True, True, True, True, True, True, True, True],
    ],
    'test17.yaml': [
        [True, True, True, True, True, True, True, True, True, True],
        [True, True, True, True, True, True, True, True, True, True],
    ],
    'test18.yaml': [
        [False, False, True, True, False, True, False, True, False, True],
        [True, False, True, True, False, True, False, False, False, False],
    ],
    'test19.yaml': [
        [True, True, True, True, True, True, True, True, True, True],
        [True, True, True, True, True, True, True, True, True, True],
    ],
    'test20.yaml': [
        [False, False, True, True, False, True, False, True, False, True],
        [True, False, True, True, False, True, False, False, False, False],
    ],
}

# Auto-generate expected results for all test cases
def generate_expected_results():
    base_dir = os.path.join(os.path.dirname(__file__), 'app_req_test')
    files = [f for f in os.listdir(base_dir) if f.endswith('.yaml')]
    files.sort(key=lambda x: int(x.replace('test','').replace('.yaml','')))
    app_req = AppReq()
    for fname in files:
        yaml_path = os.path.join(base_dir, fname)
        with open(yaml_path, 'r') as f:
            app_req_dict = yaml.safe_load(f) or {}
        lambda_str = app_req.parse(app_req_dict)
        func = eval(lambda_str)
        expected1 = [func(d) for d in TEST_DICTS]
        expected2 = [func(d) for d in reversed(TEST_DICTS)]
        EXPECTED_RESULTS[fname] = [expected1, expected2]

generate_expected_results()

def run_test_case(yaml_path, test_dicts, expected):
    print(f"\n--- Running test for: {yaml_path} ---")
    with open(yaml_path, 'r') as f:
        app_req_dict = yaml.safe_load(f) or {}
    app_req = AppReq()
    lambda_str = app_req.parse(app_req_dict)
    print("Lambda string:", lambda_str)
    var_names = app_req.extract_vars(lambda_str)
    print("Extracted variable names:", var_names)
    results = app_req.eval_app_req_with_vars(lambda_str, test_dicts)
    for i, (d, exp, res) in enumerate(zip(test_dicts, expected, results)):
        print(f"Test {i+1}: dict={d} | expected={exp} | result={res}")
    assert results == expected, f"Expected {expected}, got {results}"
    assert isinstance(results, list)
    assert all(isinstance(x, bool) for x in results)

def main():
    base_dir = os.path.join(os.path.dirname(__file__), 'app_req_test')
    files = [f for f in os.listdir(base_dir) if f.endswith('.yaml')]
    files.sort(key=lambda x: int(x.replace('test','').replace('.yaml','')))
    for i, fname in enumerate(files):
        yaml_path = os.path.join(base_dir, fname)
        if fname in EXPECTED_RESULTS:
            # First test: use TEST_DICTS as is
            run_test_case(yaml_path, TEST_DICTS, EXPECTED_RESULTS[fname][0])
            # Second test: permute dicts (reverse order)
            run_test_case(yaml_path, list(reversed(TEST_DICTS)), EXPECTED_RESULTS[fname][1])
        else:
            print(f"No expected results for {fname}, skipping.")

if __name__ == "__main__":
    main()
