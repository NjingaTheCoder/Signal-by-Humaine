from fastapi import Response


def cache_headers(response: Response, max_age: int = 300) -> None:
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
