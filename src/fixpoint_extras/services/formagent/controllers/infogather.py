"""A controller that gathers info in order to fill out a form."""

from typing import Any, Dict, List, Type, Generic, TypeVar, Optional

from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo

from fixpoint.utils.messages import umsg
from fixpoint.completions import ChatCompletionMessageParam, ChatCompletion
from fixpoint.agents import BaseAgent


_QUESTION_FIELD_PREFIX = "question_"
_QUESTION_FIELD_PREFIX_LEN = len(_QUESTION_FIELD_PREFIX)


T = TypeVar("T", bound=BaseModel)


class InfoGatherer(Generic[T]):
    """A controller that gathers info in order to fill out a form."""

    agent: BaseAgent
    info_model: Type[T]
    info: T
    # A history of all info objects, including the latest. AKA,
    # `self.info_history[-1] == self.info`
    info_history: List[T]
    _questions: Dict[str, str]

    def __init__(self, info_model: Type[T], agent: BaseAgent):
        self.agent = agent
        self.info = info_model()
        self.info_model = info_model
        self.info_history = [self.info]
        self._questions = self.make_field_questions()

    def _make_questions_model(self) -> Type[BaseModel]:
        # type-checking the `create_model` is weird, so just ignore it
        new_fields: Dict[str, Any] = {}
        for k, v in self.info_model.model_fields.items():
            new_fields[f"{_QUESTION_FIELD_PREFIX}{k}"] = (
                str,
                Field(description=f"Question for: {v.description}"),
            )

        # We want to use a class-style variable name here, which Pylint normally
        # complains about.
        # pylint: disable=invalid-name
        InfoGathererQuestions: Type[BaseModel] = create_model(
            "InfoGathererQuestions", **new_fields
        )
        return InfoGathererQuestions

    def make_field_questions(self, agent: Optional[BaseAgent] = None) -> Dict[str, str]:
        """Make a question for every info field.

        The info fields are often not formatted as questions. This generates a
        list of questions, one for every info field.
        """
        if not agent:
            agent = self.agent
        questions_model = self._make_questions_model()
        field_descs = "\n".join(
            [
                # Ideally every field should have a description. If it's
                # missing, just use the field name.
                (v.description if v.description else k)
                for k, v in self.info_model.model_fields.items()
            ]
        )
        prompt = (
            "Below are a series of form field descriptions, one per line.\n"
            "\n"
            f"{field_descs}\n"
            "\n"
            "For each form field, write a short question that asks a person for the "
            'field\'s value. Do not prefix each question with "Question:" or '
            "anything similar."
        )
        cmpl = agent.create_completion(
            messages=[umsg(prompt)], response_model=questions_model
        )
        sout = cmpl.fixp.structured_output
        if sout is None:
            raise ValueError("No structured output found in completion")

        out_dict = sout.model_dump()
        # every question key was prefixed with "question_". Remove that prefix
        return {k[_QUESTION_FIELD_PREFIX_LEN:]: v for k, v in out_dict.items()}

    def missing_fields(self) -> Dict[str, FieldInfo]:
        """Get the fields that do not yet have answers."""
        missing: Dict[str, FieldInfo] = {}
        for k, v in self.info.model_dump().items():
            if v is None:
                missing[k] = self.info_model.model_fields[k]
        return missing

    def is_complete(self) -> bool:
        """True if all form info has been filled in."""
        missing = self.missing_fields()
        return len(missing) == 0

    def process_messages(
        self,
        messages: List[ChatCompletionMessageParam],
        agent: Optional[BaseAgent] = None,
    ) -> ChatCompletion[T]:
        """Process a user's message and update the form info."""
        if not agent:
            agent = self.agent
        old_info = self.info
        completion = agent.create_completion(
            messages=messages, response_model=self.info_model
        )

        # get the non-None fields from the old info and the new info
        old_info_dict = _get_non_none_dict(old_info)
        if completion.fixp.structured_output is None:
            raise ValueError("No structured output found in completion")
        new_info_dict = _get_non_none_dict(completion.fixp.structured_output)

        # TODO(dbmikus) add a way to merge old and new fields when they are both
        # set [PRO-15]

        # Only copy over fields not set on the new info
        for k in old_info_dict.keys():
            if new_info_dict.get(k, None) is None:
                new_info_dict[k] = old_info_dict[k]

        self.info = self.info_model(**new_info_dict)
        self.info_history.append(self.info)
        completion.fixp.structured_output = self.info
        return completion

    def format_questions(
        self,
        info: Optional[T] = None,
    ) -> str:
        """Format the questions for the missing fields.

        Format the questions for the missing fields, which can be passed to a
        human or to another agent.
        """
        if info is None:
            info = self.info
        missing = self.missing_fields()

        # get the questions for the missing fields
        questions = "\n".join([f"- {self._questions[k]}" for k in missing.keys()])

        return "We're still missing some info. Can you tell us:\n\n" f"{questions}"


def _get_non_none_dict(info: BaseModel) -> Dict[str, Any]:
    return {k: v for k, v in info.model_dump().items() if v is not None}
