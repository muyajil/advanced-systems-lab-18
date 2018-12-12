import os
import argparse
from asltesting.test_configuration import TestConfiguration
from asltesting.plotter import MiddlewarePlotter, MemtierPlotter
from asltesting.test_runner import TestRunner
from asltesting import paths
from asltesting.install import Installer
import time


def generate_plots(test_configs, plot_dir=None):
    mw_plotter = MiddlewarePlotter()
    mt_plotter = MemtierPlotter()
    for test_config in test_configs:
        if plot_dir is not None:
            mt_plotter.plot_test(test_config.run_configuration, test_config.log_dir, os.path.join(plot_dir, test_config.name))
        else:
            mt_plotter.plot_test(test_config.run_configuration, test_config.log_dir, test_config.plot_dir)
        if test_config.run_configuration['num_threads_per_mw_range'][0] > 0:
            if plot_dir is not None:
                mw_plotter.plot_test(test_config.run_configuration, test_config.log_dir, plot_dir)
            else:
                mw_plotter.plot_test(test_config.run_configuration, test_config.log_dir, test_config.plot_dir)


def move_and_sample_logs(test_configs, log_dir):
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_names', nargs='+', type=str, default=[], dest='test_names')
    parser.add_argument('--local', action='store_true')
    parser.add_argument('--run_id', type=str, default=None)
    parser.add_argument('--exclude ', nargs='+', type=str, default=[], dest='exclude')
    parser.add_argument('--plot', action='store_true')
    parser.add_argument('--repetitions', type=int, default=3)
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--prepare_submission', action='store_true')
    parser.add_argument('--two_k_analysis', action='store_true')
    args = parser.parse_args()

    test_configs = []
    run_id = args.run_id if args.run_id is not None else str(int(time.time()))

    if len(args.test_names) > 0:
        test_configs = list(map(lambda test_name: TestConfiguration(test_name, run_id), args.test_names))
    else:
        test_configs = list(map(lambda test_name: TestConfiguration(test_name, run_id),
                                filter(lambda x: x not in args.exclude and 'mini' not in x,
                                       sorted(os.listdir(paths.Absolute.TESTS)))))

    if args.prepare_submission:
        if args.run_id is None:
            raise RuntimeError("Prepare submission must refer to a run_id")

        generate_plots(test_configs, paths.Absolute.SUBMISSION_PLOTS)
        #TODO: move log files to submission dir and sample
        pass

    elif args.two_k_analysis:
        test_configs = list(map(lambda test_name: TestConfiguration(test_name, run_id),
                                filter(lambda x: '2k' in x,
                                       sorted(os.listdir(paths.Absolute.TESTS)))))
        # TODO: Load data from 2k analysis
        # TODO: Print 2k analysis tables for latex
        pass

    elif args.plot:
        generate_plots(test_configs)
    elif args.install:
        installer = Installer()
        installer.set_private_key()
        installer.install_memtier()
        installer.install_memcached()
        installer.install_middleware()
    else:
        runner = TestRunner(args.repetitions, args.local)
        for test_config in test_configs:
                runner.run_test(test_config.run_configuration, test_config.log_dir)


