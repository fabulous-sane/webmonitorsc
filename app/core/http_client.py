import httpx

timeout = httpx.Timeout(10.0, connect=5.0)

limits = httpx.Limits(
    max_connections=200,
    max_keepalive_connections=50,
)

client = httpx.AsyncClient(
    timeout=timeout,
    follow_redirects=True,
    limits=limits,
    headers={"User-Agent": "WebCheckBot/1.0"},
    max_redirects=5,
)
