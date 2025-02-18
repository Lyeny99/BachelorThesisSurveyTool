import dataclasses


@dataclasses.dataclass
class Answer:
    question_id: str
    answer: str


@dataclasses.dataclass
class Result:
    participant_id: int
    survey_id: int
    answers: list[Answer]
