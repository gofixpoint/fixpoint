from fixpoint.workflows.node_state import WorkflowStatus
from fixpoint.workflows.imperative.workflow import Workflow


class TestNodeStates:
    def test_goto(self) -> None:
        wfrun = Workflow(id="test_workflow").run()

        # Default node state should be default __main__/__main__
        assert wfrun.current_node_info.id == "__main__/__main__"

        wfrun.goto_step("step_1")
        assert wfrun.current_node_info.id == "__main__/step_1"

        wfrun.goto_task("task_1")
        assert wfrun.current_node_info.id == "task_1/__main__"

        wfrun.goto_step("step_1")
        assert wfrun.current_node_info.id == "task_1/step_1"

    def test_call(self) -> None:
        wfrun = Workflow(id="test_workflow").run()

        # Default node state should be default __main__/__main__
        assert wfrun.current_node_info.id == "__main__/__main__"

        # Call a particular step
        step_handle = wfrun.call_step("step_1")
        assert wfrun.current_node_info.id == "__main__/step_1"

        step_handle.close(WorkflowStatus.COMPLETED)
        assert wfrun.current_node_info.id == "__main__/__main__"

        # Call a particular task
        task_handle = wfrun.call_task("task_1")
        assert wfrun.current_node_info.id == "task_1/__main__"

        task_handle.close(WorkflowStatus.COMPLETED)
        assert wfrun.current_node_info.id == "__main__/__main__"

        # The code below outlines undefined behavior when call_step is called multiple times before being closed
        # The code below is an example of an anti-pattern that should not be used
        step1_handle = wfrun.call_step("step_1")
        assert wfrun.current_node_info.id == "__main__/step_1"
        step2_handle = wfrun.call_step("step_2")
        assert wfrun.current_node_info.id == "__main__/step_2"

        # This will update the node state to the previous state of the step_1
        step1_handle.close(WorkflowStatus.COMPLETED)
        assert wfrun.current_node_info.id == "__main__/__main__"

        # After step_2 is closed, the node state will be updated to the previous state of the step_2 which is step_1
        step2_handle.close(WorkflowStatus.COMPLETED)
        assert wfrun.current_node_info.id == "__main__/step_1"

    def test_spawn(self) -> None:
        wfrun = Workflow(id="test_workflow").run()

        assert wfrun.current_node_info.id == "__main__/__main__"

        # Let's add a step outside a spawn group
        first_spawn = wfrun.spawn_step("step_0")

        # Current task id should stay the same
        assert wfrun.current_node_info.id == "__main__/__main__"

        with wfrun.spawn_group() as sg:
            sg.spawn_step("step_1")
            # Current node state did not change
            assert wfrun.current_node_info.id == "__main__/__main__"
            assert wfrun._node_state.next_states[1].info.id == "__main__/step_1"
            assert (
                wfrun._node_state.next_states[1].info.status == WorkflowStatus.RUNNING
            )
            assert wfrun._node_state.next_states[1].prev_state == wfrun._node_state

            sg.spawn_step("step_2")
            # Current node state did not change
            assert wfrun.current_node_info.id == "__main__/__main__"
            assert wfrun._node_state.next_states[2].info.id == "__main__/step_2"
            assert (
                wfrun._node_state.next_states[2].info.status == WorkflowStatus.RUNNING
            )
            assert wfrun._node_state.next_states[2].prev_state == wfrun._node_state

            sg.spawn_task("task_1")
            # Current node state did not change
            assert wfrun.current_node_info.id == "__main__/__main__"
            assert wfrun._node_state.next_states[3].info.id == "task_1/__main__"
            assert (
                wfrun._node_state.next_states[3].info.status == WorkflowStatus.RUNNING
            )
            assert wfrun._node_state.next_states[3].prev_state == wfrun._node_state

        states = wfrun._node_state.next_states
        assert len(states) == 4
        assert states[0].info.status == WorkflowStatus.RUNNING
        assert states[1].info.status == WorkflowStatus.COMPLETED
        assert states[2].info.status == WorkflowStatus.COMPLETED
        assert states[3].info.status == WorkflowStatus.COMPLETED
        assert wfrun.current_node_info.id == "__main__/__main__"

        # Now when we close the first spawn should the first spawn's status be updated
        first_spawn.close(WorkflowStatus.COMPLETED)
        assert wfrun._node_state.next_states[0].info.status == WorkflowStatus.COMPLETED
        assert wfrun.current_node_info.id == "__main__/__main__"
