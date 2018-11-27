import seaborn
import os
import pandas

class Plotter(object):

    def __init__(self, num_runs):
        self.num_runs = num_runs

    def plot_test(self, test_config):
        raise NotImplementedError

    def get_middleware_data(self, test_config):
        pass

    def get_middleware_values(run_configuration, base_log_dir):
        os.path.join(test_config.log_dir,
                     *[
                         str(test_config.run_configuration['num_threads_per_mw']),
                         str(num_clients_per_thread),
                         '-'.join(map(lambda x: str(x), workload)),
                         str(iteration)
                     ]))