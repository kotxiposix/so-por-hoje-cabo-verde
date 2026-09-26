from __future__ import annotations

import unittest
from unittest.mock import patch

from sph.account_deletion import (
    AccountAuthenticationError,
    AccountDeletionConfig,
    SupabaseAccountDeletion,
    bearer_token,
)


class FakeResponse:
    def __init__(self, body: bytes = b"") -> None:
        self.body = body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


class AccountDeletionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = AccountDeletionConfig(
            supabase_url="https://project.supabase.co",
            service_role_key="service-secret",
        )

    def test_bearer_token_rejects_missing_or_malformed_value(self) -> None:
        self.assertEqual(bearer_token("Bearer access-token"), "access-token")
        for value in (None, "", "access-token", "Basic access-token"):
            with self.assertRaises(AccountAuthenticationError):
                bearer_token(value)

    @patch("sph.account_deletion.urlopen")
    def test_server_deletes_only_user_resolved_from_access_token(self, mock_urlopen) -> None:
        mock_urlopen.side_effect = [
            FakeResponse(b'{"id":"resolved-user"}'),
            FakeResponse(),
        ]

        deleted_id = SupabaseAccountDeletion(self.config).delete_for_access_token("user-access-token")

        self.assertEqual(deleted_id, "resolved-user")
        current_user_request = mock_urlopen.call_args_list[0].args[0]
        delete_request = mock_urlopen.call_args_list[1].args[0]
        self.assertEqual(current_user_request.full_url, "https://project.supabase.co/auth/v1/user")
        self.assertEqual(current_user_request.headers["Authorization"], "Bearer user-access-token")
        self.assertEqual(
            delete_request.full_url,
            "https://project.supabase.co/auth/v1/admin/users/resolved-user",
        )
        self.assertEqual(delete_request.get_method(), "DELETE")
        self.assertEqual(delete_request.headers["Authorization"], "Bearer service-secret")


if __name__ == "__main__":
    unittest.main()
