from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import AudienceLevel, ClarityLevel, ContentFormat

Text = Annotated[str, Field(min_length=1)]
Title = Annotated[str, Field(min_length=1, max_length=255)]
Minutes = Annotated[int, Field(ge=1, le=600)]
KeyConcepts = Annotated[list[Text], Field(min_length=1, max_length=10)]
Prerequisites = Annotated[list[Text], Field(max_length=10)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TutorialSection(StrictModel):
    title: Text
    body: Text  # Markdown


class TutorialContent(StrictModel):
    summary: Text
    sections: list[TutorialSection] = Field(min_length=1, max_length=8)
    takeaways: list[Text] = Field(min_length=1, max_length=5)


class Flashcard(StrictModel):
    front: Text
    back: Text
    hint: Text | None = None


class FlashcardsContent(StrictModel):
    introduction: Text
    cards: list[Flashcard] = Field(min_length=8, max_length=12)


class QuizQuestion(StrictModel):
    prompt: Text
    options: list[Text] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation: Text

    @field_validator("options")
    @classmethod
    def options_are_unique(cls, options: list[str]) -> list[str]:
        if len(set(options)) != len(options):
            raise ValueError("As opções não podem se repetir.")
        return options


class QuizContent(StrictModel):
    questions: list[QuizQuestion] = Field(min_length=5, max_length=5)


class GeneratedBase(StrictModel):
    title: Title
    estimated_minutes: Minutes
    key_concepts: KeyConcepts
    prerequisites: Prerequisites


class GeneratedTutorial(GeneratedBase):
    content: TutorialContent


class GeneratedFlashcards(GeneratedBase):
    content: FlashcardsContent


class GeneratedQuiz(GeneratedBase):
    content: QuizContent


CONTENT_MODELS: dict[ContentFormat, type[BaseModel]] = {
    ContentFormat.tutorial: TutorialContent,
    ContentFormat.flashcards: FlashcardsContent,
    ContentFormat.quiz: QuizContent,
}

GENERATED_MODELS: dict[ContentFormat, type[GeneratedBase]] = {
    ContentFormat.tutorial: GeneratedTutorial,
    ContentFormat.flashcards: GeneratedFlashcards,
    ContentFormat.quiz: GeneratedQuiz,
}


def parse_content(content_format: ContentFormat, data: dict[str, Any]) -> BaseModel:
    return CONTENT_MODELS[content_format].model_validate(data)


class ContentPackage(StrictModel):
    format: ContentFormat
    audience_level: AudienceLevel
    niche: Text  # niche.slug
    title: Title
    content: dict[str, Any]
    estimated_minutes: Minutes
    key_concepts: KeyConcepts
    prerequisites: Prerequisites
    grounding_score: float = Field(ge=0, le=1)
    clarity: ClarityLevel
    review_notes: Text
