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
        self.current_config = 0
        self.num_configs = None

    def run_test(self, run_configuration, base_log_dir):
        try:
            self.num_configs = len(run_configuration['workloads']) * \
                               len(run_configuration['num_threads_per_mw_range']) * \
                               len(run_configuration['num_clients_per_thread_range']) * \
                               self.num_runs

            print('////////////////////////////////////////////////////////////////')
            print('Running new experiment {}'.format(run_configuration['name']))

            print('\tBuilding middleware...')
            for middleware_id in range(1, run_configuration['num_middlewares'] + 1):
                output = self.client_manager.exec(self.command_manager.get_middleware_build_command(), 'middleware',
                                                  middleware_id, wait=True)
                # print(output)

            print('\tStarting memcached servers...')
            for memcached_id in range(1, run_configuration['num_memcached_servers'] + 1):
                command = self.command_manager.get_memcached_run_command(memcached_id)
                self.client_manager.exec(command=command, server_type='memcached', server_id=memcached_id, wait=True)

            for run in range(self.num_runs):
                print('################################################################')
                print('\tStarting iteration {}...'.format(run))
                self.run_single_test(run, run_configuration, base_log_dir)
                if not self.local:
                    self.gather_logs()

            print('\tStopping memcached...')
            for memcached_id in range(1, run_configuration['num_memcached_servers'] + 1):
                command = self.command_manager.get_memcached_stop_command()
                self.client_manager.exec(command=command, server_type='memcached', server_id=memcached_id, wait=True)

        finally:

            # STOP MIDDLEWARE
            for middleware_id in range(1, run_configuration['num_middlewares'] + 1):
                self.client_manager.terminate('middleware', middleware_id)

            # STOP MEMCACHED
            for memcached_id in range(1, run_configuration['num_memcached_servers'] + 1):
                command = self.command_manager.get_memcached_stop_command()
                self.client_manager.exec(command=command, server_type='memcached', server_id=memcached_id, wait=True)

    def run_single_test(self, iteration, run_configuration, base_log_dir):

        for workload in run_configuration['workloads']:
            for num_threads_per_mw in run_configuration['num_threads_per_mw_range']:
                for num_clients_per_thread in run_configuration['num_clients_per_thread_range']:
                    self.current_config += 1
                    print('----------------------------------------------------------------')
                    print(
                        "\t\tRunning configuration {}/{}:\n\t\t\tThreads per MW:\t\t{}\n\t\t\tClients per Thread:\t{}\n\t\t\tWorkload:\t\t\t{}\n".format(
                            self.current_config,
                            self.num_configs,
                            num_threads_per_mw,
                            num_clients_per_thread,
                            ':'.join(map(lambda x: str(x), workload))
                        ))

                    middleware_log_dir, memtier_log_dir = self.setup_log_dirs(
                        os.path.join(base_log_dir,
                                     *[
                                         str(num_threads_per_mw),
                                         str(num_clients_per_thread),
                                         '-'.join(map(lambda x: str(x), workload)),
                                         str(iteration)
                                     ]))

                    if run_configuration['num_middlewares'] > 0:
                        print('\t\tStarting middleware servers...')
                        for middleware_id in range(1, run_configuration['num_middlewares'] + 1):
                            command = self.command_manager.get_middleware_run_command(
                                sharded=run_configuration['sharded'],
                                num_threads=num_threads_per_mw,
                                log_dir=middleware_log_dir,
                                middleware_server_id=middleware_id,
                                num_servers=run_configuration['num_memcached_servers'])
                            self.client_manager.exec(command=command, server_type='middleware', server_id=middleware_id)

                        time.sleep(5)

                    print('\t\tStarting memtier...')
                    for memtier_id in range(1, run_configuration['num_client_machines'] + 1):

                        if run_configuration['num_middlewares'] > 0:

                            for middleware_id in range(1, run_configuration['num_middlewares'] + 1):
                                command = self.command_manager.get_memtier_run_command(
                                    middleware_server_id=middleware_id,
                                    threads=run_configuration['num_threads_per_memtier'],
                                    clients_per_thread=num_clients_per_thread,
                                    workload=':'.join(map(lambda x: str(x), workload)),
                                    multi_get_key_size=workload[1],
                                    memtier_server_id=memtier_id,
                                    log_dir=memtier_log_dir)

                                self.client_manager.exec(command, 'memtier', memtier_id)

                        else:

                            for memcached_id in range(1, run_configuration['num_memcached_servers'] + 1):
                                command = self.command_manager.get_memtier_run_command(
                                    memcached_server_id=memcached_id,
                                    threads=run_configuration['num_threads_per_memtier'],
                                    clients_per_thread=num_clients_per_thread,
                                    workload=':'.join(map(lambda x: str(x), workload)),
                                    multi_get_key_size=workload[1],
                                    memtier_server_id=memtier_id,
                                    log_dir=memtier_log_dir)
                                self.client_manager.exec(command, 'memtier', memtier_id)

                    print('\t\tWaiting for memtier...')
                    for memtier_id in range(1, run_configuration['num_client_machines'] + 1):
                        output = self.client_manager.get_output('memtier', memtier_id)
                        # print(output)

                    print('\t\tStopping middleware...')
                    for middleware_id in range(1, run_configuration['num_middlewares'] + 1):
                        self.client_manager.terminate('middleware', middleware_id)
                        output = self.client_manager.get_output('middleware', middleware_id)
                        # print(output)

    def setup_log_dirs(self, test_log_dir):
        middleware_log_dir = os.path.join(test_log_dir, 'middleware')
        memtier_log_dir = os.path.join(test_log_dir, 'memtier')

        if not os.path.exists(test_log_dir):
            os.makedirs(test_log_dir)

        if not os.path.exists(middleware_log_dir):
            os.makedirs(middleware_log_dir)

        if not os.path.exists(memtier_log_dir):
            os.makedirs(memtier_log_dir)

        return middleware_log_dir, memtier_log_dir

    def gather_logs(self):
        raise NotImplementedError
