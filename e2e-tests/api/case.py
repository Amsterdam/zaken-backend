import time


class Case:
    """
    Technically different then workflow engine user-tasks. Create case is needed
    to trigger the first task in the workflow.
    """

    timeline = []

    def __init__(self, data, client, events):
        self.data = data
        self.client = client
        self.timeline = events

    def run_steps(self, steps):
        steps = filter(lambda step: step is not None, steps)

        for step in steps:
            # Give Spiff some time to do async processing.
            # Sleep _before_ running a task because this could be the first
            # task after creating the case (which is not a step in itself).
            if step.is_async():
                print("Sleeping ....")
                time.sleep(2)

            step.run(self.client, self)
