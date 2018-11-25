import os
import argparse
from asltesting.test_configuration import TestConfiguration
from asltesting.plotter import Plotter
from asltesting.test_runner import TestRunner
from asltesting import paths
import time


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_name', type=str, default=None)
    parser.add_argument('--local', action='store_true')
    parser.add_argument('--run_id', type=str, default=None)
    args = parser.parse_args()

    test_configs = []
    run_id = args.run_id if args.run_id is not None else int(time.time())

    if args.test_name is not None:
        test_configs = [TestConfiguration(args.test_name, run_id)]
    else:
        test_configs = list(map(lambda test_name: TestConfiguration(test_name, run_id), os.listdir(paths.Absolute.TESTS)))

    runner = TestRunner(3, args.local)

    for test_config in test_configs:
        if not os.path.exists(test_config.log_dir):
            os.makedirs(test_config.log_dir)
        runner.run_test(test_config.config, test_config.log_dir)
