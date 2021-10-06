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
        steps = filter(lambda step: step is not None, steps)
        for step in steps:
            # Give Camunda and Spiff some time to do async processing
            time.sleep(0.05)

            step.run(self.api, self.data)
