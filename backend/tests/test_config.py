from app.config import Settings


def test_bare_postgres_scheme_rewritten_to_psycopg3():
    s = Settings(database_url="postgres://user:pass@host:5432/railway")
    assert s.database_url == "postgresql+psycopg://user:pass@host:5432/railway"


def test_bare_postgresql_scheme_rewritten_to_psycopg3():
    s = Settings(database_url="postgresql://user:pass@host:5432/railway")
    assert s.database_url == "postgresql+psycopg://user:pass@host:5432/railway"


def test_already_psycopg3_scheme_left_unchanged():
    url = "postgresql+psycopg://user:pass@host:5432/railway"
    s = Settings(database_url=url)
    assert s.database_url == url
