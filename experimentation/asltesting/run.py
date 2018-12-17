import os
import argparse
from asltesting.test_configuration import TestConfiguration
from asltesting.plotter import MiddlewarePlotter, MemtierPlotter
from asltesting.test_runner import TestRunner
from asltesting import paths
from asltesting.install import Installer
from asltesting.twok_analyzer import TwoKAnalyzer
import time
from shutil import copyfile, copytree, rmtree
from glob import glob
import pandas as pd


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
                mw_plotter.plot_test(test_config.run_configuration, test_config.log_dir, os.path.join(plot_dir, test_config.name))
            else:
                mw_plotter.plot_test(test_config.run_configuration, test_config.log_dir, test_config.plot_dir)


def move_and_sample_logs(test_configs, submission_dir):
    for test_config in test_configs:
        print('Processing {}'.format(test_config.name))
        for workload in test_config.run_configuration['workloads']:
            for num_threads_per_mw in test_config.run_configuration['num_threads_per_mw_range']:
                for num_clients_per_thread in test_config.run_configuration['num_clients_per_thread_range']:
                    for iteration in range(3):
                        old_log_dir = os.path.join(test_config.log_dir,
                                        *[
                                            str(num_threads_per_mw),
                                            str(num_clients_per_thread),
                                            '-'.join(map(lambda x: str(x), workload)),
                                            str(iteration)
                                        ])

                        if not os.path.exists(old_log_dir):
                            continue

                        new_log_dir =  os.path.join(submission_dir,
                                        *[
                                            str(test_config.name),
                                            str(num_threads_per_mw),
                                            str(num_clients_per_thread),
                                            '-'.join(map(lambda x: str(x), workload)),
                                            str(iteration)
                                        ])

                        if os.path.exists(os.path.join(new_log_dir, 'memtier')):
                            rmtree(os.path.join(new_log_dir, 'memtier'))
                        copytree(os.path.join(old_log_dir, 'memtier'), os.path.join(new_log_dir, 'memtier'))
                        
                        middleware_log_files = glob(old_log_dir + '/middleware/*.log')
                        for mw_id, middleware_log_file in enumerate(middleware_log_files):
                            df = pd.read_csv(middleware_log_file).sample(1000)
                            folder_path = os.path.join(new_log_dir, 'middleware')
                            os.makedirs(folder_path, exist_ok=True)
                            df.to_csv(os.path.join(folder_path, str(mw_id + 1) + '.log'))


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
        raise RuntimeError('At least one test name must be specified')

    if args.prepare_submission:
        if args.run_id is None:
            raise RuntimeError("Prepare submission must refer to a run_id")

        generate_plots(test_configs, paths.Absolute.SUBMISSION_PLOTS)
        move_and_sample_logs(test_configs, paths.Absolute.SUBMISSION_LOGS)
        copyfile('../report/report.pdf', '../report.pdf')

    elif args.two_k_analysis:
        test_configs = list(map(lambda test_name: TestConfiguration(test_name, run_id),
                                filter(lambda x: '2k' in x,
                                       sorted(os.listdir(paths.Absolute.TESTS)))))

        twoKAnalyzer = TwoKAnalyzer(test_configs)
        twoKAnalyzer.generate_sign_table('1-0')
        twoKAnalyzer.generate_sign_table('0-1')

    elif args.plot:
        if args.run_id is None:
             raise RuntimeError("Plotting must refer to a run_id")
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


