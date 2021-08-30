# -*- coding: utf-8

import os
import sys

from SpiffWorkflow import Task, Workflow
from SpiffWorkflow.specs import WorkflowSpec
from SpiffWorkflow.storage import XmlSerializer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lib"))


def on_entered_cb(workflow, task, taken_path):
    # print "entered:",task.get_name()
    return True


def on_ready_cb(workflow, task, taken_path):
    # print "ready:",task.get_name()
    return True


def on_reached_cb(workflow, task, taken_path):
    # print "reached:",task.get_name()
    return True


def on_complete_cb(workflow, task, taken_path):
    # Record the path.
    print("complete:", task.get_name())
    # print task.get_description()
    indent = "  " * (task._get_depth() - 1)
    taken_path.append("%s%s" % (indent, task.get_name()))
    return True


class QuestionError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class QuestionWorkflow(object):
    def __init__(self):
        self.serializer = XmlSerializer()

    def set_up(self, filename):
        # Test patterns that are defined in XML format.
        xml = open(filename).read()
        self.wf_spec = WorkflowSpec.deserialize(XmlSerializer(), xml, filename=filename)
        self.taken_path = self.track_workflow(self.wf_spec)
        self.workflow = Workflow(self.wf_spec)

    def run(self, UserSelection, restart=False):

        if restart:
            self.workflow = Workflow(self.wf_spec)

        workflow = self.workflow
        condition_keys = []
        if UserSelection is None:
            UserSelection = {}

        task_data_dict = UserSelection.copy()

        while not workflow.is_completed():
            tasks = workflow.get_tasks(Task.READY)

            for t in tasks:
                print("Ready:", t.task_spec.name)
                if hasattr(t.task_spec, "cond_task_specs"):
                    for cond, name in t.task_spec.cond_task_specs:
                        for cond_unit in cond.args:
                            if hasattr(cond_unit, "name"):
                                condition_keys.append(cond_unit.name)

            flag_keys_in_user_select = True
            for cond_key in condition_keys:
                if cond_key not in task_data_dict.keys():
                    print(cond_key)
                    flag_keys_in_user_select = False
                    break

            if not flag_keys_in_user_select:
                # some tast's condition's key not in input userselect dict
                return

            for t in tasks:
                t.set_data(**task_data_dict)

            workflow.complete_next()

        if not workflow.is_completed():
            raise QuestionError("invalid feature")

    def print_trace(self):
        path = "\n".join(self.taken_path) + "\n"
        info = ""
        info += "the workflowrun path:\n"
        info += "%s\n" % path
        print(info)

    def track_task(self, task_spec, taken_path):

        # reached event call back
        if task_spec.reached_event.is_connected(on_reached_cb):
            task_spec.reached_event.disconnect(on_reached_cb)
        task_spec.reached_event.connect(on_reached_cb, taken_path)

        # completed event call back
        if task_spec.completed_event.is_connected(on_complete_cb):
            task_spec.completed_event.disconnect(on_complete_cb)
        task_spec.completed_event.connect(on_complete_cb, taken_path)

        # enter event call back
        if task_spec.entered_event.is_connected(on_entered_cb):
            task_spec.entered_event.disconnect(on_entered_cb)
        task_spec.entered_event.connect(on_entered_cb, taken_path)

        # ready event call back
        if task_spec.ready_event.is_connected(on_ready_cb):
            task_spec.ready_event.disconnect(on_ready_cb)
        task_spec.ready_event.connect(on_ready_cb, taken_path)

    def track_workflow(self, wf_spec, taken_path=None):
        if taken_path is None:
            taken_path = []
        for name in wf_spec.task_specs:
            # print "track_workflow:",name
            self.track_task(wf_spec.task_specs[name], taken_path)
        return taken_path


if __name__ == "__main__":
    qw = QuestionWorkflow()
    qw.set_up("./case.xml")
    print("==========1st question==========")
    user_selct = {"man": "1"}
    qw.run(user_selct)
    print("==========2nd question==========")
    user_selct = {"man": "1", "house": "2"}
    qw.run(user_selct)
    print("==========3rd question==========")
    user_selct = {"man": "1", "house": "2", "why": "because you are a hero"}
    qw.run(user_selct)

    """
    print "==========4th question========="
    user_selct = {'man':'1', 'house': '2', 'role':'5'}
    qw.run(user_selct)
    """

    print("==========fix some question==========")
    user_selct = {"man": "1", "house": "1", "role": "5"}
    qw.run(user_selct, True)

    print
