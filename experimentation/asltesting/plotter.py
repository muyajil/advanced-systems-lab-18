import os
import pandas as pd
from matplotlib import pyplot as plt
from abc import ABC, abstractmethod
from asltesting.analyzer import MiddlewareAnalyzer, MemtierAnalyzer
from asltesting.image import merge_images
from glob import glob

# TODO: save processed data!
YLABELS = {
    "set_tp_s": "Ops/Sec",
    "get_tp_s": "Ops/Sec",
    "set_rt_ms": "ms",
    "get_rt_ms": "ms",
    "get_service_time_ms": "ms",
    "set_service_time_ms": "ms",
    "interactive_set_rt_ms" : "ms",
    "interactive_get_rt_ms" : "ms",
    "queue_length": "Number of Requests"
}

TITLES = {
    "set_tp_s": "SET Throughput",
    "get_tp_s": "GET Throughput",
    "set_rt_ms": "SET Response Time",
    "get_rt_ms": "GET Response Time",
    "get_service_time_ms": "GET memcached Service Time",
    "set_service_time_ms": "SET memcached Service Time",
    "interactive_set_rt_ms": "SET Response Time (Interactive Law)",
    "interactive_get_rt_ms": "GET Response Time (Interactive Law)",
    "queue_length": "Queue Length"
}

SERVER_TYPE = {
    "set_tp_s": True,
    "get_tp_s": True,
    "set_rt_ms": True,
    "get_rt_ms": True,
    "get_service_time_ms": True,
    "set_service_time_ms": True,
    "interactive_set_rt_ms": False,
    "interactive_get_rt_ms": False,
    "queue_length": False
}

YLIMS = {
    "set_tp_s": 17000,
    "get_tp_s": 17000,
    "set_rt_ms": 50,
    "get_rt_ms": 100,
    "get_service_time_ms": 50,
    "set_service_time_ms": 50,
    "interactive_set_rt_ms": 50,
    "interactive_get_rt_ms": 50,
    "queue_length": 300
}


class Plotter(ABC):

    @staticmethod
    @abstractmethod
    def get_datapoint(log_dir, total_clients):
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def get_server_type():
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def get_plot_types():
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def get_response_times(log_dir):
        raise NotImplementedError()

    def get_plot_dataframes(self, run_configuration, base_log_dir, num_threads_per_mw, workload):
        dfs = []
        for num_clients_per_thread in run_configuration['num_clients_per_thread_range']:
            log_dir = os.path.join(base_log_dir,
                                   *[
                                       str(num_threads_per_mw),
                                       str(num_clients_per_thread),
                                       '-'.join(map(lambda x: str(x), workload)),
                                   ])

            total_clients = num_clients_per_thread * run_configuration['num_client_machines'] * run_configuration['num_memtier_per_client'] * run_configuration['num_threads_per_memtier']
            df = self.get_datapoint(log_dir, total_clients)
            dfs.append(df)

        return dfs

    def generate_histogram(self, df, plot_dir, x_label):
        # TODO: Implement Histogram
        pass

    def generate_plot(self, type, plot_data, plot_dir, x_label):
        plt.clf()
        plt.xlabel(x_label)
        plt.ylabel(YLABELS[type])
        title = TITLES[type]
        if SERVER_TYPE[type]:
            title += " ({})".format(self.get_server_type().capitalize())
        plt.title(title)
        plt.grid(True)
        plotted = False
        if len(plot_data.keys()) > 1:
            for mw_threads in plot_data:
                df = plot_data[mw_threads]
                if not df['avg_' + type].mean() == 0.0:
                    plotted = True
                    plt.errorbar(df.index.values,
                                 df['avg_' + type],
                                 marker='x',
                                 ls=':',
                                 yerr=df['conf_' + type],
                                 label="{} Middleware Threads".format(mw_threads),
                                 elinewidth=1.0,
                                 capsize=3.0)
        else:
            mw_threads = list(plot_data.keys())[0]
            percentiles = [25, 50, 75, 90, 99]
            df = plot_data[mw_threads]
            if not df['avg_' + type].mean() == 0.0:
                plotted = True

                if type in {'set_rt_ms', 'get_rt_ms'} and 'full_system_read' in plot_dir:
                    plt.errorbar(df.index.values,
                                 df['avg_' + type],
                                 marker='x',
                                 ls=':',
                                 yerr=df['conf_' + type],
                                 label="Average Response Time",
                                 elinewidth=1.0,
                                 capsize=3.0)
                    for percentile in percentiles:
                        plt.errorbar(df.index.values,
                                     df[type + '_' + str(percentile)],
                                     marker='x',
                                     ls=':',
                                     yerr=df['conf_' + type],
                                     label="{}th Percentile".format(percentile),
                                     elinewidth=1.0,
                                     capsize=3.0)
                else:
                    plt.errorbar(df.index.values,
                                 df['avg_' + type],
                                 marker='x',
                                 ls=':',
                                 yerr=df['conf_' + type],
                                 label="{} Middleware Threads".format(mw_threads),
                                 elinewidth=1.0,
                                 capsize=3.0)

        if plotted:
            plt.legend()
            plt.ylim(bottom=0, top=YLIMS[type])
            file_name = self.get_server_type() + '_' + type + '.png'
            path = os.path.join(plot_dir, file_name)
            plt.savefig(path)
            print("Generated plot {}".format(path))

    def generate_plots(self, plot_data, plot_dir, x_label):
        if not os.path.exists(plot_dir):
            os.makedirs(plot_dir)

        plot_types = self.get_plot_types()

        for plot_type in plot_types:
            self.generate_plot(plot_type, plot_data, plot_dir, x_label)

        plot_files = glob(plot_dir + '/*')
        merge_images(sorted(plot_files), os.path.join(plot_dir, 'all.png'))

    def plot_workload_range(self, run_configuration, base_log_dir, plot_dir, num_threads_per_mw):
        dfs = []
        plot_data = dict()
        for workload in run_configuration['workloads']:
            workload_str = "-".join(map(lambda x: str(x), workload))
            df = self.get_plot_dataframes(run_configuration, base_log_dir, num_threads_per_mw, workload)[0]
            df['workload'] = workload_str
            dfs.append(df)
            #self.generate_histogram(self.get_response_times())
        plot_data[num_threads_per_mw] = pd.concat(dfs).set_index('workload')
        # TODO: Call self.generate_histogram
        self.generate_plots(plot_data, os.path.join(plot_dir, str(num_threads_per_mw)), "Workload")

    def plot_thread_range(self, run_configuration, base_log_dir, plot_dir, workload):
        plot_data = dict()
        for num_threads_per_mw in run_configuration['num_threads_per_mw_range']:
            dfs = self.get_plot_dataframes(run_configuration, base_log_dir, num_threads_per_mw, workload)

            plot_data[num_threads_per_mw] = pd.concat(dfs).set_index('num_clients')

        self.generate_plots(plot_data, os.path.join(plot_dir, "-".join(map(lambda x: str(x), workload))), "Number of Clients")

    def plot_test(self, run_configuration, base_log_dir, plot_dir):
        if len(run_configuration['num_threads_per_mw_range']) == 1 and run_configuration['num_threads_per_mw_range'][0] != 0:
            for num_threads_per_mw in run_configuration['num_threads_per_mw_range']:
                self.plot_workload_range(run_configuration, base_log_dir, plot_dir, num_threads_per_mw)
        else:
            for workload in run_configuration['workloads']:
                self.plot_thread_range(run_configuration, base_log_dir, plot_dir, workload)


class MiddlewarePlotter(Plotter):

    @staticmethod
    def get_response_times(log_dir):
        df = MiddlewareAnalyzer.get_dataframe(log_dir)
        return df['ResponseTimeMilli']

    @staticmethod
    def get_datapoint(log_dir, total_clients):
        return pd.DataFrame.from_dict(MiddlewareAnalyzer.get_datapoint(log_dir, total_clients))

    @staticmethod
    def get_plot_types():
        return ['set_rt_ms', 'set_tp_s', 'get_rt_ms', 'get_tp_s', 'queue_length', 'interactive_set_rt_ms', 'interactive_get_rt_ms', "get_service_time_ms", "set_service_time_ms"]

    @staticmethod
    def get_server_type():
        return 'middleware'


class MemtierPlotter(Plotter):

    @staticmethod
    def get_response_times(log_dir):
        df = MemtierAnalyzer.get_dataframe(log_dir)
        return df['ResponseTimeMilli']

    @staticmethod
    def get_datapoint(log_dir, total_clients):
        return pd.DataFrame.from_dict(MemtierAnalyzer.get_datapoint(log_dir, total_clients))

    @staticmethod
    def get_plot_types():
        return ['set_rt_ms', 'set_tp_s', 'get_rt_ms', 'get_tp_s']

    @staticmethod
    def get_server_type():
        return 'memtier'
