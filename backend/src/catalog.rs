//! 카탈로그 JSON. 파일이 바뀌면 다음 조회에서 다시 읽는다.

use std::{
    collections::BTreeMap,
    fs,
    path::PathBuf,
    sync::{Arc, Mutex},
    time::SystemTime,
};

use serde::{Deserialize, Serialize};
use serde_json::{Value, json};

pub const MEMBER_ONLY: &[&str] = &["model", "material", "color", "noise"];
pub const GUEST_PAGE: usize = 48;
pub const MEMBER_PAGE: usize = 96;
pub const GUEST_SHORTLIST: usize = 30;
pub const MEMBER_SHORTLIST: usize = 120;
pub const GUEST_RECS: usize = 6;
pub const MEMBER_RECS: usize = 12;

const FACETS: &[&str] = &[
    "purpose",
    "condition",
    "category",
    "brand",
    "model",
    "material",
    "form_factor",
    "socket",
    "shop",
    "color",
    "noise",
    "power",
    "grade",
];

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CatalogItem {
    pub id: String,
    pub name: String,
    pub category: String,
    pub brand: String,
    pub model: String,
    pub material: String,
    pub form_factor: String,
    pub socket: String,
    pub condition: String,
    pub grade: String,
    pub color: String,
    pub shop: String,
    pub price: i64,
    pub noise: String,
    pub power: String,
    pub purposes: Vec<String>,
    pub summary: String,
    pub specs: BTreeMap<String, String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub url: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub image: Option<String>,
    #[serde(default = "reference_source")]
    pub source: String,
    #[serde(default = "reference_availability")]
    pub availability: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub fetched_at: String,
}

fn reference_source() -> String {
    "reference".to_string()
}

fn reference_availability() -> String {
    "reference".to_string()
}

fn closed(item: &CatalogItem) -> bool {
    matches!(
        item.availability.as_str(),
        "discontinued" | "sold" | "stopped" | "upcoming" | "unverified"
    )
}

#[derive(Clone, Debug, Deserialize)]
struct CatalogFile {
    snapshot: String,
    note: String,
    #[serde(default)]
    price_kind: String,
    products: Vec<CatalogItem>,
    #[serde(skip)]
    live_fetched_at: String,
    #[serde(skip)]
    live_count: usize,
}

#[derive(Debug, Deserialize)]
struct LiveFile {
    #[serde(default)]
    fetched_at: String,
    products: Vec<CatalogItem>,
}

struct Cache {
    modified: (SystemTime, Option<SystemTime>),
    data: Arc<CatalogFile>,
}

pub struct CatalogStore {
    path: PathBuf,
    live_path: PathBuf,
    cache: Mutex<Option<Cache>>,
}

#[derive(Debug, Default, Deserialize)]
pub struct CatalogQuery {
    #[serde(default)]
    pub part_name: String,
    #[serde(default)]
    pub purpose: String,
    pub price_max: Option<i64>,
    #[serde(default)]
    pub price_min: Option<i64>,
    #[serde(default)]
    pub condition: String,
    #[serde(default)]
    pub category: String,
    #[serde(default)]
    pub brand: String,
    #[serde(default)]
    pub model: String,
    #[serde(default)]
    pub material: String,
    #[serde(default)]
    pub form_factor: String,
    #[serde(default)]
    pub socket: String,
    #[serde(default)]
    pub shop: String,
    #[serde(default)]
    pub color: String,
    #[serde(default)]
    pub noise: String,
    #[serde(default)]
    pub power: String,
    #[serde(default)]
    pub grade: String,
    #[serde(default)]
    pub source: String,
    #[serde(default)]
    pub availability: String,
    pub offset: Option<i64>,
}

struct Criteria {
    part_name: String,
    purpose: String,
    price_max: Option<i64>,
    price_min: Option<i64>,
    condition: String,
    category: String,
    brand: String,
    model: String,
    material: String,
    form_factor: String,
    socket: String,
    shop: String,
    color: String,
    noise: String,
    power: String,
    grade: String,
    source: String,
    availability: String,
}

impl CatalogStore {
    pub fn open() -> Self {
        let dir = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../data/catalog");
        Self {
            path: dir.join("products.json"),
            live_path: dir.join("live.json"),
            cache: Mutex::new(None),
        }
    }

    fn data(&self) -> Result<Arc<CatalogFile>, String> {
        let base_modified = fs::metadata(&self.path)
            .and_then(|meta| meta.modified())
            .map_err(|err| err.to_string())?;
        let live_modified = fs::metadata(&self.live_path).and_then(|meta| meta.modified()).ok();
        let modified = (base_modified, live_modified);
        let mut guard = self.cache.lock().unwrap_or_else(|poison| poison.into_inner());
        if let Some(cache) = guard.as_ref() {
            if cache.modified == modified {
                return Ok(Arc::clone(&cache.data));
            }
        }
        let text = fs::read_to_string(&self.path).map_err(|err| err.to_string())?;
        let mut parsed: CatalogFile = serde_json::from_str(&text).map_err(|err| err.to_string())?;
        if live_modified.is_some() {
            match fs::read_to_string(&self.live_path)
                .map_err(|err| err.to_string())
                .and_then(|text| serde_json::from_str::<LiveFile>(&text).map_err(|err| err.to_string()))
            {
                Ok(live) => {
                    parsed.live_fetched_at = live.fetched_at;
                    parsed.live_count = live.products.len();
                    let mut merged = live.products;
                    merged.append(&mut parsed.products);
                    parsed.products = merged;
                }
                Err(err) => tracing::warn!("live.json을 읽지 못했습니다: {err}"),
            }
        }
        let data = Arc::new(parsed);
        *guard = Some(Cache {
            modified,
            data: Arc::clone(&data),
        });
        Ok(data)
    }

    pub fn query(&self, member: bool, query: &CatalogQuery) -> Result<Value, String> {
        let data = self.data()?;
        let criteria = criteria_from(query, member);
        let mut matched: Vec<&CatalogItem> = data
            .products
            .iter()
            .filter(|item| matches(item, &criteria, None))
            .collect();
        matched.sort_by(|left, right| {
            closed(left)
                .cmp(&closed(right))
                .then(category_rank(&left.category).cmp(&category_rank(&right.category)))
                .then(left.price.cmp(&right.price))
                .then(left.name.cmp(&right.name))
        });

        let limit = if member { MEMBER_PAGE } else { GUEST_PAGE };
        let offset = query.offset.unwrap_or(0).max(0) as usize;
        let page: Vec<&CatalogItem> = matched.iter().skip(offset).take(limit).copied().collect();
        let facets = facets_of(&data.products, &criteria);

        Ok(json!({
            "snapshot": data.snapshot,
            "note": data.note,
            "price_kind": data.price_kind,
            "live_fetched_at": data.live_fetched_at,
            "live_count": data.live_count,
            "tier": if member { "member" } else { "guest" },
            "total": matched.len(),
            "offset": offset,
            "limit": limit,
            "shortlist_limit": if member { MEMBER_SHORTLIST } else { GUEST_SHORTLIST },
            "recommend_limit": if member { MEMBER_RECS } else { GUEST_RECS },
            "locked_filters": if member { Vec::<&str>::new() } else { MEMBER_ONLY.to_vec() },
            "facets": facets,
            "items": page,
        }))
    }

    /// 카탈로그에 있고 판매가 끝나지 않은 id만 남긴다. 파일을 읽지 못하면 요청을 그대로 둔다.
    pub fn selling_ids(&self, ids: &[String]) -> Vec<String> {
        let Ok(data) = self.data() else {
            return ids.to_vec();
        };
        let mut index = BTreeMap::new();
        for item in &data.products {
            index.entry(item.id.as_str()).or_insert(item);
        }
        ids.iter()
            .filter(|id| index.get(id.as_str()).is_some_and(|item| !closed(item)))
            .cloned()
            .collect()
    }
}

fn category_rank(category: &str) -> u8 {
    match category {
        "CPU" => 0,
        "메인보드" => 1,
        "메모리" => 2,
        "GPU" => 3,
        "SSD" => 4,
        "파워" => 5,
        "케이스" => 6,
        "쿨러" => 7,
        "모니터" => 8,
        "키보드" => 9,
        "마우스" => 10,
        "HDD" => 11,
        "케이스팬" => 12,
        _ => 20,
    }
}

fn criteria_from(query: &CatalogQuery, member: bool) -> Criteria {
    Criteria {
        part_name: query.part_name.trim().to_lowercase(),
        purpose: query.purpose.trim().to_string(),
        price_max: query.price_max.filter(|price| *price > 0),
        price_min: query.price_min.filter(|price| *price > 0),
        condition: blank_unless(&query.condition, &["new", "used"]),
        category: query.category.trim().to_string(),
        brand: query.brand.trim().to_string(),
        model: if member { query.model.trim().to_string() } else { String::new() },
        material: if member { query.material.trim().to_string() } else { String::new() },
        form_factor: query.form_factor.trim().to_string(),
        socket: query.socket.trim().to_string(),
        shop: query.shop.trim().to_string(),
        color: if member { query.color.trim().to_string() } else { String::new() },
        noise: if member { query.noise.trim().to_string() } else { String::new() },
        power: query.power.trim().to_string(),
        grade: query.grade.trim().to_string(),
        source: blank_unless(&query.source, &["naver", "reference", "market"]),
        availability: blank_unless(
            &query.availability,
            &["selling", "sold", "discontinued", "stopped", "upcoming", "unverified"],
        ),
    }
}

fn blank_unless(value: &str, allowed: &[&str]) -> String {
    let value = value.trim();
    if allowed.contains(&value) { value.to_string() } else { String::new() }
}

fn matches(item: &CatalogItem, criteria: &Criteria, skip: Option<&str>) -> bool {
    if skip != Some("part_name") && !criteria.part_name.is_empty() && !contains_text(item, &criteria.part_name) {
        return false;
    }
    if skip != Some("purpose") && !criteria.purpose.is_empty() && !item.purposes.iter().any(|purpose| purpose == &criteria.purpose)
    {
        return false;
    }
    if skip != Some("price") {
        if let Some(max) = criteria.price_max {
            if item.price > max {
                return false;
            }
        }
        if let Some(min) = criteria.price_min {
            if item.price < min {
                return false;
            }
        }
    }
    eq(skip, "condition", &criteria.condition, &item.condition)
        && eq(skip, "category", &criteria.category, &item.category)
        && eq(skip, "brand", &criteria.brand, &item.brand)
        && eq(skip, "model", &criteria.model, &item.model)
        && eq(skip, "material", &criteria.material, &item.material)
        && eq(skip, "form_factor", &criteria.form_factor, &item.form_factor)
        && eq(skip, "socket", &criteria.socket, &item.socket)
        && eq(skip, "shop", &criteria.shop, &item.shop)
        && eq(skip, "color", &criteria.color, &item.color)
        && eq(skip, "noise", &criteria.noise, &item.noise)
        && eq(skip, "power", &criteria.power, &item.power)
        && eq(skip, "grade", &criteria.grade, &item.grade)
        && eq(skip, "source", &criteria.source, &item.source)
        && eq(skip, "availability", &criteria.availability, &item.availability)
}

fn eq(skip: Option<&str>, field: &str, expected: &str, actual: &str) -> bool {
    skip == Some(field) || expected.is_empty() || actual == expected
}

fn contains_text(item: &CatalogItem, needle: &str) -> bool {
    [item.name.as_str(), item.brand.as_str(), item.model.as_str(), item.material.as_str(), item.summary.as_str()]
        .iter()
        .any(|text| text.to_lowercase().contains(needle))
}

fn values<'a>(item: &'a CatalogItem, field: &str) -> Vec<&'a str> {
    match field {
        "category" => vec![item.category.as_str()],
        "brand" => vec![item.brand.as_str()],
        "model" => vec![item.model.as_str()],
        "material" => vec![item.material.as_str()],
        "form_factor" => vec![item.form_factor.as_str()],
        "socket" => vec![item.socket.as_str()],
        "shop" => vec![item.shop.as_str()],
        "color" => vec![item.color.as_str()],
        "noise" => vec![item.noise.as_str()],
        "power" => vec![item.power.as_str()],
        "grade" => vec![item.grade.as_str()],
        "condition" => vec![item.condition.as_str()],
        "purpose" => item.purposes.iter().map(String::as_str).collect(),
        _ => Vec::new(),
    }
}

fn facets_of(products: &[CatalogItem], criteria: &Criteria) -> Value {
    let mut facets = serde_json::Map::new();
    for field in FACETS {
        let mut counts: BTreeMap<&str, usize> = BTreeMap::new();
        for item in products.iter().filter(|item| matches(item, criteria, Some(field))) {
            for value in values(item, field) {
                if value.is_empty() || value == "없음" {
                    continue;
                }
                *counts.entry(value).or_default() += 1;
            }
        }
        let mut rows: Vec<(&str, usize)> = counts.into_iter().collect();
        rows.sort_by(|left, right| right.1.cmp(&left.1).then(left.0.cmp(right.0)));
        facets.insert(
            (*field).to_string(),
            json!(
                rows.into_iter()
                    .map(|(value, count)| json!({"value": value, "count": count}))
                    .collect::<Vec<_>>()
            ),
        );
    }
    Value::Object(facets)
}
