import json
from asltesting import paths
from asltesting.client import BashClient, SSHClient


class ClientManager(object):

    def __init__(self, local):
        self.local = local
        self.server_config = json.load(open(paths.Absolute.SERVER_CONFIG, 'r'))
        self.clients = {
            "memcached": {},
            "middleware": {},
            "memtier": {}
        }

    def init_connections(self, run_configuration):
        for server_id in range(1, run_configuration['num_memcached_servers'] + 1):
            self.clients['memcached'][server_id] = self.get_or_create_client('memcached', server_id)

        for server_id in range(1, run_configuration['num_middlewares'] + 1):
            self.clients['middleware'][server_id] = self.get_or_create_client('middleware', server_id)

        for server_id in range(1, run_configuration['num_client_machines'] + 1):
            self.clients['memtier'][server_id] = self.get_or_create_client('memtier', server_id)

    def create_client(self, server_type, server_id):
        if self.local:
            return BashClient()
        else:
            if type(server_id) is not str:
                server_id = str(server_id)
            return SSHClient(
                self.server_config[server_type][server_id],
                open(paths.Absolute.PRIVATE_KEY, 'r').read(),
                'ajilm')

    def get_or_create_client(self, server_type, server_id):
        server_id = str(server_id)

        if server_id not in self.clients[server_type] or self.clients[server_type][server_id] is None:
            self.clients[server_type][server_id] = self.create_client(server_type, server_id)

        return self.clients[server_type][server_id]

    def exec(self, command, server_type, server_id, wait=False, retry=False):
        try:
            client = self.get_or_create_client(server_type, server_id)
            if wait:
                return client.exec_and_wait(command)
            else:
                client.exec_and_forget(command)
        except Exception as e:
            if retry:
                raise e
            else:
                client = self.create_client(server_type, server_id)
                self.clients[server_type][server_id] = client

                self.exec(command, server_type, server_id, retry=True, wait=wait)

    def get_output(self, server_type, server_id):
        client = self.get_or_create_client(server_type, server_id)
        return client.get_output()

    def terminate(self, server_type, server_id):
        client = self.get_or_create_client(server_type, server_id)
        client.terminate()

    def close(self):
        for server_type in self.clients:
            for server_id in self.clients[server_type]:
                self.clients[server_type][server_id].close()

    def get_internal_ip(self, server_type, server_id):
        if self.local:
            return '127.0.0.1'
        else:
            client = self.get_or_create_client(server_type, server_id)
            return client.get_internal_ip()

    def set_private_key(self, server_type, server_id):
        client = self.get_or_create_client(server_type, server_id)
        client.set_private_key()

    def download_logs(self, server_type, server_id, log_dir):
        client = self.get_or_create_client(server_type, server_id)
        client.download_logs(log_dir)
