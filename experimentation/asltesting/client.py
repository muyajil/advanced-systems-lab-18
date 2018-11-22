from abc import ABC, abstractmethod
import subprocess
import time
import paramiko
from io import StringIO
from concurrent.futures import TimeoutError


class Client(ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def exec_and_wait(self, command):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def exec_and_forget(self, command):
        pass


class BashClient(Client):

    def __init__(self):
        super().__init__()
        pass

    def exec_and_wait(self, command):
        stdout = subprocess.check_output(command)
        return stdout

    def exec_and_forget(self, command):
        subprocess.Popen(command)

    def close(self):
        pass


class SSHClient(Client):

    def __init__(self, host, key, username):
        self.client = self.get_ssh_client(host, key, username)
        super().__init__()

    @staticmethod
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

    def close(self):
        self.client.close()

    def exec_and_wait(self, command):
        _, stdout, stderr = self.client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            raise RuntimeError('Received non-zero exit status\nCommand: \
            {}\nError: {}'.format(command, stderr.read().decode('utf-8')))
        else:
            return stdout.read().decode('utf-8')

    def exec_and_forget(self, command):
        _, stdout, stderr = self.client.exec_command(command)
        time.sleep(1)
        if stdout.channel.exit_status_ready():
            stdout.channel.close()
            exit_status = stdout.channel.recv_exit_status()

            if exit_status != 0:
                raise RuntimeError('Received non-zero exit status\nCommand: \
                        {}\nError: {}'.format(command, stderr.read().decode('utf-8')))