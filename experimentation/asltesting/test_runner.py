class TestRunner(object):

    run_local = None

    def __init__(self, run_local):
        self.run_local = run_local

    def run_test(self, test_config):
        raise NotImplementedError