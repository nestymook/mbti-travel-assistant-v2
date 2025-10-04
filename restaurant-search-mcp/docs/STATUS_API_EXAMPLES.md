# Status Monitoring API Examples

## Basic Status Check Examples

### System Health Check
```bash
curl -X GET "https://your-gateway-url/status/health" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Server Status Check
```bash
curl -X GET "https://your-gateway-url/status/servers/restaurant-search-mcp" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Manual Health Check
```bash
curl -X POST "https://your-gateway-url/status/health-check" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"server_names": ["restaurant-search-mcp"]}'
```

### Circuit Breaker Control
```bash
curl -X POST "https://your-gateway-url/status/circuit-breaker" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "reset", "server_names": ["restaurant-search-mcp"]}'
```

## Python Integration Examples

### Basic Status Client
```python
import aiohttp
import asyncio

class StatusClient:
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {jwt_token}'}
    
    async def get_health(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/status/health", headers=self.headers) as response:
                return await response.json()

# Usage
client = StatusClient("https://your-gateway-url", jwt_token)
health = await client.get_health()
print(f"System Health: {health}")
```

### Console Dashboard
```python
class StatusDashboard:
    def __init__(self, client: StatusClient):
        self.client = client
    
    async def display(self):
        health = await self.client.get_health()
        print("=== STATUS DASHBOARD ===")
        print(f"Health: {health['data']['overall_health_percentage']:.1f}%")
        print(f"Servers: {health['data']['total_servers']}")
```