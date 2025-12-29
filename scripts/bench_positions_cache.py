import time, json, statistics, sys, pathlib
from datetime import datetime, timedelta

root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'abu_engine'))

from abu_engine.core.chart import chart_json  # type: ignore

lat = -34.6037
lon = -58.3816
birth = datetime.fromisoformat("1990-01-01T12:00:00+00:00")

# Warm
chart_json(lat, lon, birth)

N = 10
cached=[]
for _ in range(N):
    t0=time.perf_counter(); chart_json(lat, lon, birth); cached.append(time.perf_counter()-t0)

uncached=[]
for i in range(N):
    dt = birth + timedelta(minutes=i+1)
    t0=time.perf_counter(); chart_json(lat, lon, dt); uncached.append(time.perf_counter()-t0)

print(json.dumps({
  'cached_avg': statistics.mean(cached),
  'uncached_avg': statistics.mean(uncached),
  'speedup_factor': (statistics.mean(uncached)/statistics.mean(cached)) if statistics.mean(cached)>0 else None,
  'cached_samples': cached,
  'uncached_samples': uncached
}, indent=2))
