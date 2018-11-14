import subprocess
import paramiko
import time
from io import StringIO
from concurrent.futures import TimeoutError


def get_ssh_client(host, key, username):
    success = False
    ssh_client = paramiko.client.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    string_io = StringIO(key)
    private_key = paramiko.RSAKey.from_private_key(string_io)
    string_io.close()
    while not success:
        try:
            ssh_client.connect(host, pkey=private_key, username=username)
            success = True
        except (TimeoutError,
                paramiko.ssh_exception.NoValidConnectionsError,
                paramiko.ssh_exception.SSHException):
            time.sleep(1)
    return ssh_client


class Client(object):

    def exec_and_wait(self, command):
        raise NotImplementedError

    def exec_and_return_stdout(self, command):
        raise NotImplementedError

    def exec_and_forget(self, command):
        raise NotImplementedError


class SSHClient(Client):

    client = None

    def __init__(self, config):
        self.client = get_ssh_client(config['host'], config['key'], config['username'])

    def exec_and_wait(self, command):
        _, stdout, stderr = self.client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            raise RuntimeError('Received non-zero exit status\nCommand: \
            {}\nError: {}'.format(command, stderr.read().decode('utf-8')))

    def exec_and_return_stdout(self, command):
        _, stdout, stderr = self.client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            raise RuntimeError('Received non-zero exit status\nCommand: \
            {}\nError: {}'.format(command, stderr.read().decode('utf-8')))
        else:
            return stdout.read().decode('utf-8')

    def exec_and_forget(self, command):
        _, stdout, stderr = self.client.exec_command(command)
        time.sleep(5)
        if stdout.channel.exit_status_ready():
            stdout.channel.close()
            exit_status = stdout.channel.recv_exit_status()

            if exit_status != 0:
                raise RuntimeError('Received non-zero exit status\nCommand: \
                        {}\nError: {}'.format(command, stderr.read().decode('utf-8')))


class BashClient(Client):

    def exec_and_wait(self, command):
        raise NotImplementedError

    def exec_and_return_stdout(self, command):
        raise NotImplementedError

    def exec_and_forget(self, command):
        raise NotImplementedError
