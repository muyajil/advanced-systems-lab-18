import pandas as pd
import numpy as np
from glob import glob
from functools import reduce
from abc import ABC, abstractmethod


class Analyzer(ABC):

    @staticmethod
    def get_confidence_interval(df):
        return 1.96*(df.std()/np.sqrt(len(df)))

    @staticmethod
    @abstractmethod
    def get_datapoint(log_dir, num_clients):
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def get_performance(df, op_key):
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def get_dataframe(log_dir):
        raise NotImplementedError()


class MemtierAnalyzer(Analyzer):

    @staticmethod
    def get_dataframe(log_dir):
        repetitions = glob(log_dir + '/*/')

        dfs = []

        for rep_id, repetition in enumerate(repetitions):
            client_stats_files = glob(repetition + '/memtier/*clients*')
            for client_id, client_stats_file in enumerate(client_stats_files):
                temp_df = pd.read_csv(client_stats_file, header=1).dropna().astype(float)
                temp_df = temp_df[temp_df.Second > 10]
                temp_df = temp_df[temp_df.Second < len(temp_df) - 10]
                temp_df['HostId'] = client_id
                temp_df['Repetition'] = rep_id
                dfs.append(temp_df)

        df = pd.concat(dfs)
        return df

    @staticmethod
    def get_datapoint(log_dir, num_clients):
        df = MemtierAnalyzer.get_dataframe(log_dir)
        set_df = df[df['SET Requests'] > 0]
        get_df = df[df['GET Requests'] > 0]
        (avg_set_rt_ms,
         set_rt_ms_25,
         set_rt_ms_50,
         set_rt_ms_75,
         set_rt_ms_90,
         set_rt_ms_99,
         conf_set_rt_ms,
         avg_set_tp_s,
         conf_set_tp_s) = MemtierAnalyzer.get_performance(set_df, 'SET')

        (avg_get_rt_ms,
         get_rt_ms_25,
         get_rt_ms_50,
         get_rt_ms_75,
         get_rt_ms_90,
         get_rt_ms_99,
         conf_get_rt_ms,
         avg_get_tp_s,
         conf_get_tp_s) = MemtierAnalyzer.get_performance(get_df, 'GET')

        miss_rate = 0
        if df['GET Requests'].sum() > 0:
            miss_rate = df['GET Misses'].sum() / df['GET Requests'].sum()

        return {
            "num_clients": [num_clients],

            "avg_set_rt_ms": [avg_set_rt_ms],
            "set_rt_ms_25": [set_rt_ms_25],
            "set_rt_ms_50": [set_rt_ms_50],
            "set_rt_ms_75": [set_rt_ms_75],
            "set_rt_ms_90": [set_rt_ms_90],
            "set_rt_ms_99": [set_rt_ms_99],
            "conf_set_rt_ms": [conf_set_rt_ms],
            "avg_set_tp_s": [avg_set_tp_s],
            "conf_set_tp_s": [conf_set_tp_s],

            "avg_get_rt_ms": [avg_get_rt_ms],
            "get_rt_ms_25": [get_rt_ms_25],
            "get_rt_ms_50": [get_rt_ms_50],
            "get_rt_ms_75": [get_rt_ms_75],
            "get_rt_ms_90": [get_rt_ms_90],
            "get_rt_ms_99": [get_rt_ms_99],
            "conf_get_rt_ms": [conf_get_rt_ms],
            "avg_get_tp_s": [avg_get_tp_s],
            "conf_get_tp_s": [conf_get_tp_s],

            "miss_rate": [miss_rate]
        }

    @staticmethod
    def get_performance(df, op_key):

        if df.empty:
            return 0, 0, 0, 0, 0, 0, 0, 0, 0

        avg_rt_ms = (df[op_key + ' Average Latency'] * 1000).mean()
        rt_ms_25 = (df[op_key + ' Average Latency'] * 1000).quantile(0.25)
        rt_ms_50 = (df[op_key + ' Average Latency'] * 1000).quantile(0.5)
        rt_ms_75 = (df[op_key + ' Average Latency'] * 1000).quantile(0.75)
        rt_ms_90 = (df[op_key + ' Average Latency'] * 1000).quantile(0.90)
        rt_ms_99 = (df[op_key + ' Average Latency'] * 1000).quantile(0.99)
        conf_rt_ms = Analyzer.get_confidence_interval(df[op_key + ' Average Latency'] * 1000)

        tps = []
        for rep_id in df['Repetition'].unique():
            rep_df = df[df.Repetition == rep_id]
            rep_tps = []
            for host_id in df['HostId'].unique():
                host_df = rep_df[rep_df.HostId == host_id]
                host_tps = host_df[op_key + ' Requests']
                rep_tps.append(pd.DataFrame(host_tps))
            tps.append(pd.DataFrame(reduce(lambda x, y: x.add(y), rep_tps)))
        tps = pd.concat(tps)
        avg_tp_s = tps.mean()
        conf_tp_s = Analyzer.get_confidence_interval(tps)

        return avg_rt_ms, rt_ms_25, rt_ms_50, rt_ms_75, rt_ms_90, rt_ms_99, conf_rt_ms, avg_tp_s, conf_tp_s

class MiddlewareAnalyzer(Analyzer):

    @staticmethod
    def get_dataframe(log_dir):
        repetitions = glob(log_dir + "/*/")

        dfs = []
        uptimes = []

        for rep_id, repetitions in enumerate(repetitions):
            middleware_log_files = glob(repetitions + '/middleware/*')
            for middleware_id, middleware_log_file in enumerate(middleware_log_files):
                temp_df = pd.read_csv(middleware_log_file).dropna()
                server_start = temp_df['EnqueueNano'].min() + 1e10
                server_stop = temp_df['ReturnedToClientNano'].max() - 1e10
                temp_df = temp_df[temp_df.EnqueueNano > server_start]
                temp_df = temp_df[temp_df.ReturnedToClientNano < server_stop]
                temp_df['HostId'] = middleware_id
                temp_df['Repetition'] = rep_id
                dfs.append(temp_df)
                uptimes.append((server_stop - server_start) / 1e9)

        df = pd.concat(dfs)
        return df, uptimes

    @staticmethod
    def get_datapoint(log_dir, num_clients):
        df, uptimes = MiddlewareAnalyzer.get_dataframe(log_dir)

        s_bins = np.mean(uptimes)

        set_df = df[df.RequestType == 'SET']
        get_df = df[(df.RequestType == 'GET') | (df.RequestType == 'MULTI-GET')]

        avg_queue_length = df['QueueLength'].mean()
        conf_queue_length = Analyzer.get_confidence_interval(df['QueueLength'])

        (avg_set_rt_ms,
         set_rt_ms_25,
         set_rt_ms_50,
         set_rt_ms_75,
         set_rt_ms_90,
         set_rt_ms_99,
         conf_set_rt_ms,
         avg_set_tp_s,
         conf_set_tp_s,
         avg_interactive_set_rt_ms) = MiddlewareAnalyzer.get_performance(set_df, s_bins)

        (avg_get_rt_ms,
         get_rt_ms_25,
         get_rt_ms_50,
         get_rt_ms_75,
         get_rt_ms_90,
         get_rt_ms_99,
         conf_get_rt_ms,
         avg_get_tp_s,
         conf_get_tp_s,
         avg_interactive_get_rt_ms) = MiddlewareAnalyzer.get_performance(get_df, s_bins)

        miss_rate = 0
        if len(get_df) > 0:
            miss_rate = len(get_df[~get_df.IsSuccessful]) / len(get_df)

        return {
            "num_clients": [num_clients],

            "avg_set_rt_ms": [avg_set_rt_ms],
            "set_rt_ms_25" : [set_rt_ms_25],
            "set_rt_ms_50" : [set_rt_ms_50],
            "set_rt_ms_75" : [set_rt_ms_75],
            "set_rt_ms_90" : [set_rt_ms_90],
            "set_rt_ms_99" : [set_rt_ms_99],
            "conf_set_rt_ms": [conf_set_rt_ms],
            "avg_set_tp_s": [avg_set_tp_s],
            "conf_set_tp_s": [conf_set_tp_s],
            "avg_interactive_set_rt_ms": [avg_interactive_set_rt_ms],
            "conf_interactive_set_rt_ms": [0],

            "avg_get_rt_ms": [avg_get_rt_ms],
            "get_rt_ms_25": [get_rt_ms_25],
            "get_rt_ms_50": [get_rt_ms_50],
            "get_rt_ms_75": [get_rt_ms_75],
            "get_rt_ms_90": [get_rt_ms_90],
            "get_rt_ms_99": [get_rt_ms_99],
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
    def get_performance(df, seconds_bins):

        if df.empty:
            return 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

        df['ResponseTimeMilli'] = (df['ReturnedToClientNano'] - df['EnqueueNano']) / 1e6
        avg_rt_ms = df['ResponseTimeMilli'].mean()
        rt_ms_25 = df['ResponseTimeMilli'].quantile(0.25)
        rt_ms_50 = df['ResponseTimeMilli'].quantile(0.5)
        rt_ms_75 = df['ResponseTimeMilli'].quantile(0.75)
        rt_ms_90 = df['ResponseTimeMilli'].quantile(0.90)
        rt_ms_99 = df['ResponseTimeMilli'].quantile(0.99)
        conf_rt_ms = Analyzer.get_confidence_interval(df['ResponseTimeMilli'])
        tps = []
        for rep_id in df['Repetition'].unique():
            rep_df = df[df.Repetition == rep_id]
            rep_tps = []
            for host_id in rep_df['HostId'].unique():
                host_df = rep_df[rep_df.HostId == host_id]
                host_tps, _ = np.histogram(host_df['ReturnedToClientNano'], bins=int(seconds_bins))
                rep_tps.append(pd.DataFrame(host_tps))
            tps.append(pd.DataFrame(reduce(lambda x, y: x.add(y), rep_tps)))
        tps = pd.concat(tps)
        avg_tp_s = tps.mean()
        conf_tp_s = Analyzer.get_confidence_interval(tps)

        avg_think_time = ((df['ReturnedToClientNano'] - df['ReceivedFromServerNano']) / 1e9).mean()
        avg_interactive_rt_ms = (df['ClientId'].nunique() / avg_tp_s - avg_think_time) * 1000

        return avg_rt_ms, rt_ms_25, rt_ms_50, rt_ms_75, rt_ms_90, rt_ms_99, conf_rt_ms, avg_tp_s, conf_tp_s, avg_interactive_rt_ms
