from asltesting.client_manager import ClientManager

cmd_install = "sudo apt-get update && sudo apt-get install -y git unzip zip build-essential autoconf automake " \
                  "libpcre3-dev libevent-dev pkg-config zlib1g-dev software-properties-common htop && " \
                  "if [ ! -d logs ]; then mkdir logs; fi && " \
                  "if [ ! -d fill ]; then mkdir fill; fi "


class Installer(object):

    def __init__(self):
        self.client_manager = ClientManager(False)

    def execute_on_all_servers(self, server_type, command):
        for server_id in self.client_manager.server_config[server_type]:
            if int(server_id) < 4: # Simplest way to ignore the double memtiers
                print('-----------------------------------------------------------------')
                print('Setting up {} server {}'.format(server_type, server_id))
                output = self.client_manager.exec(command, server_type, server_id, wait=True)
                print(output)

    def set_private_key(self):
        for server_type in self.client_manager.server_config:
            for server_id in self.client_manager.server_config[server_type]:
                self.client_manager.set_private_key(server_type, server_id)

    def install_memtier(self):
        cmd_install_memtier = "if [ ! -d memtier_benchmark ]; then " \
                              "git clone https://github.com/RedisLabs/memtier_benchmark.git; fi && " \
                              "cd memtier_benchmark && autoreconf -ivf && ./configure && make && sudo make install"
        cmd = cmd_install + " && " + cmd_install_memtier

        self.execute_on_all_servers('memtier', cmd)

    def install_memcached(self):
        cmd_install_memcached = "sudo apt-get install -y memcached && " \
                                "sudo sed -i -- 's/127.0.0.1/0.0.0.0/g' /etc/memcached.conf"
        cmd = cmd_install + " && " + cmd_install_memcached

        self.execute_on_all_servers('memcached', cmd)

    def install_middleware(self):
        cmd_install_middleware = "sudo add-apt-repository ppa:openjdk-r/ppa -y && sudo apt-get update && " \
                                 "sudo apt-get install -y openjdk-8-jdk ant && " \
                                 "sudo grep -q -F \"JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-amd64/jre/\" " \
                                 "/etc/environment || echo \"JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-amd64/jre/\" | " \
                                 "sudo tee --append /etc/environment && " \
                                 "ssh-keyscan gitlab.ethz.ch > /home/ajilm/.ssh/known_hosts && " \
                                 "if [ ! -d asl18 ]; then " \
                                 "git clone git@gitlab.ethz.ch:ajilm/asl-fall18-project.git ~/asl18; fi"

        cmd = cmd_install + " && " + cmd_install_middleware

        self.execute_on_all_servers('middleware', cmd)
