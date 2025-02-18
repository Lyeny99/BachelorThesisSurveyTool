from loguru import logger
import re
from typing import List
from sentence_transformers import SentenceTransformer, util


class DataPreparer:
    @staticmethod
    def prepare_surveys(survey_1, survey_2):
        """
        Matches questions and prepares data for analysis, including statistics computation.
        """
        logger.info("Preparing surveys for analysis.")
        question_matcher = QuestionMatcher()
        matched_pairs = question_matcher.match_questions(
            [q.question_text for q in survey_1.questions],
            [q.question_text for q in survey_2.questions],
        )

        logger.debug(f"Matched pairs: {matched_pairs}")
        # Compute statistics
        for pair in matched_pairs:
            try:
                logger.debug(f"Processing matched pair: {pair}")
                q1 = next(
                    q
                    for q in survey_1.questions
                    if q.question_text == pair["survey1_question"]
                )
                q2 = next(
                    q
                    for q in survey_2.questions
                    if q.question_text == pair["survey2_question"]
                )

                data1 = survey_1.get_data_by_question_id(q1.question_id)
                data2 = survey_2.get_data_by_question_id(q2.question_id)

                if len(data1) > 0 and len(data2) > 0:
                    avg1, sd1 = data1.mean(), data1.std()
                    avg2, sd2 = data2.mean(), data2.std()
                    survey_1.add_statistics(q1.question_id, avg1, sd1)
                    survey_2.add_statistics(q2.question_id, avg2, sd2)
                    logger.debug(
                        f"Computed statistics for pair {pair}: Survey1 AVG={avg1}, SD={sd1}; Survey2 AVG={avg2}, SD={sd2}"
                    )
                else:
                    logger.warning(f"Insufficient data for pair {pair}")

            except Exception as e:
                logger.error(
                    f"Error processing statistics for pair {pair}: {e}", exc_info=True
                )

        logger.info("Survey preparation completed.")
        return matched_pairs


class QuestionMatcher:
    def __init__(self, model_name="paraphrase-MiniLM-L6-v2"):
        logger.info(f"Initializing QuestionMatcher with model {model_name}")
        self.model = SentenceTransformer(model_name)

    def clean_text(self, text):
        """
        Returns text inside square brackets at the end of `text`, if present.

        Removes brackets and surrounding text, returning only content inside brackets at
        the end of `text`. If no brackets are found, returns `text` without surrounding whitespace.

        Example for Regex:
        "Some Question Group Title [Actual Question Text]"
        will be converted to
        "Actual Question Text"

        This should help with readability and shrink unnecessary content.

        Parameters:
            text (str): Input string.

        Returns:
            str: Content in brackets or cleaned original text.

        Note: actual question is inside braces
        """
        logger.debug(f"Cleaning text: {text}")
        match = re.search(r"\[(.*?)\]$", text)
        cleaned_text = match.group(1).strip() if match else text.strip()
        logger.debug(f"Cleaned text: {cleaned_text}")
        return cleaned_text

    def match_questions(
        self,
        survey1_questions: List[str],
        survey2_questions: List[str],
        threshold: float = 0.75,
    ):
        """
        Matches questions from two surveys based on semantic similarity.

        Encodes questions from `survey1_questions` and `survey2_questions` into embeddings, calculates
        cosine similarity scores, and finds the best match for each question in `survey1_questions`
        based on a given similarity `threshold`. Each question in `survey2_questions` can only be matched once.

        Parameters:
            survey1_questions (list of str): Questions from Survey 1.
            survey2_questions (list of str): Questions from Survey 2.
            threshold (float): Minimum similarity score to consider a match (default is 0.75).

        Returns:
            list of dict: Matched question pairs with:
                - "survey1_question" (str): Question from Survey 1.
                - "survey2_question" (str): Matched question from Survey 2.
                - "unified_label" (str): Combined label for similar questions.
        """
        logger.info("Matching questions between surveys.")
        embeddings1 = self.model.encode(survey1_questions, convert_to_tensor=True)
        embeddings2 = self.model.encode(survey2_questions, convert_to_tensor=True)

        cosine_scores = util.pytorch_cos_sim(embeddings1, embeddings2)
        matched_pairs = []

        used_indices = set()  # Track indices in survey2 already matched

        for i, score_row in enumerate(cosine_scores):
            max_score, best_match_idx = (
                score_row.max().item(),
                score_row.argmax().item(),
            )

            if max_score >= threshold and best_match_idx not in used_indices:
                question1 = survey1_questions[i]
                question2 = survey2_questions[best_match_idx]

                unified_label = (
                    question1
                    if question1 == question2
                    else f"{question1} / {question2}"
                )

                matched_pairs.append(
                    {
                        "survey1_question": question1,
                        "survey2_question": question2,
                        "unified_label": unified_label,
                    }
                )

                used_indices.add(best_match_idx)
                logger.debug(
                    f"Matched: Survey1 Question={question1}, Survey2 Question={question2}, Score={max_score}"
                )

        logger.info("Question matching completed.")
        return matched_pairs
