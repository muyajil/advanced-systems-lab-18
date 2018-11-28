from asltesting import paths
import os


class CommandManager(object):

    def __init__(self, local):
        self.local = local

    def get_memcached_run_command(self, server_id):
        if self.local:
            return "docker-compose -f {} up -d memcached_{}".format(paths.Absolute.MEMCACHED_YML, server_id)
        else:
            return "sudo service memcached start"

    def get_memcached_stop_command(self):
        if self.local:
            return "docker-compose -f {} down".format(paths.Absolute.MEMCACHED_YML)
        else:
            return "sudo service memcached stop"

    def get_memtier_run_command(self,
                                memtier_server_id,
                                threads,
                                clients_per_thread,
                                workload,
                                log_dir,
                                multi_get_key_size=1,
                                middleware_server_id=None,
                                memcached_server_id=None,
                                internal_ip_middleware=None,
                                internal_ip_memcached=None):

        if self.local:
            command_prefix = "docker run --rm -v {}:/output --net host memtier_benchmark ".format(log_dir)
        else:
            command_prefix = "memtier_benchmark"

        command_options = "-P memcache_text -c {0} -t {1} --test-time 60 --data-size 4096 --key-maximum=10000 --expiry-range=9999-10000 --ratio {2} --out-file=/output/{3}.log --client-stats=/output/{3}_{4}_clients ".format(
                clients_per_thread,
                threads,
                workload,
                memtier_server_id,
                middleware_server_id if middleware_server_id is not None else memcached_server_id)

        if self.local:

            command_options += "-s 127.0.0.1 "

            if middleware_server_id is not None:
                command_options += "-p 808{} ".format(middleware_server_id)
            else:
                command_options += "-p 1121{} ".format(memcached_server_id)

            if multi_get_key_size > 0:
                command_options += "--multi-key-get={}".format(multi_get_key_size)

            return command_prefix + command_options
        else:
            raise NotImplementedError

    def get_middleware_run_command(self, middleware_server_id, sharded, num_threads, log_dir, num_servers):
        if self.local:
            servers = ""
            for server_id in range(1, num_servers+1):
                servers += "127.0.0.1:1121{} ".format(server_id)
        else:
            raise NotImplementedError

        return "java -jar {} -l 0.0.0.0 -p 808{} -t {} -s {} -m {}-o {}".format(paths.Absolute.JAR_FILE, middleware_server_id, num_threads, sharded, servers, os.path.join(log_dir, str(middleware_server_id) + '.log'))

    @staticmethod
    def get_middleware_build_command():
        return "ant -f {} jar".format(paths.Absolute.BUILD_XML)

    @staticmethod
    def get_middleware_stop_command():
        return "if pgrep -f middleware-ajilm.jar; then pkill -SIGTERM -f middleware-ajilm.jar; fi"
