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
    def get_mw_range_stats(dataframe, seconds_bins):

        if dataframe.empty:
            return 0, 0, 0, 0, 0

        avg_rt_ms = dataframe['ResponseTimeMilli'].mean()
        conf_rt_ms = Plotter.get_confidence_interval(dataframe['ResponseTimeMilli'])
        tps = []
        for middleware_id in dataframe['MiddlewareId'].unique():
            temp_df = dataframe[dataframe.MiddlewareId == middleware_id]
            temp_tps, _ = np.histogram(temp_df['ReturnedToClientNano'], bins=int(seconds_bins))
            tps.append(pd.DataFrame(temp_tps))
        tps = pd.concat(tps)
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
        plotted = False
        # TODO: handle threads configs vs get size configs (different plot methods?)
        for num_threads_per_mw in plot_data:

            df = plot_data[num_threads_per_mw]
            if not df['avg_' + type].mean() == 0.0:
                plotted = True
                plt.errorbar(df.index.values,
                             df['avg_' + type],
                             marker='x',
                             ls=':',
                             yerr=df['conf_' + type],
                             label="{} Middleware Threads".format(num_threads_per_mw),
                             elinewidth=1.0,
                             capsize=3.0)

        if plotted:
            plt.legend()
            plt.ylim(bottom=0)
            path = os.path.join(plot_dir, server_type + '_' + type + '.png')
            plt.savefig(path)
            print("Generated plot {}".format(path))

    @staticmethod
    def generate_plots(server_type, plot_data, plot_dir):
        if not os.path.exists(plot_dir):
            os.makedirs(plot_dir)

        plot_types = ['set_rt_ms', 'set_tp_s', 'get_rt_ms', 'get_tp_s']
        if server_type == 'middleware':
            plot_types.extend(['queue_length', 'interactive_set_rt_ms', 'interactive_get_rt_ms'])

        for plot_type in plot_types:
            Plotter.generate_plot(plot_type, plot_data, plot_dir, server_type)

    @staticmethod
    def plot_data(run_configuration, base_log_dir, plot_dir, workload, server_type):
        plot_data = dict()
        for num_threads_per_mw in run_configuration['num_threads_per_mw_range']:
            dataframes = []
            for num_clients_per_thread in run_configuration['num_clients_per_thread_range']:
                log_dir = os.path.join(base_log_dir,
                                       *[
                                           str(num_threads_per_mw),
                                           str(num_clients_per_thread),
                                           '-'.join(map(lambda x: str(x), workload)),
                                       ])

                total_clients = num_clients_per_thread * run_configuration['num_client_machines'] * run_configuration['num_memtier_per_client'] * run_configuration['num_threads_per_memtier']

                if server_type == 'memtier':
                    dataframes.append(pd.DataFrame.from_dict(Plotter.get_memtier_data_point(log_dir, total_clients)))
                else:
                    dataframes.append(pd.DataFrame.from_dict(Plotter.get_middleware_data_point(log_dir, total_clients)))

            plot_data[num_threads_per_mw] = pd.concat(dataframes).set_index('num_clients')

        Plotter.generate_plots(server_type, plot_data, os.path.join(plot_dir, "-".join(map(lambda x: str(x), workload))))

    @staticmethod
    def plot_memtier_data(run_configuration, base_log_dir, plot_dir, workload):
        Plotter.plot_data(run_configuration, base_log_dir, plot_dir, workload, 'memtier')

    @staticmethod
    def plot_middleware_data(run_configuration, base_log_dir, plot_dir, workload):
        Plotter.plot_data(run_configuration, base_log_dir, plot_dir, workload, 'middleware')

    @staticmethod
    def plot_test(run_configuration, base_log_dir, plot_dir):

        if len(run_configuration['num_threads_per_mw_range']) == 1 and run_configuration['num_threads_per_mw_range'][0] != 0:
            # TODO: For each workload generate a line

            pass
        else:
            for workload in run_configuration['workloads']:
                Plotter.plot_memtier_data(run_configuration, base_log_dir, plot_dir, workload)
                if run_configuration['num_threads_per_mw_range'][0] > 0:
                    Plotter.plot_middleware_data(run_configuration, base_log_dir, plot_dir, workload)


    @staticmethod
    def get_middleware_data_point(log_dir, num_clients):
        middleware_log_files = glob(log_dir + '/*/middleware/*')

        dataframes = []
        uptimes = []

        for idx, middleware_log_file in enumerate(middleware_log_files):
            temp_dataframe = pd.read_csv(middleware_log_file).dropna()
            server_start = temp_dataframe['EnqueueNano'].min() + 1e10
            server_stop = temp_dataframe['ReturnedToClientNano'].max() - 1e10
            temp_dataframe = temp_dataframe[temp_dataframe.EnqueueNano > server_start]
            temp_dataframe = temp_dataframe[temp_dataframe.ReturnedToClientNano < server_stop]
            temp_dataframe['MiddlewareId'] = idx
            dataframes.append(temp_dataframe)
            uptimes.append((server_stop - server_start)/1e9)

        dataframe = pd.concat(dataframes)

        s_bins = np.mean(uptimes)

        dataframe['ResponseTimeMilli'] = (dataframe['ReturnedToClientNano'] - dataframe['EnqueueNano']) / 1e6

        set_dataframe = dataframe[dataframe.RequestType == 'SET']
        get_dataframe = dataframe[(dataframe.RequestType == 'GET') | (dataframe.RequestType == 'MULTI-GET')]

        avg_queue_length = dataframe['QueueLength'].mean()
        conf_queue_length = Plotter.get_confidence_interval(dataframe['QueueLength'])

        avg_set_rt_ms, conf_set_rt_ms, avg_set_tp_s, conf_set_tp_s, avg_interactive_set_rt_ms = Plotter.get_mw_range_stats(set_dataframe, s_bins)
        avg_get_rt_ms, conf_get_rt_ms, avg_get_tp_s, conf_get_tp_s, avg_interactive_get_rt_ms = Plotter.get_mw_range_stats(get_dataframe, s_bins)

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

    @staticmethod
    def get_memtier_data_point(log_dir, num_clients):
        repetitions = glob(log_dir + '/*/')

        dataframes = []
        tps = []

        for repetition in repetitions:
            client_stats_files = glob(repetition + '/memtier/*clients*')
            temp_tps = []
            for client_stats_file in client_stats_files:
                temp_dataframe = pd.read_csv(client_stats_file, header=1).dropna().astype(float)
                temp_dataframe = temp_dataframe[temp_dataframe.Second > 10]
                temp_dataframe = temp_dataframe[temp_dataframe.Second < len(temp_dataframe) - 10]
                temp_tps.append(temp_dataframe[['SET Requests', 'GET Requests']])
                dataframes.append(temp_dataframe)
            tps.append(reduce(lambda x, y: x.add(y), temp_tps))

        dataframe = pd.concat(dataframes)
        tp_dataframe = pd.concat(tps)

        avg_set_tp_s, conf_set_tp_s = tp_dataframe['SET Requests'].mean(), Plotter.get_confidence_interval(dataframe['SET Requests'])
        avg_get_tp_s, conf_get_tp_s = tp_dataframe['GET Requests'].mean(), Plotter.get_confidence_interval(dataframe['GET Requests'])

        avg_set_rt_ms, conf_set_rt_ms = (dataframe['SET Average Latency']*1000).mean(), Plotter.get_confidence_interval(dataframe['SET Average Latency']*1000)
        avg_get_rt_ms, conf_get_rt_ms = (dataframe['GET Average Latency']*1000).mean(), Plotter.get_confidence_interval(dataframe['GET Average Latency']*1000)

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
