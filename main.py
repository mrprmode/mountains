import os
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Mountain(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    height: int
    local_name: str | None = Field(default=None, index=True)

db_user, db_pwd, db_host, db_name = os.getenv('DB_USER'), os.getenv('DB_PWD'), os.getenv('DB_HOST'), os.getenv('DB_NAME')
engine = create_engine(f"mysql+pymysql://{db_user}:{db_pwd}@{db_host}/{db_name}")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

# Production == DB Migration == SQLModel's migration utilities wrapping Alembic
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    mountain_1 = Mountain(name="Mt. Everest", height=29032, local_name="Sagarmatha")
    mountain_2 = Mountain(name="Mt. Annapurna", height=26545)
    mountain_3 = Mountain(name="Mt. Fishtail", height=22943, local_name="Machapuchare")
    mountain_4 = Mountain(name="Mt. McKinley", height=20310, local_name="Denali")
    mountain_5 = Mountain(name="Mt. Rainier", height=14410, local_name="Tahoma")
    with Session(engine) as session:
        # mountain = session.get(Mountain, 1)
        if not session.get(Mountain, 1):
            session.add(mountain_1)
            session.add(mountain_2)
            session.add(mountain_3)
            session.add(mountain_4)
            session.add(mountain_5)
            session.commit()

@app.get("/")
def read_mountains(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Mountain]:
    mountains = session.exec(select(Mountain).offset(offset).limit(limit)).all()
    return mountains


@app.get("/mountains/{mountain_id}")
def read_mountain(mountain_id: int, session: SessionDep) -> Mountain:
    mountain = session.get(Mountain, mountain_id)
    if not mountain:
        raise HTTPException(status_code=404, detail="Mountain not found")
    return mountain