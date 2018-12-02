import os
import pandas as pd
import numpy as np
from glob import glob
from matplotlib import pyplot as plt
from functools import reduce

# TODO: save processed data!
YLABELS = {
    "set_tp_s": "Ops/Sec",
    "get_tp_s": "Ops/Sec",
    "set_rt_ms": "ms",
    "get_rt_ms": "ms",
    "interactive_set_rt_ms" : "ms",
    "interactive_get_rt_ms" : "ms",
    "queue_length": "Number of Requests"
}

TITLES = {
    "set_tp_s": "SET Throughput",
    "get_tp_s": "GET Throughput",
    "set_rt_ms": "SET Response Time",
    "get_rt_ms": "GET Response Time",
    "interactive_set_rt_ms": "SET Response Time Interactive Law",
    "interactive_get_rt_ms": "GET Response Time Interactive Law",
    "queue_length": "Queue Length"
}

class Plotter(object):

    def __init__(self, num_runs):
        self.num_runs = num_runs
        self.base_log_dir = None

    @staticmethod
    def get_confidence_interval(dataframe):
        return 1.96*(dataframe.std()/np.sqrt(len(dataframe)))

    @staticmethod
    def get_range_stats(dataframe, seconds_bins):

        avg_rt_ms = dataframe['ResponseTimeMilli'].mean()
        conf_rt_ms = Plotter.get_confidence_interval(dataframe['ResponseTimeMilli'])

        tps, _ = np.histogram(dataframe['ReturnedToClientNano'], bins=int(seconds_bins))
        avg_tp_s = tps.mean()
        conf_tp_s = Plotter.get_confidence_interval(tps)

        avg_think_time = ((dataframe['ReturnedToClientNano'] - dataframe['ReceivedFromServerNano']) / 1e9).mean()
        avg_interactive_rt_ms = (dataframe['ClientId'].nunique() / avg_tp_s - avg_think_time)*1000

        return avg_rt_ms, conf_rt_ms, avg_tp_s, conf_tp_s, avg_interactive_rt_ms

    @staticmethod
    def generate_plot(type, plot_data, plot_dir, server_type):
        plt.clf()
        plt.xlabel("Number of Clients")
        plt.ylabel(YLABELS[type])
        plt.title(TITLES[type])
        plt.grid(True)
        # TODO: handle threads configs vs get size configs (different plot methods?)
        for num_threads_per_mw in plot_data:

            df = plot_data[num_threads_per_mw]
            plt.errorbar(df.index.values,
                         df['avg_' + type],
                         marker='x',
                         ls=':',
                         yerr=df['conf_' + type],
                         label="{} Middleware Threads".format(num_threads_per_mw),
                         elinewidth=1.0,
                         capsize=3.0)

        plt.legend()
        plt.ylim(bottom=0)
        plt.savefig(os.path.join(plot_dir, server_type + '_' + type + '.png'))

    def generate_plots(self, server_type, plot_data, plot_dir):
        if not os.path.exists(plot_dir):
            os.makedirs(plot_dir)

        plot_types = ['set_rt_ms', 'set_tp_s', 'get_rt_ms', 'get_tp_s']
        if server_type == 'middleware':
            plot_types.extend(['queue_length', 'interactive_set_rt_ms', 'interactive_get_rt_ms'])

        for plot_type in plot_types:
            self.generate_plot(plot_type, plot_data, plot_dir, server_type)

    def plot_test(self, run_configuration, base_log_dir, plot_dir):

        if len(run_configuration['num_threads_per_mw_range']) == 1:
            # TODO: For each workload generate a line
            pass
        else:
            for workload in run_configuration['workloads']:
                plot_data = dict()
                plot_data['middleware'] = dict()
                plot_data['memtier'] = dict()
                for num_threads_per_mw in run_configuration['num_threads_per_mw_range']:
                    middleware_dataframes = []
                    memtier_dataframes = []
                    for num_clients_per_thread in run_configuration['num_clients_per_thread_range']:
                        log_dir = os.path.join(base_log_dir,
                                     *[
                                         str(num_threads_per_mw),
                                         str(num_clients_per_thread),
                                         '-'.join(map(lambda x: str(x), workload)),
                                     ])

                        total_clients = num_clients_per_thread*run_configuration['num_client_machines']*run_configuration['num_memtier_per_client']*run_configuration['num_threads_per_memtier']

                        middleware_dataframes.append(pd.DataFrame.from_dict(self.get_middleware_data_point(log_dir, total_clients)))
                        memtier_dataframes.append(pd.DataFrame.from_dict(self.get_memtier_data_point(log_dir, total_clients)))
                    plot_data['middleware'][num_threads_per_mw] = pd.concat(middleware_dataframes).set_index('num_clients')
                    plot_data['memtier'][num_threads_per_mw] = pd.concat(memtier_dataframes).set_index('num_clients')

                for server_type in plot_data:
                    self.generate_plots(server_type, plot_data[server_type], os.path.join(plot_dir,"-".join(map(lambda x: str(x), workload))))

    def get_middleware_data_point(self, log_dir, num_clients):
        middleware_log_files = glob(log_dir + '/*/middleware/*')

        dataframes = []

        for middleware_log_file in middleware_log_files:
            temp_dataframe = pd.read_csv(middleware_log_file).dropna()
            server_start = temp_dataframe['EnqueueNano'].min() + 1e10
            server_stop = temp_dataframe['ReturnedToClientNano'].max() - 1e10
            temp_dataframe = temp_dataframe[temp_dataframe.EnqueueNano > server_start]
            temp_dataframe = temp_dataframe[temp_dataframe.ReturnedToClientNano < server_stop]
            dataframes.append(temp_dataframe)

        dataframe = pd.concat(dataframes)

        s_bins = int((dataframe['ReturnedToClientNano'].max() - dataframe['EnqueueNano'].min())/1e9)

        dataframe['ResponseTimeMilli'] = (dataframe['ReturnedToClientNano'] - dataframe['EnqueueNano']) / 1e6

        set_dataframe = dataframe[dataframe.RequestType == 'SET']
        get_dataframe = dataframe[(dataframe.RequestType == 'GET') & (dataframe.RequestType == 'MULTI-GET')]

        avg_queue_length = dataframe['QueueLength'].mean()
        conf_queue_length = self.get_confidence_interval(dataframe['QueueLength'])

        avg_set_rt_ms, conf_set_rt_ms, avg_set_tp_s, conf_set_tp_s, avg_interactive_set_rt_ms = Plotter.get_range_stats(set_dataframe, s_bins)
        avg_get_rt_ms, conf_get_rt_ms, avg_get_tp_s, conf_get_tp_s, avg_interactive_get_rt_ms = Plotter.get_range_stats(get_dataframe, s_bins)

        miss_rate = 0
        if len(get_dataframe) > 0:
            miss_rate = len(get_dataframe[~(get_dataframe.IsSuccessful)]) / len(get_dataframe)

        return {
            "num_clients": [num_clients],

            "avg_set_rt_ms": [avg_set_rt_ms],
            "conf_set_rt_ms": [conf_set_rt_ms],
            "avg_set_tp_s": [avg_set_tp_s],
            "conf_set_tp_s": [conf_set_tp_s],
            "avg_interactive_set_rt_ms": [avg_interactive_set_rt_ms],
            "conf_interactive_set_rt_ms": [0],

            "avg_get_rt_ms": [avg_get_rt_ms],
            "conf_get_rt_ms": [conf_get_rt_ms],
            "avg_get_tp_s": [avg_get_tp_s],
            "conf_get_tp_s": [conf_get_tp_s],
            "avg_interactive_get_rt_ms": [avg_interactive_get_rt_ms],
            "conf_interactive_get_rt_ms": [0],

            "avg_queue_length": [avg_queue_length],
            "conf_queue_length": [conf_queue_length],

            "miss_rate": [miss_rate]
        }

    def get_memtier_data_point(self, log_dir, num_clients):
        client_stats_files = glob(log_dir + '/*/memtier/*clients*')

        dataframes = []
        tps = []

        for client_stats_file in client_stats_files:
            temp_dataframe = pd.read_csv(client_stats_file, header=1).dropna().astype(float)
            temp_dataframe = temp_dataframe[temp_dataframe.Second > 10]
            temp_dataframe = temp_dataframe[temp_dataframe.Second < len(temp_dataframe) - 10]
            tps.append(temp_dataframe[['SET Requests', 'GET Requests']])
            dataframes.append(temp_dataframe)

        dataframe = pd.concat(dataframes)
        tp_dataframe = reduce(lambda x, y: x.add(y), tps)

        avg_set_tp_s, conf_set_tp_s = tp_dataframe['SET Requests'].mean(), self.get_confidence_interval(dataframe['SET Requests'])
        avg_get_tp_s, conf_get_tp_s = tp_dataframe['GET Requests'].mean(), self.get_confidence_interval(dataframe['GET Requests'])

        avg_set_rt_ms, conf_set_rt_ms = (dataframe['SET Average Latency']*1000).mean(), self.get_confidence_interval(dataframe['SET Average Latency']*1000)
        avg_get_rt_ms, conf_get_rt_ms = (dataframe['GET Average Latency']*1000).mean(), self.get_confidence_interval(dataframe['GET Average Latency']*1000)

        miss_rate = 0
        if dataframe['GET Requests'].sum() > 0:
            miss_rate = dataframe['GET Misses'].sum() / dataframe['GET Requests'].sum()

        return {
            "num_clients": [num_clients],

            "avg_set_rt_ms": [avg_set_rt_ms],
            "conf_set_rt_ms": [conf_set_rt_ms],
            "avg_set_tp_s": [avg_set_tp_s],
            "conf_set_tp_s": [conf_set_tp_s],

            "avg_get_rt_ms": [avg_get_rt_ms],
            "conf_get_rt_ms": [conf_get_rt_ms],
            "avg_get_tp_s": [avg_get_tp_s],
            "conf_get_tp_s": [conf_get_tp_s],

            "miss_rate": [miss_rate]
        }
