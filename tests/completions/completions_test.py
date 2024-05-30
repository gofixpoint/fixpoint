import json

from pydantic import BaseModel

from fixpoint.completions import ChatCompletion
from fixpoint.agents.mock import new_mock_orig_completion

from ..test_utils import SampleStructure


class TestChatCompletion:
    def test_fixpoint_completions(self) -> None:

        greeting_completion = new_mock_orig_completion(content="I'm doing good.")
        greeting_structure = SampleStructure(name="John")

        fixpoint_completion = ChatCompletion.from_original_completion(
            greeting_completion, greeting_structure
        )

        # Chat completion attributes should be accessed directly from the completion object
        assert fixpoint_completion.choices[0].message.content == "I'm doing good."

        # Structured output should be accessible on the .fixp attribute
        assert isinstance(fixpoint_completion.fixp, ChatCompletion.Fixp)
        assert isinstance(fixpoint_completion.fixp.structured_output, SampleStructure)
        assert fixpoint_completion.fixp.structured_output.name == "John"

    def test_model_serialization(self) -> None:
        orig_completion = new_mock_orig_completion()
        structured_out = ExampleStructuredOutput(name="Dylan", age=9000)
        completion = ChatCompletion.from_original_completion(
            orig_completion, structured_out
        )

        jsondata = completion.serialize_json()
        jsondict = json.loads(jsondata)
        assert jsondict["fixp"]["structured_output"] == {"name": "Dylan", "age": 9000}

        loaded_completion = ChatCompletion.deserialize_json(
            jsondata, ExampleStructuredOutput
        )

        assert loaded_completion.choices == completion.choices
        assert loaded_completion.fixp.structured_output == structured_out


class ExampleStructuredOutput(BaseModel):
    name: str
    age: int
