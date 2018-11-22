from asltesting.bash import BashClient
from asltesting import paths

example_run_config = {
    "name": "example_test_config",

    "num_memcached_servers": 1,

    "num_middlewares": 1,
    "num_threads_per_mw_range": [1],

    "num_client_machines": 1,
    "num_memtier_per_client": 1,
    "num_threads_per_memtier": 1,
    "num_clients_per_thread_range": [1],

    "sharded": False,
    "multi_get_size_range": [1],

    "workloads": [(1, 0)]
}


class LocalTestRunner(object):

    def __init__(self, num_runs):
        self.client = BashClient() # TODO one client per process -> then it is applicable to SSHClient as well!
        self.num_runs = num_runs

    def run_test(self, test_config):
        self.client.exec_and_wait('/bin/bash -c docker-compose -f {} up'.format(paths.MEMCACHED_YML))

        for run in range(self.num_runs):
            self.client.exec_and_forget('/bin/bash -c ant -f {} run1'.format(paths.BUILD_XML))
            if test_config.run_configuration['num_middlewares'] > 1:
                self.client.exec_and_forget('/bin/bash -c ant -f {} run1'.format(paths.BUILD_XML))

        self.client.exec_and_wait('/bin/bash -c docker-compose -f {} run {}'.format(test_config['memtier_yml_path'], test_config['memtier_target'])) # TODO: Need to parametrize the memtier command!

