from fixpoint.completions import FixpointCompletion
from tests.test_utils import SampleCompletion, SampleStructure


class TestCompletions:

    def test_fixpoint_completions(self) -> None:

        greeting_completion = SampleCompletion("Hello, how are you?", "I'm doing good.")
        greeting_structure = SampleStructure("John")

        fixpoint_completion = FixpointCompletion(
            greeting_completion, greeting_structure  # type: ignore
        )

        # Chat completion attributes should be accessed directly from the completion object
        assert fixpoint_completion.prompt == "Hello, how are you?"
        assert fixpoint_completion.output_message == "I'm doing good."

        # Structured output should be accessible on the .fixp attribute
        assert isinstance(fixpoint_completion.fixp, FixpointCompletion.Fixp)
        assert isinstance(fixpoint_completion.fixp.structured_output, SampleStructure)
        assert fixpoint_completion.fixp.structured_output.name == "John"
