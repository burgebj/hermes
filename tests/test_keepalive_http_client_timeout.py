"""Regression tests for _build_keepalive_http_client timeout (#37662).

The fix adds an explicit httpx.Timeout(10.0, connect=5.0) to the client
so stalled IPv6 connections don't hang the agent indefinitely.  Without
the fix, httpx applies its default Timeout(5.0).  The distinguishing
signal is the read timeout: 10.0 with fix vs 5.0 without.
"""


class TestBuildKeepaliveHttpClient:
    """Verify that _build_keepalive_http_client includes explicit timeouts."""

    def test_explicit_read_timeout_is_10_seconds(self):
        """Fix sets read timeout to 10.0 (httpx default is 5.0).

        Without the fix, httpx.Client uses its built-in default of 5.0
        for read/write/pool.  With the fix, we explicitly configure
        Timeout(10.0, connect=5.0), which sets read/write/pool to 10.0.
        """
        from run_agent import AIAgent

        client = AIAgent._build_keepalive_http_client("https://api.example.com/v1")
        assert client is not None, "build_keepalive_http_client must return a client"

        timeout = client.timeout
        read_timeout = timeout.read
        assert read_timeout == 10.0, (
            f"Expected read timeout 10.0 (explicit in fix), got {read_timeout}. "
            f"Without the fix, httpx default is 5.0."
        )

    def test_connect_timeout_is_5_seconds(self):
        """Fix sets explicit connect timeout to 5.0."""
        from run_agent import AIAgent

        client = AIAgent._build_keepalive_http_client("https://api.example.com/v1")
        timeout = client.timeout
        connect = timeout.connect
        assert connect == 5.0, (
            f"Expected connect timeout 5.0, got {connect}"
        )

    def test_client_works_without_base_url(self):
        """Should work with empty base_url (returns client, not None)."""
        from run_agent import AIAgent

        client = AIAgent._build_keepalive_http_client("")
        assert client is not None

    def test_client_is_httpx_client(self):
        """Returned object must be an httpx.Client."""
        import httpx
        from run_agent import AIAgent

        client = AIAgent._build_keepalive_http_client("https://api.example.com/v1")
        assert isinstance(client, httpx.Client), (
            "Must return httpx.Client instance"
        )
