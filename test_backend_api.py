from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api():
    print("Testing TV Guide Backend API...")
    
    # 1. Health
    r = client.get("/api/health")
    assert r.status_code == 200, f"Health failed: {r.text}"
    print("  ✓ /api/health passed")
    
    # 2. Channels
    r = client.get("/api/channels")
    assert r.status_code == 200
    channels = r.json().get("channels", [])
    assert len(channels) >= 115, f"Expected at least 115 channels, got {len(channels)}"
    print(f"  ✓ /api/channels returned {len(channels)} channels with frequency data")
    
    # 3. Channel schedule
    ch_id = channels[0]["id"]
    r = client.get(f"/api/channels/{ch_id}/schedule")
    assert r.status_code == 200
    sched = r.json().get("schedule", [])
    assert len(sched) > 0, "Schedule is empty"
    print(f"  ✓ /api/channels/{ch_id}/schedule returned {len(sched)} broadcasts")
    
    # 4. Now Airing
    r = client.get("/api/now")
    assert r.status_code == 200
    now_items = r.json().get("now_airing", [])
    assert len(now_items) > 0, "No items airing"
    print(f"  ✓ /api/now returned {len(now_items)} currently airing programs")
    
    # 5. Next Airing
    r = client.get("/api/next")
    assert r.status_code == 200
    next_items = r.json().get("next_airing", [])
    print(f"  ✓ /api/next returned {len(next_items)} upcoming programs")
    
    # 6. Movies & Content Library (Dynamic from live schedules)
    r = client.get("/api/movies?page=1&limit=10")
    assert r.status_code == 200
    movies_data = r.json()
    assert len(movies_data["results"]) == 10
    print(f"  ✓ /api/movies returned {movies_data['total']} total real-world scheduled items (page 1 has 10)")
    
    r_series = client.get("/api/movies?type=series&limit=5")
    assert r_series.status_code == 200
    print(f"  ✓ /api/movies?type=series returned {r_series.json()['total']} series from live schedules")

    r_doc = client.get("/api/movies?type=documentary&limit=5")
    assert r_doc.status_code == 200
    print(f"  ✓ /api/movies?type=documentary returned {r_doc.json()['total']} documentaries from live schedules")
    
    # 7. Movie Details with Grouped Broadcasts (e.g. Al Ameel Sefr - content_id 6)
    r = client.get("/api/content/6")
    assert r.status_code == 200
    content = r.json()
    print(f"  ✓ /api/content/6 ({content['title_ar']}) returned with {content['airings_count']} broadcasts across channels")
    
    # 8. Search (Arabic + Diacritics + English)
    r = client.get("/api/search?q=العميل")
    assert r.status_code == 200
    results = r.json().get("results", [])
    assert len(results) > 0
    print(f"  ✓ /api/search?q=العميل returned {len(results)} matches (Top: {results[0]['title_ar']})")
    
    r2 = client.get("/api/search?q=zero")
    assert r2.status_code == 200
    results2 = r2.json().get("results", [])
    print(f"  ✓ /api/search?q=zero returned {len(results2)} matches")
    
    # 9. Reminders System (Create, List, Delete)
    rem_payload = {
        "broadcast_id": "test_broadcast_123",
        "title": "ابن الحاج أحمد",
        "channel_name": "روتانا سينما مصر",
        "start_datetime": "2026-08-30T22:00:00+03:00",
        "remind_1hour": True,
        "remind_10min": True
    }
    r_create = client.post("/api/reminders", json=rem_payload)
    assert r_create.status_code == 200
    rem_id = r_create.json()["reminder"]["id"]
    print(f"  ✓ POST /api/reminders created reminder: {rem_id}")
    
    r_list = client.get("/api/reminders")
    assert r_list.status_code == 200
    assert r_list.json()["count"] > 0
    print(f"  ✓ GET /api/reminders returned {r_list.json()['count']} active reminders")
    
    r_del = client.delete(f"/api/reminders/{rem_id}")
    assert r_del.status_code == 200
    print(f"  ✓ DELETE /api/reminders/{rem_id} removed reminder")
    
    print("\nALL BACKEND API TESTS PASSED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    test_api()

