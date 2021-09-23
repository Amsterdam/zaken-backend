import time


class Case:
    """
    Technically different then workflow engine user-tasks. Create case is needed
    to trigger the first task in the workflow.
    """

    def __init__(self, data, api):
        self.data = data
        self.api = api

    def run_steps(self, steps):
        for step in steps:
            time.sleep(0.1)
            step.run(self.api, self.data)
