from fixpoint.workflows.node_state import NodeState, CloseStatus
from fixpoint.workflows.imperative.workflow import Workflow


class TestNodeStates:
    def test_goto(self) -> None:
        wfrun = Workflow(id="test_workflow").run()

        # Default node state should be default __main__/__main__
        assert wfrun.current_task_id == "__main__/__main__"

        wfrun.goto_step("step_1")
        assert wfrun.current_task_id == "__main__/step_1"

        wfrun.goto_task("task_1")
        assert wfrun.current_task_id == "task_1/__main__"

        wfrun.goto_step("step_1")
        assert wfrun.current_task_id == "task_1/step_1"

    def test_call(self) -> None:
        wfrun = Workflow(id="test_workflow").run()

        # Default node state should be default __main__/__main__
        assert wfrun.current_task_id == "__main__/__main__"

        # Call a particular step
        step_handle = wfrun.call_step("step_1")
        assert wfrun.current_task_id == "__main__/step_1"

        step_handle.close(CloseStatus.COMPLETED)
        assert wfrun.current_task_id == "__main__/__main__"

        # Call a particular task
        task_handle = wfrun.call_task("task_1")
        assert wfrun.current_task_id == "task_1/__main__"

        task_handle.close(CloseStatus.COMPLETED)
        assert wfrun.current_task_id == "__main__/__main__"

        # Existing behavior when multiple call steps are opened befored being closed
        step1_handle = wfrun.call_step("step_1")
        assert wfrun.current_task_id == "__main__/step_1"
        step2_handle = wfrun.call_step("step_2")
        assert wfrun.current_task_id == "__main__/step_2"

        # This will update the node state to the previous state of the step_1
        step1_handle.close(CloseStatus.COMPLETED)
        assert wfrun.current_task_id == "__main__/__main__"

        # After step_2 is closed, the node state should be updated to the previous state of the step_2 which is step_1
        step2_handle.close(CloseStatus.COMPLETED)
        assert wfrun.current_task_id == "__main__/step_1"

    def test_spawn(self) -> None:
        wfrun = Workflow(id="test_workflow").run()

        assert wfrun.current_task_id == "__main__/__main__"

        # Let's add a step outside a spawn group
        first_spawn = wfrun.spawn_step("step_0")

        # Current task id should stay the same
        assert wfrun.current_task_id == "__main__/__main__"

        with wfrun.SpawnGroup() as sg:
            sg.spawn_step("step_1")
            # Current node state did not change
            assert wfrun.current_task_id == "__main__/__main__"
            assert wfrun.node_state.next_states[1].contents.id == "__main__/step_1"
            assert wfrun.node_state.next_states[1].contents.status is None
            assert wfrun.node_state.next_states[1].prev_state == wfrun.node_state

            sg.spawn_step("step_2")
            # Current node state did not change
            assert wfrun.current_task_id == "__main__/__main__"
            assert wfrun.node_state.next_states[2].contents.id == "__main__/step_2"
            assert wfrun.node_state.next_states[2].contents.status is None
            assert wfrun.node_state.next_states[2].prev_state == wfrun.node_state

            sg.spawn_task("task_1")
            # Current node state did not change
            assert wfrun.current_task_id == "__main__/__main__"
            assert wfrun.node_state.next_states[3].contents.id == "task_1/__main__"
            assert wfrun.node_state.next_states[3].contents.status is None
            assert wfrun.node_state.next_states[3].prev_state == wfrun.node_state

        states = wfrun.node_state.next_states
        assert len(states) == 4
        assert states[0].contents.status is None
        assert states[1].contents.status == CloseStatus.COMPLETED
        assert states[2].contents.status == CloseStatus.COMPLETED
        assert states[3].contents.status == CloseStatus.COMPLETED
        assert wfrun.current_task_id == "__main__/__main__"

        # Now when we close the first spawn should the first spawn's status be updated
        first_spawn.close(CloseStatus.COMPLETED)
        assert wfrun.node_state.next_states[0].contents.status == CloseStatus.COMPLETED
        assert wfrun.current_task_id == "__main__/__main__"
