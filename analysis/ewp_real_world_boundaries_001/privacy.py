from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GroupDisposition:
    privacy_threshold_passes: bool
    privacy_suppressed: bool
    semantic_unresolved_unpublished: bool
    published: bool
    reason: str


def classify_group(shots: int, linked_contributors: int, semantic_authority_resolved: bool,
                   minimum_shots: int = 20, minimum_users: int = 10) -> GroupDisposition:
    privacy_pass = shots >= minimum_shots and linked_contributors >= minimum_users
    if not privacy_pass:
        return GroupDisposition(False, True, False, False, "DISCLOSURE_THRESHOLD_NOT_MET")
    if not semantic_authority_resolved:
        return GroupDisposition(True, False, True, False, "SEMANTIC_TRANSFER_AUTHORITY_UNRESOLVED")
    return GroupDisposition(True, False, False, True, "PUBLISHED")
