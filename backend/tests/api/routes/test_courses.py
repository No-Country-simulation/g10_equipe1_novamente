import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import ContentCitation, CourseContent
from tests.utils.course import create_course
from tests.utils.user import authentication_token_from_email, create_random_user


def test_read_courses_empty_for_new_user(client: TestClient, db: Session) -> None:
    user = create_random_user(db)
    headers = authentication_token_from_email(client=client, email=user.email, db=db)

    response = client.get(
        f"{settings.API_V1_STR}/courses/",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {"data": [], "count": 0}


def test_read_courses_returns_only_owned_courses_newest_first(
    client: TestClient, db: Session
) -> None:
    owner = create_random_user(db)
    other_user = create_random_user(db)
    owner_headers = authentication_token_from_email(
        client=client, email=owner.email, db=db
    )
    create_course(client=client, owner_email=owner.email, title="Curso antigo")
    create_course(client=client, owner_email=owner.email, title="Curso novo")
    create_course(client=client, owner_email=other_user.email, title="Outro curso")

    response = client.get(
        f"{settings.API_V1_STR}/courses/",
        headers=owner_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert {course["title"] for course in data["data"]} == {
        "Curso antigo",
        "Curso novo",
    }
    assert [course["created_at"] for course in data["data"]] == sorted(
        (course["created_at"] for course in data["data"]),
        reverse=True,
    )
    assert data["data"][0]["contents"][0]["title"] == "Tutorial de teste"
    assert "niche" in data["data"][0]


def test_read_course_returns_documents_contents_and_citations(
    client: TestClient, db: Session
) -> None:
    user = create_random_user(db)
    headers = authentication_token_from_email(client=client, email=user.email, db=db)
    course = create_course(
        client=client,
        owner_email=user.email,
        documents=[
            {
                "original_filename": "primeiro.md",
                "chunks": ["primeiro trecho"],
            },
            {
                "original_filename": "segundo.md",
                "chunks": ["segundo trecho"],
            },
        ],
        contents=[
            {
                "format": "tutorial",
                "title": "Tutorial principal",
                "content": {"body": "Conteúdo principal"},
                "cited_chunks": [0, 1],
            },
            {"format": "quiz", "title": "Quiz", "content": {}, "cited_chunks": [0, 1]},
            {
                "format": "flashcards",
                "title": "Flashcards",
                "content": {},
                "cited_chunks": [0, 1],
            },
        ],
    )
    # A ordem esperada difere da ordem de criação e de inserção das citações.
    for index, seeded_content in enumerate(course["contents"]):
        content_id = uuid.UUID(seeded_content["id"])
        content = db.get(CourseContent, content_id)
        assert content is not None
        content.position = [2, 0, 1][index]
        db.add(content)
        citations = db.exec(
            select(ContentCitation).where(ContentCitation.content_id == content_id)
        ).all()
        for citation in citations:
            first_chunk = seeded_content["citations"][0]["chunk_id"]
            citation.similarity = (
                Decimal("0.2")
                if str(citation.chunk_id) == first_chunk
                else Decimal("0.8")
            )
            db.add(citation)
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/courses/{course['id']}",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert {document["original_filename"] for document in data["documents"]} == {
        "primeiro.md",
        "segundo.md",
    }
    assert [content["position"] for content in data["contents"]] == [0, 1, 2]
    assert [content["title"] for content in data["contents"]] == [
        "Quiz",
        "Flashcards",
        "Tutorial principal",
    ]
    for content in data["contents"]:
        assert [citation["similarity"] for citation in content["citations"]] == [
            0.8,
            0.2,
        ]
        assert {
            (citation["document_title"], citation["text"])
            for citation in content["citations"]
        } == {
            ("primeiro.md", "primeiro trecho"),
            ("segundo.md", "segundo trecho"),
        }


def test_read_course_returns_404_for_other_user_and_missing_course(
    client: TestClient, db: Session
) -> None:
    owner = create_random_user(db)
    other_user = create_random_user(db)
    course = create_course(client=client, owner_email=owner.email)
    other_headers = authentication_token_from_email(
        client=client, email=other_user.email, db=db
    )

    other_response = client.get(
        f"{settings.API_V1_STR}/courses/{course['id']}",
        headers=other_headers,
    )
    missing_response = client.get(
        f"{settings.API_V1_STR}/courses/00000000-0000-0000-0000-000000000000",
        headers=other_headers,
    )

    assert other_response.status_code == 404
    assert other_response.json()["detail"] == "Curso não encontrado."
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Curso não encontrado."


def test_read_courses_requires_authentication(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/courses/")

    assert response.status_code in (401, 403)
