import os
import json

class TestConfiguration(object):

    base_dir = None
    log_dir = None
    plot_dir = None
    config = None
    name = None

    def __init__(self, test_dir, name):

        self.base_dir = os.path.join(test_dir, name)
        self.config = json.load(open(os.path.join(self.base_dir, 'config.json')))
        self.plot_dir = os.path.join(self.base_dir, 'plots')
        self.log_dir = os.path.join(self.base_dir, 'logs')
        self.name = name
