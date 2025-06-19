"""
GUST Bot Database Performance Monitor
Simple, practical performance monitoring
"""

from utils.gust_db_optimization import get_performance_report
from datetime import datetime
import json

def print_performance_report():
    """Print human-readable performance report"""
    print("=" * 50)
    print("GUST Bot Database Performance Report")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    stats = get_performance_report()
    
    print(f"\n📊 Cache Performance:")
    print(f"   Hit Rate: {stats['cache_hit_rate']}")
    print(f"   Total Queries: {stats['total_queries']}")
    print(f"   Cache Hits: {stats['cache_hits']}")
    print(f"   Cache Misses: {stats['cache_misses']}")
    
    print(f"\n⚡ Query Performance:")
    print(f"   Average Query Time: {stats['avg_query_time']}")
    print(f"   Slow Queries (>100ms): {stats['slow_queries']}")
    
    # Performance assessment
    hit_rate = float(stats['cache_hit_rate'].rstrip('%'))
    if hit_rate > 70:
        print(f"\n✅ Excellent cache performance!")
    elif hit_rate > 50:
        print(f"\n👍 Good cache performance")
    else:
        print(f"\n⚠️ Cache warming up - performance will improve")

if __name__ == "__main__":
    print_performance_report()
