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
        return err(400, "Please accept the terms to continue.")
    return jsonify(token=make_token())

@bp.post("/api/parse")
@guard
def parse():
    d = request.get_json(silent=True)
    if not isinstance(d, dict) or d.get("website"):
        return err(400, "Request not accepted.")
    if not valid_token(request.headers.get("X-Token", "")):
        return err(403, "Session expired. Please try again.", "token")
    res = check(d.get("url"))
    if not res:
        return err(400, "This link isn't supported. Paste the full https link from a supported site.")
    if d.get("platform") in C.PLATFORMS and d["platform"] != res[0]:
        return err(400, "That link doesn't match the site you selected.")
    try:
        return jsonify(extract(res[1]))
    except Busy:
        return err(503, "The server is busy. Please try again shortly.")
    except Fail:
        return err(422, "Couldn't read this link. The video may be private, unsupported, or temporarily blocked.")

@bp.get("/api/keepalive")
def keepalive():
    given = request.headers.get("X-Keepalive-Token", "")
    if not hit("ka:" + client_ip(), 10, 60) or not C.KEEPALIVE_TOKEN or \
       not hmac.compare_digest(C.KEEPALIVE_TOKEN.encode(), given.encode()):
        return "", 404
    return jsonify(ok=True)
