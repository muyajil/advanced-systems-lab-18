from asltesting.client_manager import ClientManager
from asltesting.commands import CommandManager
import os
import time
import datetime


class TestRunner(object):

    def __init__(self, num_runs, local):
        self.client_manager = ClientManager(local)
        self.command_manager = CommandManager(local)
        self.local = local
        self.num_runs = num_runs
        self.current_config = 0
        self.num_configs = None
        self.run_configuration = None
        self.init_time = time.time()

    def run_test(self, run_configuration, base_log_dir):
        try:
            self.run_configuration = run_configuration
            self.current_config = 0
            self.num_configs = len(run_configuration['workloads']) * \
                               len(run_configuration['num_threads_per_mw_range']) * \
                               len(run_configuration['num_clients_per_thread_range']) * \
                               self.num_runs

            print('////////////////////////////////////////////////////////////////')
            print('Running new experiment {}'.format(run_configuration['name']))

            self.build_middleware()

            self.start_memcached_servers()

            for run in range(self.num_runs):
                print('################################################################')
                print('\tStarting iteration {}...'.format(run))
                self.run_single_test(run, run_configuration, base_log_dir)
                if not self.local:
                    self.gather_logs()

            self.stop_memcached_servers()

        except Exception as e:
            self.stop_middleware()
            raise e
        finally:
            self.stop_memcached_servers()

    def run_single_test(self, iteration, run_configuration, base_log_dir):

        for workload in run_configuration['workloads']:
            for num_threads_per_mw in run_configuration['num_threads_per_mw_range']:
                for num_clients_per_thread in run_configuration['num_clients_per_thread_range']:
                    start = time.time()
                    self.current_config += 1
                    print('----------------------------------------------------------------')
                    print(
                        "\t\tRunning configuration {}/{}:\n\t\t\tThreads per MW:\t\t{}\n\t\t\tClients per Thread:\t{}\n\t\t\tWorkload:\t\t{}\n".format(
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
                        self.start_middleware(num_threads_per_mw, middleware_log_dir)

                        self.start_memtier_middleware(num_clients_per_thread, workload, memtier_log_dir)

                    else:
                        self.start_memtier_memcached(num_clients_per_thread, workload, memtier_log_dir)

                    self.wait_for_memtier()

                    self.stop_middleware()

                    print("\t\tTest took {} secs".format(int(time.time() - start)))
                    print("\t\tTotal running time so far: {:.2f}".format((int(time.time() - self.init_time)/3600)))

    @staticmethod
    def setup_log_dirs(test_log_dir):
        middleware_log_dir = os.path.join(test_log_dir, 'middleware')
        memtier_log_dir = os.path.join(test_log_dir, 'memtier')

        if not os.path.exists(test_log_dir):
            os.makedirs(test_log_dir)

        if not os.path.exists(middleware_log_dir):
            os.makedirs(middleware_log_dir)

        if not os.path.exists(memtier_log_dir):
            os.makedirs(memtier_log_dir)

        return middleware_log_dir, memtier_log_dir

    def build_middleware(self):
        print('\tBuilding middleware...')
        for middleware_id in range(1, self.run_configuration['num_middlewares'] + 1):
            output = self.client_manager.exec(self.command_manager.get_middleware_build_command(), 'middleware', middleware_id, wait=True)
            # print(output)

    def start_middleware(self, num_threads_per_mw, middleware_log_dir):
        print('\t\tStarting middleware...')
        for middleware_id in range(1, self.run_configuration['num_middlewares'] + 1):
            command = self.command_manager.get_middleware_run_command(
                sharded=self.run_configuration['sharded'],
                num_threads=num_threads_per_mw,
                log_dir=middleware_log_dir,
                middleware_server_id=middleware_id,
                num_servers=self.run_configuration['num_memcached_servers'])
            self.client_manager.exec(command=command, server_type='middleware', server_id=middleware_id)

        time.sleep(5)

    def stop_middleware(self):
        print('\t\tStopping middleware...')
        for middleware_id in range(1, self.run_configuration['num_middlewares'] + 1):
            self.client_manager.terminate('middleware', middleware_id)
            output = self.client_manager.get_output('middleware', middleware_id)
            # print(output)

    def start_memcached_servers(self):
        print('\tStarting memcached servers...')
        for memcached_id in range(1, self.run_configuration['num_memcached_servers'] + 1):
            command = self.command_manager.get_memcached_run_command(memcached_id)
            self.client_manager.exec(command=command, server_type='memcached', server_id=memcached_id, wait=True)

    def stop_memcached_servers(self):
        print('\tStopping memcached...')
        for memcached_id in range(1, self.run_configuration['num_memcached_servers'] + 1):
            command = self.command_manager.get_memcached_stop_command()
            self.client_manager.exec(command=command, server_type='memcached', server_id=memcached_id, wait=True)

    def start_memtier_middleware(self, num_clients_per_thread, workload, memtier_log_dir):
        print('\t\tStarting memtier...')
        for memtier_id in range(1, self.run_configuration['num_client_machines'] + 1):
            for middleware_id in range(1, self.run_configuration['num_middlewares'] + 1):
                command = self.command_manager.get_memtier_run_command(
                    middleware_server_id=middleware_id,
                    threads=self.run_configuration['num_threads_per_memtier'],
                    clients_per_thread=num_clients_per_thread,
                    workload=':'.join(map(lambda x: str(x), workload)),
                    multi_get_key_size=workload[1],
                    memtier_server_id=memtier_id,
                    log_dir=memtier_log_dir)

                self.client_manager.exec(command, 'memtier', memtier_id)

    def start_memtier_memcached(self, num_clients_per_thread, workload, memtier_log_dir):
        print('\t\tStarting memtier...')
        for memtier_id in range(1, self.run_configuration['num_client_machines'] + 1):
            for memcached_id in range(1, self.run_configuration['num_memcached_servers'] + 1):
                command = self.command_manager.get_memtier_run_command(
                    memcached_server_id=memcached_id,
                    threads=self.run_configuration['num_threads_per_memtier'],
                    clients_per_thread=num_clients_per_thread,
                    workload=':'.join(map(lambda x: str(x), workload)),
                    multi_get_key_size=workload[1],
                    memtier_server_id=memtier_id,
                    log_dir=memtier_log_dir)
                self.client_manager.exec(command, 'memtier', memtier_id)

    def wait_for_memtier(self):
        # TODO: if multiple commands on same machine we cant get the output
        print('\t\tWaiting for memtier...')
        for memtier_id in range(1, self.run_configuration['num_client_machines'] + 1):
            output = self.client_manager.get_output('memtier', memtier_id)
            lines = output.split('\n')
            performance_lines = lines[6].split('\r')
            print('\t\t' + performance_lines[-2])

    def gather_logs(self):
        raise NotImplementedError
