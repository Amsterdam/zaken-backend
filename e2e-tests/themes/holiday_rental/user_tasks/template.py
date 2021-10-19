from api.test import DefaultAPITest
from api.validators import ValidateNoOpenTasks


class TestClassName(DefaultAPITest):
    def test_function(self):
        """This docblock will be used by unittest"""
        self.case.run_steps(
            # *Start.get_steps(),
            # TestClass(),
            ValidateNoOpenTasks(),
        )

    def test_unimplemented(self):
        """This test will be skipped"""
        self.skipTest("Not implemented, check with Nicoline")  # TODO
