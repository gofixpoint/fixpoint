import unittest

from fixpoint.utils import decorate_instructor_completion_with_fixp
from fixpoint.completions import FixpointCompletion
from tests.test_utils import SampleCompletion, SampleStructure


class TestUtilsCompletions(unittest.TestCase):

    def test_instructor_completion_decorator(self) -> None:

        def instructed_chat_completion(
            prompt: str, response_type: SampleStructure
        ) -> tuple[SampleStructure, SampleCompletion]:
            completion = SampleCompletion(prompt, "I'm doing good.")
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

        # Chat completion response should be of type FixpointCompletion
        self.assertIsInstance(fixpoint_completion, FixpointCompletion)

        # Chat completion attributes should be accessed directly from the completion object
        self.assertEqual(fixpoint_completion.prompt, "Hello, how are you?")
        self.assertEqual(fixpoint_completion.output_message, "I'm doing good.")

        # Strucutred output should be accessible on the .fixp attribute
        self.assertIsInstance(fixpoint_completion.fixp, FixpointCompletion.Fixp)
        self.assertIsInstance(
            fixpoint_completion.fixp.structured_output, SampleStructure
        )
        self.assertEqual(fixpoint_completion.fixp.structured_output.name, "John")
