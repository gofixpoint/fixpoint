from fixpoint.completions import ChatCompletion
from fixpoint.agents.mock import new_mock_orig_completion
from tests.test_utils import SampleStructure


class TestCompletions:

    def test_fixpoint_completions(self) -> None:

        greeting_completion = new_mock_orig_completion(content="I'm doing good.")
        greeting_structure = SampleStructure("John")

        fixpoint_completion = ChatCompletion.from_original_completion(
            greeting_completion, greeting_structure
        )

        # Chat completion attributes should be accessed directly from the completion object
        assert fixpoint_completion.choices[0].message.content == "I'm doing good."

        # Structured output should be accessible on the .fixp attribute
        assert isinstance(fixpoint_completion.fixp, ChatCompletion.Fixp)
        assert isinstance(fixpoint_completion.fixp.structured_output, SampleStructure)
        assert fixpoint_completion.fixp.structured_output.name == "John"
