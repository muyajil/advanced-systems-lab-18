import os
import argparse
from asltesting.test_configuration import TestConfiguration
from asltesting.plotter import Plotter
from asltesting.test_runner import TestRunner

TESTS_DIR = './tests/'

def get_tests():
    return os.listdir(TESTS_DIR)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--local', action='store_true')
    args = parser.parse_args()

    test_configs = []

    for test_name in get_tests():
        test_configs.append(TestConfiguration(TESTS_DIR, test_name))

    plotter = Plotter()
    runner = TestRunner(args.local)

    for test_config in test_configs:
        runner.run_test(test_config)
        plotter.plot_test(test_config)