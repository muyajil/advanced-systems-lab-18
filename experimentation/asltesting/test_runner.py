from asltesting.client_manager import ClientManager
from asltesting.commands import CommandManager
import os
import time


class TestRunner(object):

    def __init__(self, num_runs, local):
        self.client_manager = ClientManager(local)
        self.command_manager = CommandManager(local)
        self.local = local
        self.num_runs = num_runs

    def run_test(self, run_configuration, base_log_dir):
        for middleware_id in range(1, run_configuration['num_middlewares'] + 1):
            output = self.client_manager.exec(self.command_manager.get_middleware_build_command(), 'middleware', middleware_id, wait=True)
            print(output)
        for run in range(self.num_runs):
            self.run_single_test(run, run_configuration, base_log_dir)
            if not self.local:
                self.gather_logs()

    def run_single_test(self, iteration, run_configuration, base_log_dir):
        try:
            for memcached_id in range(1, run_configuration['num_memcached_servers']+1):
                command = self.command_manager.get_memcached_run_command(memcached_id)
                self.client_manager.exec(command=command, server_type='memcached', server_id=memcached_id, wait=True)

            for num_threads_per_mw in run_configuration['num_threads_per_mw_range']:
                for num_clients_per_thread in run_configuration['num_clients_per_thread_range']:
                    for multi_get_size in run_configuration['multi_get_size_range']:
                        for workload in run_configuration['workloads']:

                            for middleware_id in range(1, run_configuration['num_middlewares']+1):
                                command = self.command_manager.get_middleware_run_command(sharded=run_configuration['sharded'],
                                                                                          num_threads=num_threads_per_mw,
                                                                                          log_dir=os.path.join(base_log_dir, *[str(iteration), 'middleware']), # TODO: include whole config in path, create log dir if not exists
                                                                                          middleware_server_id=middleware_id,
                                                                                          num_servers=run_configuration['num_memcached_servers'])
                                self.client_manager.exec(command=command, server_type='middleware', server_id=middleware_id)

                            time.sleep(10)

                            for memtier_id in range(1, run_configuration['num_client_machines']+1):
                                for middleware_id in range(1, run_configuration['num_middlewares'] + 1):
                                    command = self.command_manager.get_memtier_run_command(middleware_server_id=middleware_id,
                                                                                           threads=run_configuration['num_threads_per_memtier'],
                                                                                           clients_per_thread=num_clients_per_thread,
                                                                                           workload=':'.join(workload),
                                                                                           multi_get_key_size=multi_get_size,
                                                                                           memtier_server_id=memtier_id,
                                                                                           log_dir=os.path.join(base_log_dir, *[str(iteration), 'memtier'])) # TODO: include whole config in path, create log dir if not exists
                                    self.client_manager.exec(command, 'memtier', memtier_id)

                            for middleware_id in range(1, run_configuration['num_middlewares']+1):
                                command = self.command_manager.get_middleware_stop_command()
                                self.client_manager.exec(command, 'middleware', middleware_id)

        finally:
            for memcached_id in range(1, run_configuration['num_memcached_servers']+1):
                command = self.command_manager.get_memcached_stop_command()
                self.client_manager.exec(command=command, server_type='memcached', server_id=memcached_id, wait=True)

            for middleware_id in range(1, run_configuration['num_middlewares'] + 1):
                command = self.command_manager.get_middleware_stop_command()
                self.client_manager.exec(command, 'middleware', middleware_id, wait=True)


    def gather_logs(self):
        raise NotImplementedError