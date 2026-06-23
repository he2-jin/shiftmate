"""사용자-근무자 연결 서비스."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models.schedule_person import SchedulePerson
from app.db.models.user import User


def link_user_to_person(db: Session, user: User, person_id: int) -> SchedulePerson:
    """user_id를 SchedulePerson에 연결. 이미 다른 사용자가 연결했으면 409."""
    person = db.get(SchedulePerson, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="근무자를 찾을 수 없습니다.")

    if person.user_id is not None and person.user_id != user.id:
        raise HTTPException(status_code=409, detail="이미 다른 사용자가 연결된 근무자입니다.")

    person.user_id = user.id
    db.commit()
    db.refresh(person)
    return person
