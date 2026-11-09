"""Isolated OIDC issuer for integration tests; never used by the deployed service."""
import base64
import hashlib
from http.server import BaseHTTPRequestHandler
import json
import secrets
import time
from urllib.parse import parse_qs

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import jwt


def b64(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


class Identity(BaseHTTPRequestHandler):
    issuer = ""
    client_id = "attendance-fixture"
    client_secret = "fixture-secret-" + "z" * 32
    key = Ed25519PrivateKey.generate()
    codes = {}

    def log_message(self, *_):
        pass

    @classmethod
    def code(cls, query, scenario="organizer"):
        code = secrets.token_urlsafe(32)
        cls.codes[code] = (query, scenario)
        return code

    def reply(self, body, status=200):
        body = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/.well-known/openid-configuration":
            self.reply({
                "issuer": self.issuer,
                "authorization_endpoint": self.issuer + "/authorize",
                "token_endpoint": self.issuer + "/token",
                "jwks_uri": self.issuer + "/jwks",
                "response_types_supported": ["code"],
                "subject_types_supported": ["public"],
                "id_token_signing_alg_values_supported": ["EdDSA"],
                "token_endpoint_auth_methods_supported": ["client_secret_basic"],
                "code_challenge_methods_supported": ["S256"],
            })
        elif self.path == "/jwks":
            self.reply({"keys": [{"kty": "OKP", "crv": "Ed25519", "alg": "EdDSA", "use": "sig", "kid": "fixture",
                                  "x": b64(self.key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))}]})
        else:
            self.reply({"error": "not_found"}, 404)

    def do_POST(self):
        form = parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode())
        expected = "Basic " + base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        entry = self.codes.pop(form.get("code", [""])[0], None)
        if self.path != "/token" or self.headers.get("Authorization") != expected or not entry:
            return self.reply({"error": "invalid_grant"}, 400)
        query, scenario = entry
        challenge = b64(hashlib.sha256(form.get("code_verifier", [""])[0].encode()).digest())
        if (challenge != query["code_challenge"][0] or form.get("redirect_uri") != query.get("redirect_uri")
                or form.get("grant_type") != ["authorization_code"]):
            return self.reply({"error": "invalid_grant"}, 400)
        now = int(time.time())
        access = "fixture-access-token"
        claims = {"iss": self.issuer, "aud": self.client_id, "sub": "fixture-user", "iat": now,
                  "exp": now + 3600, "nonce": query["nonce"][0], "roles": [scenario],
                  "at_hash": b64(hashlib.sha512(access.encode()).digest()[:32])}
        if scenario == "missing-role":
            claims.pop("roles")
        overrides = {"wrong-nonce": {"nonce": "wrong"}, "wrong-audience": {"aud": "other-app"},
                     "wrong-issuer": {"iss": "https://wrong.example"}, "expired": {"exp": now - 60},
                     "wrong-hash": {"at_hash": "wrong"}}
        claims.update(overrides.get(scenario, {}))
        key = Ed25519PrivateKey.generate() if scenario == "wrong-signature" else self.key
        self.reply({"access_token": access, "token_type": "Bearer", "expires_in": 3600,
                    "id_token": jwt.encode(claims, key, algorithm="EdDSA", headers={"kid": "fixture"})})
