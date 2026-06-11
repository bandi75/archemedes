from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CATALOG = Path(__file__).resolve().parents[3] / "data" / "azure_pricing.json"


@dataclass(slots=True)
class CostEstimate:
    assumptions: list[str]
    resource_sizing: list[dict[str, Any]]
    monthly_range: dict[str, float]
    annual_range: dict[str, float]
    major_cost_drivers: list[dict[str, Any]]
    cost_sensitivity: str
    warnings: list[str]
    missing_prices: list[dict[str, Any]]


def estimate_azure_cost(
    resources: list[dict[str, Any]],
    *,
    pricing_catalog_path: str | None = None,
    currency: str = "USD",
) -> CostEstimate:
    catalog = _load_catalog(pricing_catalog_path)

    assumptions = [
        "Pricing is indicative and based on local catalog snapshots.",
        "Hours per month defaults to 730 unless explicitly provided.",
        "Costs exclude taxes, support plans, and most data egress fees.",
    ]
    resource_sizing: list[dict[str, Any]] = []
    warnings: list[str] = []
    missing_prices: list[dict[str, Any]] = []

    expected_monthly = 0.0
    low_monthly = 0.0
    high_monthly = 0.0

    for resource in resources:
        service = str(resource.get("service", "")).strip()
        sku = str(resource.get("sku", "default")).strip() or "default"
        region = str(resource.get("region", "eastus")).strip() or "eastus"
        quantity = float(resource.get("quantity", 1.0))
        hours_per_month = float(resource.get("hours_per_month", 730.0))

        if not service:
            warnings.append("Resource entry missing service name and was skipped.")
            continue

        pricing = _lookup_price(catalog, service, sku, region)
        if pricing is None:
            missing_prices.append({"service": service, "sku": sku, "region": region})
            warnings.append(f"Price missing for {service}/{sku} in {region}.")
            continue

        unit_price = float(pricing["price_usd"])
        unit = pricing.get("unit", "per hour")

        monthly = unit_price * quantity
        if unit == "per hour":
            monthly *= hours_per_month

        expected_monthly += monthly
        low_monthly += monthly * 0.85
        high_monthly += monthly * 1.25

        resource_sizing.append(
            {
                "service": service,
                "sku": sku,
                "region": region,
                "quantity": quantity,
                "hours_per_month": hours_per_month,
                "unit": unit,
                "unit_price_usd": unit_price,
                "estimated_monthly_usd": round(monthly, 2),
            }
        )

    drivers = _top_drivers(resource_sizing)
    sensitivity = _sensitivity_label(resource_sizing)

    monthly_range = {
        "low": round(low_monthly, 2),
        "expected": round(expected_monthly, 2),
        "high": round(high_monthly, 2),
        "currency": currency,
    }
    annual_range = {
        "low": round(low_monthly * 12, 2),
        "expected": round(expected_monthly * 12, 2),
        "high": round(high_monthly * 12, 2),
        "currency": currency,
    }

    return CostEstimate(
        assumptions=assumptions,
        resource_sizing=resource_sizing,
        monthly_range=monthly_range,
        annual_range=annual_range,
        major_cost_drivers=drivers,
        cost_sensitivity=sensitivity,
        warnings=warnings,
        missing_prices=missing_prices,
    )


def _load_catalog(pricing_catalog_path: str | None) -> dict[str, Any]:
    path = Path(pricing_catalog_path) if pricing_catalog_path else DEFAULT_CATALOG
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _lookup_price(catalog: dict[str, Any], service: str, sku: str, region: str) -> dict[str, Any] | None:
    service_prices = catalog.get(service)
    if not service_prices:
        return None

    sku_prices = service_prices.get(sku)
    if not sku_prices:
        return None

    price_entry = sku_prices.get(region) or sku_prices.get("global")
    return price_entry


def _top_drivers(resource_sizing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not resource_sizing:
        return []
    total = sum(item["estimated_monthly_usd"] for item in resource_sizing)
    if total <= 0:
        return []

    sorted_items = sorted(resource_sizing, key=lambda item: item["estimated_monthly_usd"], reverse=True)
    top = []
    for item in sorted_items[:3]:
        pct = (item["estimated_monthly_usd"] / total) * 100.0
        top.append(
            {
                "service": item["service"],
                "percentage_of_total": round(pct, 2),
                "sensitivity": "high" if pct >= 35 else "medium" if pct >= 15 else "low",
                "notes": [f"{item['service']} contributes significant monthly cost share."],
            }
        )
    return top


def _sensitivity_label(resource_sizing: list[dict[str, Any]]) -> str:
    if not resource_sizing:
        return "low"
    if any(item["service"] in {"Event Hubs", "Cosmos DB", "AKS"} for item in resource_sizing):
        return "high"
    if len(resource_sizing) >= 4:
        return "medium"
    return "low"
