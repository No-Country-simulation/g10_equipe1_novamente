import copy
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from app.models import AudienceLevel, ClarityLevel, ContentFormat
from app.services.content_schemas import (
    CONTENT_MODELS,
    GENERATED_MODELS,
    ContentPackage,
    FlashcardsContent,
    QuizContent,
    TutorialContent,
    parse_content,
)


def tutorial() -> dict[str, Any]:
    return {
        "summary": "Uma VCN é a rede privada da sua empresa dentro da nuvem.",
        "sections": [
            {"title": "O que é uma VCN", "body": "Uma **VCN** é uma rede virtual..."}
        ],
        "takeaways": ["A VCN isola os seus recursos."],
    }


def card(index: int = 0) -> dict[str, Any]:
    return {
        "front": f"O que é uma VCN? ({index})",
        "back": "Uma rede virtual privada.",
        "hint": "Pense em um terreno cercado.",
    }


def flashcards(cards: int = 8) -> dict[str, Any]:
    return {
        "introduction": "Cartões sobre os conceitos de rede da OCI.",
        "cards": [card(i) for i in range(cards)],
    }


def question() -> dict[str, Any]:
    return {
        "prompt": "Qual recurso controla o tráfego de entrada?",
        "options": ["Security List", "Bucket", "Compartment", "Tenancy"],
        "correct_index": 0,
        "explanation": "A Security List define as regras de entrada e de saída.",
    }


def quiz(questions: int = 5) -> dict[str, Any]:
    return {"questions": [question() for _ in range(questions)]}


EXAMPLES = {
    ContentFormat.tutorial: tutorial,
    ContentFormat.flashcards: flashcards,
    ContentFormat.quiz: quiz,
}


def generated(content_format: ContentFormat) -> dict[str, Any]:
    return {
        "title": "Redes na OCI",
        "estimated_minutes": 15,
        "key_concepts": ["VCN"],
        "prerequisites": [],
        "content": EXAMPLES[content_format](),
    }


def package() -> dict[str, Any]:
    return {
        "format": "tutorial",
        "audience_level": "technical_basic",
        "niche": "fintech",
        "title": "Redes na OCI",
        "content": tutorial(),
        "estimated_minutes": 15,
        "key_concepts": ["VCN", "Subnet"],
        "prerequisites": ["Noções de rede"],
        "grounding_score": 0.92,
        "clarity": "high",
        "review_notes": "Fiel ao documento.",
    }


def set_path(data: Any, path: tuple[str | int, ...], value: Any) -> None:
    for key in path[:-1]:
        data = data[key]
    data[path[-1]] = value


def test_maps_cover_every_format() -> None:
    assert set(CONTENT_MODELS) == set(ContentFormat)
    assert set(GENERATED_MODELS) == set(ContentFormat)


@pytest.mark.parametrize(
    "content_format,model",
    [
        (ContentFormat.tutorial, TutorialContent),
        (ContentFormat.flashcards, FlashcardsContent),
        (ContentFormat.quiz, QuizContent),
    ],
)
def test_parse_content_accepts_valid_example(
    content_format: ContentFormat, model: type[BaseModel]
) -> None:
    data = EXAMPLES[content_format]()

    parsed = parse_content(content_format, data)

    assert type(parsed) is model
    assert parsed.model_dump() == data


def test_parse_content_uses_the_model_of_the_format() -> None:
    with pytest.raises(ValidationError):
        parse_content(ContentFormat.quiz, tutorial())


@pytest.mark.parametrize("content_format", list(ContentFormat))
def test_generated_model_accepts_valid_answer(content_format: ContentFormat) -> None:
    data = generated(content_format)

    parsed = GENERATED_MODELS[content_format].model_validate(data)

    assert parsed.model_dump() == data


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", "a" * 256),
        ("estimated_minutes", 0),
        ("estimated_minutes", 601),
        ("key_concepts", []),
        ("key_concepts", ["c"] * 11),
        ("prerequisites", ["p"] * 11),
        ("content", flashcards()),
    ],
)
def test_generated_model_rejects_out_of_range(field: str, value: Any) -> None:
    data = generated(ContentFormat.tutorial)
    data[field] = value

    with pytest.raises(ValidationError):
        GENERATED_MODELS[ContentFormat.tutorial].model_validate(data)


@pytest.mark.parametrize(
    "cards,valid", [(7, False), (8, True), (12, True), (13, False)]
)
def test_flashcards_card_count(cards: int, valid: bool) -> None:
    data = flashcards(cards)

    if valid:
        parse_content(ContentFormat.flashcards, data)
    else:
        with pytest.raises(ValidationError):
            parse_content(ContentFormat.flashcards, data)


@pytest.mark.parametrize("questions", [4, 6])
def test_quiz_rejects_wrong_question_count(questions: int) -> None:
    with pytest.raises(ValidationError):
        parse_content(ContentFormat.quiz, quiz(questions))


@pytest.mark.parametrize(
    "field,value",
    [
        ("options", ["Security List", "Bucket", "Compartment"]),
        ("options", ["Security List", "Bucket", "Compartment", "Tenancy", "VCN"]),
        ("options", ["Security List", "Bucket", "Bucket", "Tenancy"]),
        ("options", ["Security List", "Bucket", " Bucket ", "Tenancy"]),
        ("correct_index", 4),
        ("correct_index", -1),
    ],
)
def test_quiz_rejects_invalid_question(field: str, value: Any) -> None:
    data = quiz()
    data["questions"][0][field] = value

    with pytest.raises(ValidationError):
        parse_content(ContentFormat.quiz, data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("sections", []),
        ("sections", [tutorial()["sections"][0]] * 9),
        ("takeaways", []),
        ("takeaways", ["t"] * 6),
    ],
)
def test_tutorial_rejects_wrong_counts(field: str, value: Any) -> None:
    data = tutorial()
    data[field] = value

    with pytest.raises(ValidationError):
        parse_content(ContentFormat.tutorial, data)


def test_tutorial_requires_takeaways() -> None:
    data = tutorial()
    del data["takeaways"]

    with pytest.raises(ValidationError):
        parse_content(ContentFormat.tutorial, data)


@pytest.mark.parametrize(
    "content_format,path",
    [
        (ContentFormat.tutorial, ("summary",)),
        (ContentFormat.tutorial, ("sections", 0, "title")),
        (ContentFormat.tutorial, ("sections", 0, "body")),
        (ContentFormat.tutorial, ("takeaways", 0)),
        (ContentFormat.flashcards, ("introduction",)),
        (ContentFormat.flashcards, ("cards", 0, "front")),
        (ContentFormat.flashcards, ("cards", 0, "back")),
        (ContentFormat.flashcards, ("cards", 0, "hint")),
        (ContentFormat.quiz, ("questions", 0, "prompt")),
        (ContentFormat.quiz, ("questions", 0, "options", 0)),
        (ContentFormat.quiz, ("questions", 0, "explanation")),
    ],
)
@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_content_rejects_blank_text(
    content_format: ContentFormat, path: tuple[str | int, ...], blank: str
) -> None:
    data = EXAMPLES[content_format]()
    set_path(data, path, blank)

    with pytest.raises(ValidationError):
        parse_content(content_format, data)


@pytest.mark.parametrize(
    "path", [("title",), ("key_concepts", 0), ("prerequisites", 0)]
)
def test_generated_model_rejects_blank_text(path: tuple[str | int, ...]) -> None:
    data = generated(ContentFormat.quiz)
    data["prerequisites"] = ["Noções de rede"]
    set_path(data, path, "  ")

    with pytest.raises(ValidationError):
        GENERATED_MODELS[ContentFormat.quiz].model_validate(data)


def test_text_is_stripped() -> None:
    data = tutorial()
    data["summary"] = "  Resumo.  "

    parsed = parse_content(ContentFormat.tutorial, data)

    assert isinstance(parsed, TutorialContent)
    assert parsed.summary == "Resumo."


@pytest.mark.parametrize(
    "content_format,path",
    [
        (ContentFormat.tutorial, ()),
        (ContentFormat.tutorial, ("sections", 0)),
        (ContentFormat.flashcards, ()),
        (ContentFormat.flashcards, ("cards", 0)),
        (ContentFormat.quiz, ()),
        (ContentFormat.quiz, ("questions", 0)),
    ],
)
def test_content_rejects_extra_field(
    content_format: ContentFormat, path: tuple[str | int, ...]
) -> None:
    data = EXAMPLES[content_format]()
    set_path(data, (*path, "extra"), "x")

    with pytest.raises(ValidationError):
        parse_content(content_format, data)


@pytest.mark.parametrize("content_format", list(ContentFormat))
def test_generated_model_rejects_extra_field(content_format: ContentFormat) -> None:
    data = generated(content_format)
    data["extra"] = "x"

    with pytest.raises(ValidationError):
        GENERATED_MODELS[content_format].model_validate(data)


def test_hint_is_optional() -> None:
    data = flashcards()
    del data["cards"][0]["hint"]
    data["cards"][1]["hint"] = None

    parsed = parse_content(ContentFormat.flashcards, data)

    assert isinstance(parsed, FlashcardsContent)
    assert parsed.cards[0].hint is None
    assert parsed.cards[1].hint is None


def test_content_package_round_trips_through_json() -> None:
    original = ContentPackage.model_validate(package())

    restored = ContentPackage.model_validate_json(original.model_dump_json())

    assert restored == original
    assert restored.format is ContentFormat.tutorial
    assert restored.audience_level is AudienceLevel.technical_basic
    assert restored.clarity is ClarityLevel.high
    assert restored.model_dump(mode="json") == package()


def test_content_package_has_exactly_the_eleven_keys() -> None:
    dumped = ContentPackage.model_validate(package()).model_dump(mode="json")

    assert list(dumped) == [
        "format",
        "audience_level",
        "niche",
        "title",
        "content",
        "estimated_minutes",
        "key_concepts",
        "prerequisites",
        "grounding_score",
        "clarity",
        "review_notes",
    ]


@pytest.mark.parametrize(
    "field,value",
    [
        ("extra", "x"),
        ("format", "resumo"),
        ("grounding_score", 1.01),
        ("grounding_score", -0.01),
        ("review_notes", " "),
        ("niche", ""),
        ("content", []),
    ],
)
def test_content_package_rejects_invalid_field(field: str, value: Any) -> None:
    data = copy.deepcopy(package())
    data[field] = value

    with pytest.raises(ValidationError):
        ContentPackage.model_validate(data)
