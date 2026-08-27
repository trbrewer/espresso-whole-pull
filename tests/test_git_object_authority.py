import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.git_object_authority import (
    AuthorityError, GitAuthority, changed_paths, object_bytes, verify_authority,
)


class GitObjectAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Test"], check=True)
        self.base = self._commit("allowed.txt", b"base\n", "base")
        self.candidate = self._commit("evidence.json", b"{}\n", "candidate")

    def _authority(self, commit):
        tree = subprocess.check_output(["git", "-C", str(self.repo), "rev-parse", f"{commit}^{{tree}}"], text=True).strip()
        return GitAuthority(commit, tree)

    def _commit(self, path, data, message):
        target = self.repo / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
        subprocess.run(["git", "-C", str(self.repo), "add", path], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-q", "-m", message], check=True)
        return subprocess.check_output(["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True).strip()

    def test_exact_authorities_and_later_unrelated_path(self):
        base, candidate = self._authority(self.base), self._authority(self.candidate)
        self.assertEqual(changed_paths(self.repo, base, candidate), ["evidence.json"])
        self._commit("later/sci_ed_002.json", b"later\n", "later")
        self.assertEqual(changed_paths(self.repo, base, candidate), ["evidence.json"])
        self.assertEqual(object_bytes(self.repo, candidate, "evidence.json"), b"{}\n")

    def test_wrong_commit_tree_missing_object_and_path_fail_exactly(self):
        base, candidate = self._authority(self.base), self._authority(self.candidate)
        cases = (
            (GitAuthority("0" * 40, candidate.tree), "LOCKED_COMMIT_OBJECT_MISSING"),
            (GitAuthority(candidate.commit, base.tree), "LOCKED_TREE_MISMATCH"),
        )
        for authority, reason in cases:
            with self.subTest(reason=reason), self.assertRaisesRegex(AuthorityError, reason):
                verify_authority(self.repo, authority)
        with self.assertRaisesRegex(AuthorityError, "LOCKED_PATH_OBJECT_MISSING"):
            object_bytes(self.repo, candidate, "missing.json")

    def test_non_ancestor_authority_fails_exactly(self):
        candidate = self._authority(self.candidate)
        subprocess.run(["git", "-C", str(self.repo), "checkout", "-q", "--orphan", "other"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "rm", "-q", "-rf", "."], check=True)
        other = self._commit("other.txt", b"other\n", "other")
        with self.assertRaisesRegex(AuthorityError, "NON_ANCESTOR_AUTHORITY"):
            changed_paths(self.repo, self._authority(other), candidate)
