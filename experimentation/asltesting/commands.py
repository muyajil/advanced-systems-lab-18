from asltesting import paths

# TODO: Commands to archive logs
# TODO: Stop memcached

class CommandManager(object):

    def __init__(self, local):
        self.local = local

    def get_memcached_run_command(self, server_id):
        if self.local:
            return "docker-compose -f {} run -d memcached_{}".format(paths.MEMCACHED_YML, server_id)
        else:
            return "sudo service memcached start"

    def get_memcached_stop_command(self, server_id):
        if self.local:
            raise NotImplementedError
            #return "docker-compose -f {} stop ".format(paths.MEMCACHED_YML, server_id)
        else:
            return "sudo service memcached stop"

    def get_memtier_run_command(self, server_id, ):
        raise NotImplementedError

    def get_middleware_run_command(self, server_id, sharded):
        if self.local:
            if sharded:
                return "ant -f {} runSharded{}".format(paths.BUILD_XML, server_id)
            else:
                return "ant -f {} run{}".format(paths.BUILD_XML, server_id)
        else:
            raise NotImplementedError