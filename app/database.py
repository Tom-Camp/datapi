from sqlmodel import Session, create_engine

SQLITE_URL = "sqlite:///./app.db"

engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


def get_db():
    with Session(engine) as session:
        yield session
