import os
import argparse
from asltesting.test_configuration import TestConfiguration
from asltesting.plotter import Plotter
from asltesting.test_runner import TestRunner

TESTS_DIR = './tests/'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_name', type=str)
    parser.add_argument('--local', action='store_true')
    args = parser.parse_args()

    test_configs = []

    if args.test_name is not None:
        test_configs = [TestConfiguration(TESTS_DIR, args.test_name)]
    else:
        test_configs = list(map(lambda test_name: TestConfiguration(TESTS_DIR, test_name), os.listdir(TESTS_DIR)))

    plotter = Plotter()
    runner = TestRunner(args.local)

    for test_config in test_configs:
        runner.run_test(test_config)
        plotter.plot_test(test_config)