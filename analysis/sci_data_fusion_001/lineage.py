def independently_eligible(left: dict, right: dict) -> bool:
    return bool(left.get("eligible") and right.get("eligible") and
                left.get("lineage_id") != right.get("lineage_id") and
                left.get("correlation_group_id") != right.get("correlation_group_id") and
                not left.get("target_exposed") and not right.get("target_exposed") and
                not left.get("source_internal_validation") and not right.get("source_internal_validation"))

