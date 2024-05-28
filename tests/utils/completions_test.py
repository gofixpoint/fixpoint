from openai.types.chat.chat_completion import ChatCompletion as OpenAIChatCompletion

from fixpoint._utils import decorate_instructor_completion_with_fixp
from fixpoint.completions import ChatCompletion
from fixpoint.agents.mock import new_mock_orig_completion
from tests.test_utils import SampleStructure


class TestUtilsCompletions:

    def test_instructor_completion_decorator(self) -> None:

        def instructed_chat_completion(
            _prompt: str, _response_type: SampleStructure
        ) -> tuple[SampleStructure, OpenAIChatCompletion]:
            completion = new_mock_orig_completion(content="I'm doing good.")
            structure = SampleStructure("John")

            # Return in order instructor expects them
            return structure, completion

        decorated_completion = decorate_instructor_completion_with_fixp(
            instructed_chat_completion
        )

        # Execute the chat completion
        fixpoint_completion = decorated_completion(
            "Hello, how are you?", SampleStructure
        )

        assert isinstance(fixpoint_completion, ChatCompletion)

        # Chat completion attributes should be accessed directly from the completion object
        assert fixpoint_completion.choices[0].message.content == "I'm doing good."

        # Strucutred output should be accessible on the .fixp attribute
        assert isinstance(fixpoint_completion.fixp, ChatCompletion.Fixp)
        assert isinstance(fixpoint_completion.fixp.structured_output, SampleStructure)
        assert fixpoint_completion.fixp.structured_output.name == "John"
