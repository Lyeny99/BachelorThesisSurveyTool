import dataclasses


@dataclasses.dataclass
class Question:
    question_id: str
    question_text: str
    answer_type: str
    raw_text: str = ""
