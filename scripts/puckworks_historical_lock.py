"""Keep frozen R1/WP02 consumers on their source authority after runtime adoption."""
OLD_COMMIT = "fc61c4670ec7bf801e40bb391aab16048b8da26b"
OLD_TREE = "1d553e44ee2f7480a5df521560801b478618cc84"
E1_COMMIT = "ba35a3bf1f832cd651fe98eebd59860849c0e850"
RUNTIME_COMMIT = "dce84b22b99f114225eabb76f29014a5fc3efe5d"
E1_TREE = "a5e2362992ed8f6bd3a38a340b7624de310a642b"
RUNTIME_TREE = "20e9cd3898053820c7c6df4852991d8115f4d059"


def historical_lock(lock):
    """Explicit, exact legacy projection; arbitrary replacement pins still fail."""
    if (lock.get("checkout_commit"), lock.get("checkout_tree_sha")) in {(RUNTIME_COMMIT, RUNTIME_TREE), (E1_COMMIT, E1_TREE)}:
        expected = {"checkout_commit": OLD_COMMIT, "checkout_tree_sha": OLD_TREE}
        if lock.get("historical_runtime_identity") != expected:
            raise ValueError("historical Puckworks identity missing or changed")
        return dict(lock, **expected)
    return lock
