from asltesting.client_manager import ClientManager


class Installer(object):

    def __init__(self):
        self.client_manager = ClientManager(False)
