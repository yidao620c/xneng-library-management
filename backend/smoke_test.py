"""后端 API 冒烟测试：认证 / 图书 / 评论 / 借阅 / 消息 / 统计"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UNIQ = f"reader{int(time.time()) % 100000}"

sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:8000"
PASSED, FAILED = 0, 0


def call(method, path, body=None, token=None, expect=200):
    global PASSED, FAILED
    if "?" in path:
        base, qs = path.split("?", 1)
        path = base + "?" + urllib.parse.quote(qs, safe="=&")
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read().decode())
            status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw}
        status = e.code
    ok = status == expect
    if ok:
        PASSED += 1
        print(f"  PASS {method} {path} -> {status}")
    else:
        FAILED += 1
        print(f"  FAIL {method} {path} -> {status} (expect {expect}): {payload}")
    return payload


print("== 认证 ==")
r = call("POST", "/api/auth/login", {"username": "admin", "password": "admin123"})
admin_token = r["accessToken"]
admin_refresh = r["refreshToken"]
assert r["user"]["role"] == "admin"

r = call("POST", "/api/auth/login", {"username": "user", "password": "user123"})
user_token = r["accessToken"]
user_id = r["user"]["id"]

r = call("POST", "/api/auth/login", {"username": "vip", "password": "vip123"})
vip_token = r["accessToken"]

call("POST", "/api/auth/login", {"username": "user", "password": "wrong"}, expect=401)
r = call("POST", "/api/auth/refresh", {"refreshToken": admin_refresh})
assert "accessToken" in r
call("POST", "/api/auth/refresh", {"refreshToken": "bad-token"}, expect=401)
call("GET", "/api/auth/me", token=user_token)
call("GET", "/api/auth/me", expect=401)

r = call("POST", "/api/auth/register", {"username": UNIQ, "password": "pass123", "nickname": "新读者"})
assert r["user"]["role"] == "user"
new_token = r["accessToken"]
call("POST", "/api/auth/register", {"username": UNIQ, "password": "pass123"}, expect=400)

print("== 图书与分类 ==")
cats = call("GET", "/api/categories")
assert len(cats) >= 5
r = call("GET", "/api/books?keyword=三体")
assert r["total"] == 1 and r["items"][0]["title"] == "三体"
r = call("GET", "/api/books?keyword=刘慈欣")
assert r["total"] == 1
r = call("GET", f"/api/books?categoryId={cats[0]['id']}")
assert all(b["categoryId"] == cats[0]["id"] for b in r["items"])
r = call("GET", "/api/books?status=available&size=50")
assert all(b["availableCopies"] > 0 for b in r["items"])
r = call("GET", "/api/books?tag=科幻")
assert r["total"] == 1
tags = call("GET", "/api/books/tags")
assert "科幻" in tags
book_id = call("GET", "/api/books?keyword=活着")["items"][0]["id"]
detail = call("GET", f"/api/books/{book_id}")
assert detail["ratingAvg"] >= 4

print("== 评论 ==")
rv = call("POST", f"/api/books/{book_id}/reviews", {"rating": 5, "content": "非常值得一读的经典作品！"}, token=user_token)
assert rv["rating"] == 5
call("POST", f"/api/books/{book_id}/reviews", {"rating": 4, "content": "太短"}, token=user_token, expect=400)
call("POST", f"/api/books/{book_id}/reviews", {"rating": 4, "content": "评论内容必须登录才能提交哦"}, expect=401)
r = call("GET", f"/api/books/{book_id}/reviews")
assert r["total"] >= 1

print("== 借阅流程 ==")
bid = call("GET", "/api/books?keyword=算法导论")["items"][0]["id"]
b = call("POST", "/api/borrows", {"bookId": bid}, token=new_token)
assert b["status"] == "borrowed" and b["dueDate"]
call("POST", "/api/borrows", {"bookId": bid}, token=new_token, expect=400)  # 重复借阅
call("POST", "/api/borrows", {"bookId": bid}, expect=401)
r = call("GET", "/api/borrows/my?status=active", token=new_token)
assert r["total"] >= 1
s = call("GET", "/api/borrows/my/summary", token=new_token)
assert s["borrowing"] >= 1
r = call("POST", f"/api/borrows/{b['id']}/return", token=new_token)
assert r["status"] == "returning"
call("GET", "/api/borrows", token=user_token, expect=403)  # 非管理员
r = call("GET", "/api/borrows?status=returning", token=admin_token)
assert any(x["id"] == b["id"] for x in r["items"])
r = call("POST", f"/api/borrows/{b['id']}/remind", token=admin_token)
assert r["remindedAt"]
avail_before = call("GET", f"/api/books/{bid}")["availableCopies"]
r = call("POST", f"/api/borrows/{b['id']}/confirm-return", token=admin_token)
assert r["status"] == "returned"
assert call("GET", f"/api/books/{bid}")["availableCopies"] == avail_before + 1

print("== 消息 ==")
r = call("GET", "/api/messages", token=user_token)
assert r["total"] >= 3
unread = call("GET", "/api/messages/unread-count", token=user_token)
assert unread["unreadCount"] >= 1  # 催还通知 + 全局消息
msg_id = r["items"][0]["id"]
call("POST", f"/api/messages/{msg_id}/read", token=user_token)
assert call("GET", "/api/messages/unread-count", token=user_token)["unreadCount"] == unread["unreadCount"] - 1
call("POST", "/api/messages/read-all", token=user_token)
assert call("GET", "/api/messages/unread-count", token=user_token)["unreadCount"] == 0
m = call("POST", "/api/messages", {"title": "测试消息", "content": "这是一条测试全局消息内容"}, token=admin_token)
call("POST", "/api/messages", {"title": "无权限", "content": "普通用户不能发布消息"}, token=user_token, expect=403)
r = call("GET", "/api/messages/admin/list", token=admin_token)
assert any(x["id"] == m["id"] for x in r["items"])
call("DELETE", f"/api/messages/{m['id']}", token=admin_token)

print("== 个人中心 ==")
r = call("PUT", "/api/profile", {"nickname": "书友小读改", "email": "user2@library.local", "phone": "13900000002"}, token=user_token)
assert r["nickname"] == "书友小读改"
call("PUT", "/api/profile", {"nickname": "", "email": "", "phone": ""}, token=user_token, expect=422)

print("== 管理员：用户/图书/统计 ==")
r = call("GET", "/api/users?keyword=user", token=admin_token)
assert r["total"] >= 1
uid = r["items"][0]["id"]
call("PUT", f"/api/users/{uid}/role", {"role": "vip"}, token=admin_token)
call("PUT", f"/api/users/{uid}/role", {"role": "user"}, token=admin_token)
call("PUT", f"/api/users/{uid}/status", {"isActive": True}, token=admin_token)
call("GET", "/api/users", expect=401)
nb = call("POST", "/api/books", {"title": "测试新书", "author": "测试作者", "isbn": "9780000000001", "categoryId": cats[0]["id"], "totalCopies": 3, "availableCopies": 3}, token=admin_token)
call("PUT", f"/api/books/{nb['id']}", {"title": "测试新书改", "author": "测试作者", "isbn": "9780000000001", "categoryId": cats[0]["id"], "totalCopies": 2, "availableCopies": 2}, token=admin_token)
call("POST", "/api/books", {"title": "无权限书", "isbn": "9780000000002"}, token=user_token, expect=403)
call("DELETE", f"/api/books/{nb['id']}", token=admin_token)
ov = call("GET", "/api/stats/overview", token=admin_token)
assert ov["totalBooks"] >= 18 and ov["totalUsers"] >= 4
call("GET", "/api/stats/overview", expect=401)
for g in ("day", "week", "month"):
    t = call("GET", f"/api/stats/borrow-trend?granularity={g}", token=admin_token)
    assert len(t["items"]) == t["span"]

print("== 分类管理 ==")
nc = call("POST", "/api/categories", {"name": "测试分类", "description": "临时"}, token=admin_token)
call("PUT", f"/api/categories/{nc['id']}", {"name": "测试分类改", "description": "临时改"}, token=admin_token)
call("DELETE", f"/api/categories/{nc['id']}", token=admin_token)
call("DELETE", f"/api/categories/{cats[0]['id']}", token=admin_token, expect=400)  # 有图书

print(f"\n结果: {PASSED} passed, {FAILED} failed")
exit(1 if FAILED else 0)
