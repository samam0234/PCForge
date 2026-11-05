"""사이트 하나의 목록이 필요할 때의 얇은 래퍼. 에이전트는 app.catalog.gather를 쓴다."""

from app.catalog import gather
from app.schemas import Product, Requirements


def search_site(site: str, query: str) -> list[Product]:
    requirements = Requirements(
        purpose=query or "게이밍",
        budget_krw=20_000_000,
        shop=site,
        condition="mixed",
    )
    return gather(requirements)[:12]
