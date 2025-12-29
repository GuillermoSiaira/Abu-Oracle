import time, json, statistics, sys, pathlib
from datetime import datetime, timedelta

# Ensure project root and abu_engine are on path
root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'abu_engine'))

from fastapi.testclient import TestClient  # type: ignore
from abu_engine.main import app  # type: ignore

client = TestClient(app)

lat = -34.6037
lon = -58.3816
birth = "1990-01-01T12:00:00Z"

# Prime cache
client.post('/analyze', json={'birth':{'date':birth,'lat':lat,'lon':lon},'current':{'lat':lat,'lon':lon}})

N = 5
cached = []
for _ in range(N):
    t0 = time.perf_counter()
    client.post('/analyze', json={'birth':{'date':birth,'lat':lat,'lon':lon},'current':{'lat':lat,'lon':lon}})
    cached.append(time.perf_counter()-t0)

# Uncached by varying minute
base_dt = datetime.fromisoformat(birth.replace('Z','+00:00'))
uncached = []
for i in range(N):
    dt = (base_dt + timedelta(minutes=i+1)).isoformat().replace('+00:00','Z')
    t0 = time.perf_counter()
    client.post('/analyze', json={'birth':{'date':dt,'lat':lat,'lon':lon},'current':{'lat':lat,'lon':lon}})
    uncached.append(time.perf_counter()-t0)

result = {
    'cached_avg': statistics.mean(cached),
    'uncached_avg': statistics.mean(uncached),
    'speedup_factor': (statistics.mean(uncached)/statistics.mean(cached)) if statistics.mean(cached)>0 else None,
    'cached_samples': cached,
    'uncached_samples': uncached
}

print(json.dumps(result, indent=2))
