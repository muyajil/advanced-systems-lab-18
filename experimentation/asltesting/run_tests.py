import os
import argparse
from asltesting.test_configuration import TestConfiguration
from asltesting.plotter import Plotter
from asltesting.test_runner import TestRunner
from asltesting import paths
import time


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_names', nargs='+', type=str, default=[], dest='test_names')
    parser.add_argument('--local', action='store_true')
    parser.add_argument('--run_id', type=str, default=None)
    parser.add_argument('--exclude ', nargs='+', type=str, default=[], dest='exclude')
    parser.add_argument('--plot', action='store_true')
    parser.add_argument('--repetitions', type=int, default=3)
    args = parser.parse_args()

    test_configs = []
    run_id = args.run_id if args.run_id is not None else str(int(time.time()))

    if len(args.test_names) > 0:
        test_configs = map(lambda test_name: TestConfiguration(test_name, run_id), args.test_names)
    else:
        test_configs = map(lambda test_name: TestConfiguration(test_name, run_id), filter(lambda x: x not in args.exclude, sorted(os.listdir(paths.Absolute.TESTS))))

    if args.plot:
        plotter = Plotter(args.repetitions)
        for test_config in test_configs:
            plotter.plot_test(test_config.run_configuration, test_config.log_dir, test_config.plot_dir)
    else:
        runner = TestRunner(args.repetitions, args.local)
        for test_config in test_configs:
                runner.run_test(test_config.run_configuration, test_config.log_dir)


