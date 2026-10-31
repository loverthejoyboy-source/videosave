import hmac
from flask import Blueprint, request, jsonify
import config as C
from security import guard, hit, client_ip, make_token, valid_token, err
from validator import check
from extractor import extract, Busy, Fail

bp = Blueprint("api", __name__)

@bp.post("/api/token")
@guard
def token():
    d = request.get_json(silent=True)
    if not isinstance(d, dict) or d.get("agree") is not True or d.get("v") != C.TERMS_VERSION:
        return err(400, "শর্তাবলীতে সম্মতি দিন।")
    return jsonify(token=make_token())

@bp.post("/api/parse")
@guard
def parse():
    d = request.get_json(silent=True)
    if not isinstance(d, dict) or d.get("website"):
        return err(400, "অনুরোধ গ্রহণযোগ্য নয়।")
    if not valid_token(request.headers.get("X-Token", "")):
        return err(403, "সেশন শেষ। আবার চেষ্টা করুন।", "token")
    res = check(d.get("url"))
    if not res:
        return err(400, "লিংকটি সমর্থিত নয়। সমর্থিত সাইটের পূর্ণ https লিংক দিন।")
    if d.get("platform") in C.PLATFORMS and d["platform"] != res[0]:
        return err(400, "লিংকটি আপনার বাছাই করা সাইটের নয়।")
    try:
        return jsonify(extract(res[1]))
    except Busy:
        return err(503, "সার্ভার ব্যস্ত। কিছুক্ষণ পরে চেষ্টা করুন।")
    except Fail:
        return err(422, "লিংকটি পড়া যায়নি। ভিডিওটি প্রাইভেট, অসমর্থিত বা সাময়িকভাবে ব্লক হতে পারে।")

@bp.get("/api/keepalive")
def keepalive():
    given = request.headers.get("X-Keepalive-Token", "")
    if not hit("ka:" + client_ip(), 10, 60) or not C.KEEPALIVE_TOKEN or \
       not hmac.compare_digest(C.KEEPALIVE_TOKEN.encode(), given.encode()):
        return "", 404
    return jsonify(ok=True)
