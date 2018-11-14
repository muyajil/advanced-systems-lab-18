from asltesting.client import BashClient, SSHClient


class TestRunner(object):

    local = None
    client = None

    def __init__(self, local, ssh_config=None):
        self.local = local
        if self.local:
            self.client = BashClient()
        else:
            if ssh_config is None:
                raise RuntimeError('You need to pass ssh_config')
            self.client = SSHClient(ssh_config)

    def run_test(self, test_config):
        if self.local:
            self.run_local(test_config)
        else:
            self.run_remote(test_config)

    def run_local(self, test_config):
        self.client.exec_and_wait('/bin/bash -c docker-compose -f {} up'.format(test_config['memcached_yml_path']))
        if test_config['sharded']:
            self.client.exec_and_wait('/bin/bash -c ant -f {} runSharded'.format(test_config['build_xml_path'])) # TODO: Handle multiple middlewares
        else:
            self.client.exec_and_wait('/bin/bash -c ant -f {} run'.format(test_config['build_xml_path']))

        self.client.exec_and_wait('/bin/bash -c docker-compose -f {} run {}'.format(test_config['memtier_yml_path'], test_config['memtier_target'])) # TODO: Need to parametrize the memtier command!

    def run_remote(self, test_config):
        raise NotImplementedError
