import os
import json
from asltesting import paths


class TestConfiguration(object):

    base_dir = None
    log_dir = None
    plot_dir = None
    config = None
    name = None

    def __init__(self, name, run_id):

        self.base_dir = os.path.join(paths.Absolute.TESTS, name)
        self.config = json.load(open(os.path.join(self.base_dir, 'config.json')))
        self.plot_dir = os.path.join(self.base_dir, *[run_id, 'plots'])
        self.log_dir = os.path.join(self.base_dir, *[run_id, 'logs'])
        self.name = name
