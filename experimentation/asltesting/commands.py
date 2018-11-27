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
                                internal_ip_middleware=None):
        if self.local:
            base_command = "docker run --rm -v {0}:/output --net host memtier_benchmark -s 127.0.0.1 -P memcache_text -c {1} -t {2} --test-time 60 --data-size 4096 --key-maximum=10000 --expiry-range=9999-10000 --ratio {3} --multi-key-get={4} --out-file=/output/{5}.log --client-stats=/output/{5}_clients ".format(
                log_dir,
                clients_per_thread,
                threads,
                workload,
                multi_get_key_size,
                memtier_server_id)

            if middleware_server_id is not None:

                return base_command + "-p 808{}".format(middleware_server_id)
            else:
                return base_command + "-p 1121{}".format(memcached_server_id)
        else:
            raise NotImplementedError

    def get_middleware_run_command(self, middleware_server_id, sharded, num_threads, log_dir, num_servers):
        if self.local:
            servers = ""
            for server_id in range(1, num_servers+1):
                servers += "127.0.0.1:1121{}".format(server_id)
        else:
            raise NotImplementedError

        return "java -jar {} -l 0.0.0.0 -p 8081 -t {} -s {} -m {} -o {}".format(paths.Absolute.JAR_FILE, num_threads, sharded, servers, os.path.join(log_dir, str(middleware_server_id) + '.log'))

    @staticmethod
    def get_middleware_build_command():
        return "ant -f {} jar".format(paths.Absolute.BUILD_XML)

    @staticmethod
    def get_middleware_stop_command():
        return "if pgrep -f middleware-ajilm.jar; then pkill -SIGTERM -f middleware-ajilm.jar; fi"
