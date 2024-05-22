import unittest

from fixpoint.completions import FixpointCompletion
from tests.test_utils import SampleCompletion, SampleStructure


class TestCompletions(unittest.TestCase):

    def test_fixpoint_completions(self) -> None:

        greeting_completion = SampleCompletion("Hello, how are you?", "I'm doing good.")
        greeting_structure = SampleStructure("John")

        fixpoint_completion = FixpointCompletion(
            greeting_completion, greeting_structure  # type: ignore
        )

        # Chat completion attributes should be accessed directly from the completion object
        self.assertEqual(fixpoint_completion.prompt, "Hello, how are you?")
        self.assertEqual(fixpoint_completion.output_message, "I'm doing good.")

        # Structured output should be accessible on the .fixp attribute
        self.assertIsInstance(fixpoint_completion.fixp, FixpointCompletion.Fixp)
        self.assertIsInstance(
            fixpoint_completion.fixp.structured_output, SampleStructure
        )
        self.assertEqual(fixpoint_completion.fixp.structured_output.name, "John")
