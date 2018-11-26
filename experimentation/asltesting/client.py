from abc import ABC, abstractmethod
import subprocess
import time
import paramiko
from io import StringIO
from concurrent.futures import TimeoutError
import shlex


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

    @abstractmethod
    def get_output(self):
        pass

    @abstractmethod
    def terminate(self):
        pass


class BashClient(Client):

    def __init__(self):
        super().__init__()
        self.p = None
        pass

    def exec_and_wait(self, command):
        stdout = subprocess.check_output(command, shell=True).decode('utf-8')
        return stdout

    def exec_and_forget(self, command):
        self.p = subprocess.Popen(shlex.split(command), shell=False, stdout=subprocess.PIPE)

    def terminate(self):
        if self.p is not None:
            self.p.terminate()

    def get_output(self):
        if self.p is None:
            raise RuntimeError("This is only supported for clients with previously executed 'exec_and_forget'")
        else:
            stdout, stderr = self.p.communicate()
            return stdout.decode('utf-8')

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
            raise RuntimeError('Received non-zero exit status\nCommand: {}\nError: {}'.format(command, stderr.read().decode('utf-8')))
        else:
            return stdout.read().decode('utf-8')

    def exec_and_forget(self, command):
        _, stdout, stderr = self.client.exec_command(command)
        time.sleep(1)
        if stdout.channel.exit_status_ready():
            stdout.channel.close()
            exit_status = stdout.channel.recv_exit_status()

            if exit_status != 0:
                raise RuntimeError('Received non-zero exit status\nCommand: {}\nError: {}'.format(command, stderr.read().decode('utf-8')))

    def get_internal_ip(self):
        _, stdout, _ = self.client.exec_command("""sh -c 'ifconfig eth0 | grep "inet addr" | cut -d ":" -f 2 | cut -d " " -f 1'""")
        ip = stdout.readlines()[0].rstrip()
        return ip

    def terminate(self):
        raise NotImplementedError

    def get_output(self):
        raise NotImplementedError
