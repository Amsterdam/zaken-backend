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
            if self.api.legacy_mode:
                time.sleep(0.15)
            elif hasattr(step, "asynchronous") and step.asynchronous:
                time.sleep(1)

            step.run(self.api, self.data)
