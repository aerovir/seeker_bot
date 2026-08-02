"""
Tests for data catalogs — cities.yml, sources.yml, categories.yml.

Validates structure and cross-references so broken config doesn't break seeding.
"""

import yaml
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(name: str):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestCitiesCatalog:
    def test_cities_have_required_fields(self):
        """Each city has all required morphological fields and unique slug."""
        cities = _load("cities.yml")["cities"]
        required = [
            "slug", "name_ru", "name_en", "name_ru_prepositional",
            "name_ru_genitive", "region", "country", "timezone",
            "latitude", "longitude",
        ]
        assert len(cities) >= 15

        slugs = set()
        for c in cities:
            assert c["slug"] not in slugs, f"duplicate city slug {c['slug']}"
            slugs.add(c["slug"])
            for field in required:
                assert c.get(field), f"city {c['slug']} missing field {field}"

    def test_cities_cover_millionniks(self):
        """All Russian millionnik cities are present."""
        cities = {c["slug"] for c in _load("cities.yml")["cities"]}
        expected = {
            "moscow", "saint-petersburg", "kazan", "ekaterinburg",
            "novosibirsk", "krasnodar", "rostov-on-don", "samara",
            "chelyabinsk", "voronezh", "perm", "omsk", "ufa",
            "krasnoyarsk", "volgograd", "nizhny-novgorod",
        }
        missing = expected - cities
        assert not missing, f"missing cities: {missing}"


class TestSourcesCatalog:
    def test_source_default_cities_exist(self):
        """default_city_slug in sources.yml must reference an existing city."""
        sources = _load("sources.yml")["sources"]
        cities = {c["slug"] for c in _load("cities.yml")["cities"]}

        assert len(sources) >= 10
        slugs = set()
        for s in sources:
            assert s["slug"] not in slugs, f"duplicate source slug {s['slug']}"
            slugs.add(s["slug"])
            if "default_city_slug" in s:
                assert s["default_city_slug"] in cities, (
                    f"source {s['slug']} references unknown city "
                    f"{s['default_city_slug']}"
                )

    def test_sources_have_url_and_type(self):
        """Every source has a feed_url and a valid source_type."""
        sources = _load("sources.yml")["sources"]
        valid_types = {"rss", "api", "scrape"}
        for s in sources:
            assert s.get("feed_url"), f"source {s['slug']} has no feed_url"
            assert s["source_type"] in valid_types, (
                f"source {s['slug']} has invalid type {s['source_type']}"
            )
            assert s.get("priority") in (0, 1, 2)

    def test_sources_cover_main_cities(self):
        """Sources cover Moscow and other big cities via afisha."""
        sources = _load("sources.yml")["sources"]
        city_afisha = [
            s["slug"] for s in sources
            if "gorodskoyportal" in s["feed_url"]
        ]
        assert len(city_afisha) >= 8


class TestCategoriesCatalog:
    def test_categories_required_fields(self):
        """Each category has slug, name_ru, emoji and keywords."""
        cats = _load("categories.yml")["categories"]
        assert len(cats) >= 8

        slugs = set()
        for c in cats:
            assert c["slug"] not in slugs, f"duplicate category slug {c['slug']}"
            slugs.add(c["slug"])
            assert c["name_ru"], f"category {c['slug']} missing name_ru"
            assert c["emoji"], f"category {c['slug']} missing emoji"
            assert len(c["keywords"]) > 0, f"category {c['slug']} has no keywords"

    def test_new_categories_present(self):
        """kids and excursions categories are added."""
        slugs = {c["slug"] for c in _load("categories.yml")["categories"]}
        assert "kids" in slugs
        assert "excursions" in slugs
