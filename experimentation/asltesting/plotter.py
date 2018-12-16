import os
import pandas as pd
from matplotlib import pyplot as plt
from abc import ABC, abstractmethod
from asltesting.analyzer import MiddlewareAnalyzer, MemtierAnalyzer
from asltesting.image import merge_images
from glob import glob

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
    "set_tp_s": 18000,
    "get_tp_s": 18000,
    "set_rt_ms": 50,
    "get_rt_ms": 100,
    "get_service_time_ms": 50,
    "set_service_time_ms": 50,
    "interactive_set_rt_ms": 50,
    "interactive_get_rt_ms": 100,
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
    def get_response_times(log_dir, workload):
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
            if os.path.exists(log_dir):
                total_clients = num_clients_per_thread * run_configuration['num_client_machines'] * run_configuration['num_memtier_per_client'] * run_configuration['num_threads_per_memtier']
                df = self.get_datapoint(log_dir, total_clients)
                dfs.append(df)

        return dfs

    def generate_histogram(self, plot_dir, base_log_dir, run_configuration, workload):

        num_threads_per_mw = run_configuration['num_threads_per_mw_range'][0]
        num_clients_per_thread = run_configuration['num_clients_per_thread_range'][0]
        log_dir = os.path.join(base_log_dir,
                               *[
                                   str(num_threads_per_mw),
                                   str(num_clients_per_thread),
                                   workload,
                               ])
        df = self.get_response_times(log_dir, workload)
        bins = 40
        cutoff_msec = 20
        request_types = ['SET', 'GET']
        if 'ResponseTimeMilli' in df.columns:
            for request_type in request_types:
                plt.clf()
                plt.title(request_type + ': Middleware Response Time Histogram\ncapped at {}msec'.format(cutoff_msec))
                df[(df.RequestType.str.contains(request_type)) & (df.ResponseTimeMilli < cutoff_msec)]['ResponseTimeMilli'].hist(bins=bins, density=True)
                plt.xlabel('ms')
                plt.ylabel('density')
                plt.ylim((0,1))
                plt.grid(True)
                plt.savefig(os.path.join(plot_dir, "_".join(('middleware', request_type.lower(), 'hist.png'))))
        else:
            for request_type in df['Type'].unique():
                plt.clf()
                dfs = []
                for repetition in df['repetition'].unique():
                    for client_id in df['client_id'].unique():
                        temp_df = df[(df.repetition == repetition) & (df.Type == request_type) & (df.client_id == client_id)].sort_values('msec')
                        diff = temp_df['percent'][1:].reset_index(drop=True) - temp_df['percent'][:-1].reset_index(drop=True)
                        client_data = temp_df[['Type', 'msec']][1:].reset_index(drop=True)

                        client_data['percentage'] = diff
                        dfs.append(client_data)

                type_df = pd.concat(dfs)

                plt.hist(type_df[type_df.msec < cutoff_msec]['msec'], bins=bins, weights=type_df[type_df.msec < cutoff_msec]['percentage'], density=True)
                plt.title(request_type + ': Memtier Response Time Histogram\ncapped at {}msec'.format(cutoff_msec))
                plt.xlabel('ms')
                plt.grid(True)
                plt.ylabel('density')
                plt.ylim((0, 1))
                os.makedirs(plot_dir, exist_ok=True)
                plt.savefig(os.path.join(plot_dir, "_".join(('memtier', request_type.lower(), 'hist.png'))))

    def generate_plot(self, req_type, plot_data, plot_dir, x_label):
        plt.clf()
        plt.xlabel(x_label)
        plt.ylabel(YLABELS[req_type])
        title = TITLES[req_type]
        if SERVER_TYPE[req_type]:
            title += " ({})".format(self.get_server_type().capitalize())
        plt.title(title)
        plt.grid(True)
        plotted = False
        if len(plot_data.keys()) > 1:
            for mw_threads in plot_data:
                df = plot_data[mw_threads]
                if not df['avg_' + req_type].mean() == 0.0:
                    plotted = True
                    plt.errorbar(df.index.values,
                                 df['avg_' + req_type],
                                 marker='x',
                                 ls=':',
                                 yerr=df['conf_' + req_type],
                                 label="{} Middleware Threads".format(mw_threads),
                                 elinewidth=1.0,
                                 capsize=3.0)
        else:
            mw_threads = list(plot_data.keys())[0]
            percentiles = [25, 50, 75, 90, 99]
            df = plot_data[mw_threads]
            if not df['avg_' + req_type].mean() == 0.0:
                plotted = True

                if req_type in {'set_rt_ms', 'get_rt_ms'} and 'full_system_read' in plot_dir:
                    plt.errorbar(df.index.values,
                                 df['avg_' + req_type],
                                 marker='x',
                                 ls=':',
                                 yerr=df['conf_' + req_type],
                                 label="Average Response Time",
                                 elinewidth=1.0,
                                 capsize=3.0)
                    
                    if type(self) == MiddlewarePlotter:
                        for percentile in percentiles:
                            plt.errorbar(df.index.values,
                                        df[req_type + '_' + str(percentile)],
                                        marker='x',
                                        ls=':',
                                        yerr=df['conf_' + req_type],
                                        label="{}th Percentile".format(percentile),
                                        elinewidth=1.0,
                                        capsize=3.0)
                else:
                    plt.errorbar(df.index.values,
                                 df['avg_' + req_type],
                                 marker='x',
                                 ls=':',
                                 yerr=df['conf_' + req_type],
                                 label="{} Middleware Threads".format(mw_threads),
                                 elinewidth=1.0,
                                 capsize=3.0)

        if plotted:
            plt.legend()
            if 'reduced' in plot_dir and 'rt_ms' in req_type:
                plt.ylim(bottom=0, top=20)
            elif 'full_system_read' in plot_dir and 'rt_ms' in req_type:
                plt.ylim(bottom=0, top=50)
            elif '2_1_one_middleware' in plot_dir and 'set_service_time' in req_type:
                plt.ylim(bottom=0, top=10)
            else:
                plt.ylim(bottom=0, top=YLIMS[req_type])

            file_name = self.get_server_type() + '_' + req_type + '.png'
            path = os.path.join(plot_dir, file_name)
            plt.savefig(path)
            print("Generated plot {}".format(path))

    def save_plot_data(self, plot_data, plot_dir):
        dfs = []
        for num_threads in plot_data:
            temp_df = plot_data[num_threads]
            temp_df['num_workers'] = num_threads
            dfs.append(temp_df)

        df = pd.concat(dfs)
        df.to_csv(os.path.join(plot_dir, self.get_server_type() + '_plot_data.csv'))

    def generate_plots(self, plot_data, plot_dir, x_label):
        if not os.path.exists(plot_dir):
            os.makedirs(plot_dir)

        self.save_plot_data(plot_data, plot_dir)

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
            if workload_str == '1-6':
                self.generate_histogram(os.path.join(plot_dir, str(num_threads_per_mw)),base_log_dir, run_configuration, workload_str)
        plot_data[num_threads_per_mw] = pd.concat(dfs).set_index('workload')
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
    def get_response_times(log_dir, workload):
        df, _ = MiddlewareAnalyzer.get_dataframe(log_dir)
        df['ResponseTimeMilli'] = (df['ReturnedToClientNano'] - df['StartReceivingNano']) / 1e6
        return df[['ResponseTimeMilli', 'RequestType']]

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
    def get_response_times(log_dir, workload):
        df = MemtierAnalyzer.get_response_times(log_dir, workload)
        return df

    @staticmethod
    def get_datapoint(log_dir, total_clients):
        return pd.DataFrame.from_dict(MemtierAnalyzer.get_datapoint(log_dir, total_clients))

    @staticmethod
    def get_plot_types():
        return ['set_rt_ms', 'set_tp_s', 'get_rt_ms', 'get_tp_s']

    @staticmethod
    def get_server_type():
        return 'memtier'
