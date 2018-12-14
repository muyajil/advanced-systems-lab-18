from asltesting.analyzer import MiddlewareAnalyzer
import os
import pandas as pd
import itertools
import numpy as np


class TwoKAnalyzer(object):

    def __init__(self, test_configs):
        self.test_configs = test_configs
        self.num_clients = 32

        self.factors = {
            "MW": [1, 2],
            "MC": [1, 3],
            "WT": [8, 32],
        }

        self.factor_translations = {
            "MW" :{
                "1": -1,
                "2": 1
            },
            "MC": {
                "1": -1,
                "3": 1
            },
            "WT": {
                "8": -1,
                "32": 1
            }
        }

        self.header_translations = {
            "num_middlewares": "MW",
            "num_memcached_servers": "MC",
            "num_workers": "WT",
            "avg_set_rt_ms": "Avg. RT (ms)",
            "avg_get_rt_ms": "Avg. RT (ms)",
            "avg_set_tp_s": "Avg. TP (ops/sec)",
            "avg_get_tp_s": "Avg. TP (ops/sec)"
        }

        self.workloads = [[1, 0], [0, 1]]
        self.df = self.get_dataframe()

    def get_dataframe(self):
        dfs = []
        for test_config in self.test_configs:
            num_middlewares = test_config.run_configuration['num_middlewares']
            num_memcached_servers = test_config.run_configuration['num_memcached_servers']
            for num_threads_per_mw in test_config.run_configuration['num_threads_per_mw_range']:
                for workload in test_config.run_configuration['workloads']:
                    workload_str = '-'.join(map(lambda x: str(x), workload))
                    log_dir = os.path.join(
                              test_config.log_dir,
                              *[
                                  str(num_threads_per_mw),
                                  str(self.num_clients),
                                  workload_str
                              ])
                    total_clients = self.num_clients * test_config.run_configuration['num_client_machines'] * test_config.run_configuration['num_memtier_per_client'] * test_config.run_configuration['num_threads_per_memtier']
                    temp_df = pd.DataFrame.from_dict(MiddlewareAnalyzer.get_datapoint(log_dir, total_clients))
                    temp_df['workload'] = workload_str
                    temp_df['num_middlewares'] = num_middlewares
                    temp_df['num_memcached_servers'] = num_memcached_servers
                    temp_df['num_workers'] = num_threads_per_mw
                    dfs.append(temp_df)
        df = pd.concat(dfs)
        return df

    def print_latex_table(self, df, caption, lines=True):
        print('\\begin{table}[H]')
        print('\\centering')
        headers = list(df)

        if lines:
            tabular_def = 'c'.join(["|"]*(len(headers) + 1))
        else:
            tabular_def = 'c|' + 'c'*(len(headers) - 2) + '|c'
        print('\\begin{tabular}{' + tabular_def + '}')

        print('\\hline {}\\\\'.format(' & '.join(headers)))

        for _, row in df.iterrows():
            values = []
            for value in row.values:
                if type(value) == str:
                    values.append(value)
                elif float(value).is_integer():
                    values.append(str(int(value)))
                else:
                    values.append('{:.2f}'.format(value))
            print('\\hline {}\\\\'.format(' & '.join(values)))

        print('\\end{tabular}')
        print('\\caption{' + caption + '}')
        print('\\end{table}')
        print('%')

    def translate_factors(self, df):
        new_df = pd.DataFrame()
        for header in list(df):
            new_header = self.header_translations[header]
            if new_header in self.factor_translations:
                new_df[new_header] = df[header].apply(lambda x: self.factor_translations[new_header][str(x)])
            else:
                new_df[new_header] = df[header]

        new_df['idx'] = range(len(new_df))
        return new_df.set_index('idx')

    def extend_factors(self, df, target):
        new_df = pd.DataFrame()
        new_df['I'] = pd.Series([1] * len(df))
        factors = list(self.factors.keys())
        new_df[factors] = df[factors]

        new_df[factors[0] + "*" + factors[1]] = df[factors[0]]*df[factors[1]]
        new_df[factors[0] + "*" + factors[2]] = df[factors[0]]*df[factors[2]]
        new_df[factors[1] + "*" + factors[2]] = df[factors[1]]*df[factors[2]]
        new_df[factors[0] + "*" + factors[1] + "*" + factors[2]] = df[factors[0]]*df[factors[1]]*df[factors[2]]

        factors.extend([
            factors[0] + "*" + factors[1],
            factors[0] + "*" + factors[2],
            factors[1] + "*" + factors[2],
            factors[0] + "*" + factors[1] + "*" + factors[2]
        ])

        factors = ['I'] + factors

        new_df[target] = df[target]

        aggregations = {}

        totals = [np.inner(new_df[factor], new_df[target]) for factor in factors]
        totals_8 = [x / 8 for x in totals]
        ss = [(np.power(x, 2)) * 8 for x in totals_8[1:]]
        sst = sum(ss)
        allocations = [np.round((x / sst) * 100, 2) for x in [sst] + ss]

        for idx, factor in enumerate(factors):
            if factor not in aggregations:
                aggregations[factor] = []

            aggregations[factor].extend([
                totals[idx],
                totals_8[idx],
                "{}\%".format(allocations[idx])
            ])

        aggregations[target] = ['Total', 'Total/8', 'Variation']
        aggregations['idx'] = list(range(len(new_df), len(new_df)+3))

        return pd.concat([new_df, pd.DataFrame.from_dict(aggregations).set_index('idx')])

    def generate_sign_table(self, workload):
        targets = ['avg_get_tp_s', 'avg_get_rt_ms'] if workload == '0-1' else ['avg_set_tp_s', 'avg_set_rt_ms']
        select_list = ['num_middlewares', 'num_memcached_servers', 'num_workers'] + targets
        relevant_df = self.df[(self.df.workload == workload)][select_list]

        translated_df = self.translate_factors(relevant_df)

        caption = 'Read-Only Workload' if workload == '0-1' else 'Write-Only Workload'

        self.print_latex_table(translated_df, caption)

        for target in targets:
            caption = caption + ' Sign Table ' + self.header_translations[target]
            extended_df = self.extend_factors(translated_df, self.header_translations[target])
            self.print_latex_table(extended_df, caption, lines=False)
