#!/usr/bin/env python3
"""性能基线测试 — Step 3.1"""
import os, sys, time, json, statistics, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app
app = create_app()

with app.app_context():
    from backend.app.ncf_engine import ncf_engine
    from backend.app.models import Rating, MovieSimilarity, Movie
    from backend.app import db
    from sqlalchemy import func

    if not ncf_engine.is_ready():
        ncf_engine.load()

    print('='*70)
    print('【测试A】推荐API延迟 (demo用户, n=10, 预热后5次采样)')
    print('='*70)

    strategies = [
        ('popular', '/api/recommendations?strategy=popular&n=10'),
        ('itemcf', '/api/recommendations?strategy=itemcf&n=10'),
        ('ncf', '/api/recommendations?strategy=ncf&n=10'),
        ('hybrid', '/api/recommendations?strategy=hybrid&n=10'),
    ]

    latency_data = {}
    for sname, spath in strategies:
        with app.test_client() as client:
            client.post('/api/auth/login', json={'username': 'demo', 'password': 'demo123'})
            for _ in range(2):
                client.get(spath)
            times = []
            for _ in range(5):
                t0 = time.perf_counter()
                client.get(spath)
                times.append((time.perf_counter() - t0) * 1000)

            avg = statistics.mean(times); p50 = statistics.median(times)
            p95 = sorted(times)[-1]; stdev = statistics.stdev(times) if len(times) > 1 else 0
            latency_data[sname] = {'avg_ms': round(avg,1), 'p50_ms': round(p50,1),
                'p95_ms': round(p95,1), 'min_ms': round(min(times),1),
                'max_ms': round(max(times),1), 'stdev_ms': round(stdev,2)}
            print(f'  {sname:8s} avg={avg:6.1f}ms p50={p50:6.1f}ms p95={p95:6.1f}ms stdev={stdev:5.2f}ms')

    print()
    print('='*70)
    print('【测试B】NCF推理耗时分解 (demo user)')
    print('='*70)

    demo_id = 999999
    demo_ratings = Rating.query.filter_by(user_id=demo_id).order_by(Rating.timestamp.desc()).limit(50).all()
    rated_ids = {r.movie_id for r in demo_ratings}
    popular_unrated = (
        Rating.query.with_entities(Rating.movie_id, func.count(Rating.id).label('cnt'))
        .filter(~Rating.movie_id.in_(rated_ids))
        .group_by(Rating.movie_id).order_by(func.count(Rating.id).desc()).limit(500).all()
    )
    candidates = [int(mid) for mid, _ in popular_unrated]

    tests_ncf = [
        ('score(500候选)', lambda: ncf_engine.score(demo_id, candidates)),
        ('rank(500->10)', lambda: ncf_engine.rank(demo_id, candidates, top_k=10)),
        ('score(10候选)', lambda: ncf_engine.score(demo_id, candidates[:10])),
        ('score(不在训练集)', lambda: ncf_engine.score(200949, candidates[:10])),
    ]
    for name, fn in tests_ncf:
        times = []
        for _ in range(5):
            t0 = time.perf_counter()
            r = fn()
            times.append((time.perf_counter() - t0) * 1000)
        unit = 'μs' if statistics.mean(times) < 1 else 'ms'
        val = statistics.mean(times) if unit == 'ms' else statistics.mean(times) * 1000
        print(f'  {name:20s} avg={val:7.1f}{unit}  min={min(times)* (1 if unit=="ms" else 1000):.1f}{unit}')

    print()
    print('='*70)
    print('【测试C】DB查询耗时分解')
    print('='*70)

    demo_seed_ids = [r.movie_id for r in demo_ratings[:20]]
    times = []
    for _ in range(3):
        t0 = time.perf_counter()
        sims = (MovieSimilarity.query
            .filter(MovieSimilarity.movie_id.in_(demo_seed_ids))
            .order_by(MovieSimilarity.movie_id.asc(), MovieSimilarity.score.desc()).all())
        times.append((time.perf_counter() - t0) * 1000)
    print(f'  ItemCF相似度查询(20种子)  avg={statistics.mean(times):.1f}ms rows={len(sims)}')

    all_ids = list(set([s.similar_movie_id for s in sims[:100]] + demo_seed_ids))
    times = []
    for _ in range(3):
        t0 = time.perf_counter()
        movies = Movie.query.filter(Movie.id.in_(all_ids)).all()
        times.append((time.perf_counter() - t0) * 1000)
    print(f'  Movie详情查询({len(all_ids)}ID)      avg={statistics.mean(times):.1f}ms rows={len(movies)}')

    print()
    print('='*70)
    print('【测试D】并发请求 (itemcf, n=5, demo用户)')
    print('='*70)

    def concurrent_test(n_threads, path):
        errors = []; latencies = []; lock = threading.Lock()
        def worker(idx):
            try:
                with app.test_client() as c:
                    c.post('/api/auth/login', json={'username': 'demo', 'password': 'demo123'})
                    t0 = time.perf_counter()
                    resp = c.get(path)
                    with lock: latencies.append((time.perf_counter() - t0) * 1000)
                    if resp.status_code != 200:
                        with lock: errors.append(f'T{idx}:{resp.status_code}')
            except Exception as e:
                with lock: errors.append(f'T{idx}:{e}')
        threads = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(n_threads)]
        t0 = time.perf_counter()
        for t in threads: t.start()
        for t in threads: t.join(timeout=60)
        wall = (time.perf_counter() - t0) * 1000
        return {'threads': n_threads, 'wall_ms': round(wall,1),
            'avg_ms': round(statistics.mean(latencies),1) if latencies else 0,
            'p95_ms': round(sorted(latencies)[-1],1) if latencies else 0,
            'errors': len(errors)}

    for n in [5, 10]:
        r = concurrent_test(n, '/api/recommendations?strategy=itemcf&n=5')
        print(f'  {n}并发: wall={r["wall_ms"]}ms avg={r["avg_ms"]}ms p95={r["p95_ms"]}ms errors={r["errors"]}')

    print()
    print('='*70)
    print('性能基线汇总')
    print('='*70)
    print()
    print('| 策略     | avg    | p50    | p95    | stdev  | 评级 |')
    print('|----------|--------|--------|--------|--------|------|')
    for sname, d in latency_data.items():
        if d['avg_ms'] < 50: grade = '🟢 优'
        elif d['avg_ms'] < 200: grade = '🟡 良'
        elif d['avg_ms'] < 1000: grade = '🟠 可接受'
        else: grade = '🔴 差'
        print(f'| {sname:8s} | {d["avg_ms"]:5.0f}ms | {d["p50_ms"]:5.0f}ms | {d["p95_ms"]:5.0f}ms | {d["stdev_ms"]:5.1f}ms | {grade} |')

    out_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(out_dir, 'step3.1_results.json'), 'w') as f:
        json.dump({'latency': latency_data}, f, indent=2)
    print(f'\n结果保存完成')
