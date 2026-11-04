"""사이트 검색 도구. 현재는 목업이며, 실제 상품·가격이 아니다.

실제 연동(Phase 4) 시 각 사이트의 이용약관과 robots 기준을 지키고 요청량을 제한한다.
"""

from app.schemas import Product

_MOCK_PRODUCTS = [
    Product(product_name="[목업] 라이젠 5 7500F", category="CPU", price=230000, site="다나와", specs={"socket": "AM5"}),
    Product(product_name="[목업] B650 메인보드", category="Mainboard", price=180000, site="컴퓨존", specs={"socket": "AM5", "memory": "DDR5"}),
    Product(product_name="[목업] DDR5 32GB", category="RAM", price=130000, site="11번가", specs={"memory": "DDR5"}),
    Product(product_name="[목업] RTX 4060", category="GPU", price=420000, site="쿠팡", specs={"tdp_w": "115"}),
    Product(product_name="[목업] 중고 RTX 4060", category="GPU", price=300000, site="번개장터", specs={"tdp_w": "115"}, is_used=True),
    Product(product_name="[목업] 중고 RTX 3060", category="GPU", price=200000, site="중고나라", specs={"tdp_w": "170"}, is_used=True),
]


def search_site(site: str, query: str) -> list[Product]:
    """해당 사이트의 목업 상품을 돌려준다. query는 실제 검색 구현 전까지 사용하지 않는다."""
    return [product for product in _MOCK_PRODUCTS if product.site == site]
