from fastapi import APIRouter
from sqlmodel import col, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Niche, NichePublic

router = APIRouter(prefix="/niches", tags=["niches"])


@router.get("/", response_model=list[NichePublic])
def read_niches(
    *, session: SessionDep, _current_user: CurrentUser
) -> list[NichePublic]:
    statement = select(Niche).order_by(col(Niche.id))
    return [
        NichePublic(
            id=niche.id,
            slug=niche.slug,
            name=niche.name,
            description=niche.description,
        )
        for niche in session.exec(statement).all()
        if niche.id is not None
    ]
