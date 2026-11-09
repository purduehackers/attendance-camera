//! Purdue Hackers ID: authorization code + PKCE, signed roles, opaque Redis sessions.
use anyhow::{Result, anyhow, ensure};
use axum::{
    http::{HeaderMap, header},
    response::{IntoResponse, Redirect, Response},
};
use openidconnect::{
    AccessTokenHash, AdditionalClaims, AuthorizationCode, ClientId, ClientSecret, CsrfToken,
    EndpointMaybeSet, EndpointNotSet, EndpointSet, IdToken, IssuerUrl, Nonce, OAuth2TokenResponse,
    PkceCodeChallenge, PkceCodeVerifier, RedirectUrl, Scope,
    core::{
        CoreAuthenticationFlow, CoreClient, CoreGenderClaim, CoreJweContentEncryptionAlgorithm,
        CoreJwsSigningAlgorithm, CoreProviderMetadata,
    },
};
use redis::aio::ConnectionManager;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::time::Duration;
use subtle::ConstantTimeEq;

const ISSUER: &str = "https://id.purduehackers.com/api/auth";
const FLOW_SECONDS: usize = 600;
const SESSION_SECONDS: i64 = 3600;
type OidcClient = CoreClient<
    EndpointSet,
    EndpointNotSet,
    EndpointNotSet,
    EndpointNotSet,
    EndpointMaybeSet,
    EndpointMaybeSet,
>;
type RoleToken =
    IdToken<Roles, CoreGenderClaim, CoreJweContentEncryptionAlgorithm, CoreJwsSigningAlgorithm>;

#[derive(Clone)]
pub struct Auth {
    origin: String,
    issuer: String,
    namespace: String,
    client_id: String,
    client_secret: String,
    http: reqwest::Client,
    secure: bool,
}

#[derive(Debug, Default, Deserialize, Serialize)]
struct Roles {
    #[serde(default)]
    roles: Vec<String>,
}
impl AdditionalClaims for Roles {}

#[derive(Deserialize, Serialize)]
struct Pending {
    binder: String,
    verifier: String,
    nonce: String,
}

#[derive(Deserialize)]
pub struct Callback {
    state: Option<String>,
    code: Option<String>,
    error: Option<String>,
    iss: Option<String>,
}

fn digest(value: &str) -> String {
    format!("{:x}", Sha256::digest(value.as_bytes()))
}

impl Auth {
    pub fn new(origin: &str, namespace: &str) -> Result<Self> {
        let url = url::Url::parse(origin)?;
        let local = matches!(url.host_str(), Some("localhost" | "127.0.0.1" | "[::1]"));
        let secure = url.scheme() == "https";
        ensure!(
            secure || (local && url.scheme() == "http"),
            "PUBLIC_ORIGIN requires HTTPS"
        );
        let issuer = std::env::var("PH_ID_ISSUER").unwrap_or_else(|_| ISSUER.into());
        // An alternate issuer is useful for isolated protocol tests, never on a public deployment.
        ensure!(
            issuer == ISSUER || local,
            "Public deployments must use Purdue Hackers ID"
        );
        Ok(Self {
            origin: origin.into(),
            issuer,
            namespace: namespace.into(),
            secure,
            client_id: std::env::var("PH_ID_CLIENT_ID")?,
            client_secret: crate::secret("PH_ID_CLIENT_SECRET")?,
            http: reqwest::Client::builder()
                .redirect(reqwest::redirect::Policy::none())
                .timeout(Duration::from_secs(10))
                .build()?,
        })
    }

    async fn client(&self) -> Result<OidcClient> {
        // Refresh discovery/JWKS for each login so provider key rotation needs no redeployment.
        let metadata =
            CoreProviderMetadata::discover_async(IssuerUrl::new(self.issuer.clone())?, &self.http)
                .await?;
        Ok(CoreClient::from_provider_metadata(
            metadata,
            ClientId::new(self.client_id.clone()),
            Some(ClientSecret::new(self.client_secret.clone())),
        )
        .set_redirect_uri(RedirectUrl::new(format!(
            "{}/api/auth/callback/purduehackers",
            self.origin
        ))?))
    }

    fn cookie_name(&self, flow: bool) -> &'static str {
        match (self.secure, flow) {
            (true, true) => "__Host-attendance-flow",
            (true, false) => "__Host-attendance",
            (false, true) => "attendance-flow",
            (false, false) => "attendance-session",
        }
    }

    fn cookie(&self, headers: &HeaderMap, flow: bool) -> Option<String> {
        let prefix = format!("{}=", self.cookie_name(flow));
        let mut values = headers
            .get_all(header::COOKIE)
            .iter()
            .filter_map(|v| v.to_str().ok())
            .flat_map(|v| v.split(';'))
            .filter_map(|v| v.trim().strip_prefix(&prefix));
        let value = values.next()?;
        // Reject duplicates and malformed tokens before allocating Redis keys.
        (values.next().is_none()
            && (32..=128).contains(&value.len())
            && value
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_'))
        .then(|| value.to_owned())
    }

    fn set_cookie(&self, response: &mut Response, flow: bool, value: &str, age: i64) {
        let secure = if self.secure { "; Secure" } else { "" };
        response.headers_mut().append(
            header::SET_COOKIE,
            format!(
                "{}={value}; Path=/; HttpOnly; SameSite=Lax; Max-Age={age}{secure}",
                self.cookie_name(flow),
            )
            .parse()
            .unwrap(),
        );
    }

    fn key(&self, kind: &str, value: &str) -> String {
        format!("{}:auth:{kind}:{}", self.namespace, digest(value))
    }

    pub async fn authenticated(
        &self,
        headers: &HeaderMap,
        connection: &mut ConnectionManager,
    ) -> Result<bool> {
        let Some(session) = self.cookie(headers, false) else {
            return Ok(false);
        };
        Ok(redis::cmd("EXISTS")
            .arg(self.key("session", &session))
            .query_async(connection)
            .await?)
    }

    pub async fn login(&self, connection: &mut ConnectionManager) -> Result<Response> {
        // Bound pending login state across all Vercel instances. No video is persisted.
        let count: i64 = redis::Script::new(
            "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],60) end; return n"
        ).key(format!("{}:auth:login-rate", self.namespace)).invoke_async(connection).await?;
        ensure!(count <= 120, "Login temporarily unavailable");
        let client = self.client().await?;
        let (challenge, verifier) = PkceCodeChallenge::new_random_sha256();
        let (url, state, nonce) = client
            .authorize_url(
                CoreAuthenticationFlow::AuthorizationCode,
                CsrfToken::new_random,
                Nonce::new_random,
            )
            .add_scope(Scope::new("profile".into()))
            .add_scope(Scope::new("roles".into()))
            .set_pkce_challenge(challenge)
            .url();
        let binder = CsrfToken::new_random_len(32);
        let pending = Pending {
            binder: digest(binder.secret()),
            verifier: verifier.secret().clone(),
            nonce: nonce.secret().clone(),
        };
        let _: () = redis::cmd("SET")
            .arg(self.key("flow", state.secret()))
            .arg(serde_json::to_string(&pending)?)
            .arg("EX")
            .arg(FLOW_SECONDS)
            .query_async(connection)
            .await?;
        let mut response = Redirect::to(url.as_str()).into_response();
        self.set_cookie(&mut response, true, binder.secret(), FLOW_SECONDS as i64);
        Ok(response)
    }

    pub async fn callback(
        &self,
        query: Callback,
        headers: &HeaderMap,
        connection: &mut ConnectionManager,
    ) -> Response {
        let result = self.finish(query, headers, connection).await;
        let mut response = match result {
            Ok(Some((session, age))) => {
                let mut response = Redirect::to("/").into_response();
                // Replace the previous session on successful sign-in.
                if let Some(old) = self.cookie(headers, false) {
                    let _: redis::RedisResult<usize> = redis::cmd("DEL")
                        .arg(self.key("session", &old))
                        .query_async(connection)
                        .await;
                }
                self.set_cookie(&mut response, false, &session, age);
                response
            }
            Ok(None) => Redirect::to("/login?reason=forbidden").into_response(),
            Err(_) => {
                // OAuth errors can contain codes/tokens; never log the original error.
                eprintln!("ID sign-in did not complete");
                Redirect::to("/login?reason=failed").into_response()
            }
        };
        self.set_cookie(&mut response, true, "", 0);
        response
    }

    async fn finish(
        &self,
        query: Callback,
        headers: &HeaderMap,
        connection: &mut ConnectionManager,
    ) -> Result<Option<(String, i64)>> {
        ensure!(query.error.is_none(), "Provider denied sign-in");
        ensure!(
            query.iss.as_ref().is_none_or(|iss| iss == &self.issuer),
            "Wrong authorization issuer"
        );
        let state = query
            .state
            .filter(|v| v.len() <= 128)
            .ok_or_else(|| anyhow!("Missing state"))?;
        let binder = self
            .cookie(headers, true)
            .ok_or_else(|| anyhow!("Missing browser binding"))?;
        let key = self.key("flow", &state);
        let saved: Option<String> = redis::cmd("GET").arg(&key).query_async(connection).await?;
        let pending: Pending =
            serde_json::from_str(&saved.ok_or_else(|| anyhow!("Expired state"))?)?;
        ensure!(
            bool::from(pending.binder.as_bytes().ct_eq(digest(&binder).as_bytes())),
            "Wrong browser binding"
        );
        let consumed: Option<String> = redis::cmd("GETDEL")
            .arg(&key)
            .query_async(connection)
            .await?;
        ensure!(consumed.is_some(), "State already consumed");
        let code = query
            .code
            .filter(|v| v.len() <= 4096)
            .ok_or_else(|| anyhow!("Missing code"))?;
        let client = self.client().await?;
        let token = client
            .exchange_code(AuthorizationCode::new(code))?
            .set_pkce_verifier(PkceCodeVerifier::new(pending.verifier))
            .request_async(&self.http)
            .await?;
        let raw = token
            .extra_fields()
            .id_token()
            .ok_or_else(|| anyhow!("Missing ID token"))?;
        // Decode the original compact JWT into our extra-claims type, then verify it fully.
        let id_token: RoleToken = raw.to_string().parse()?;
        let verifier = client.id_token_verifier();
        let claims = id_token.claims(&verifier, &Nonce::new(pending.nonce))?;
        if let Some(expected) = claims.access_token_hash() {
            let actual = AccessTokenHash::from_token(
                token.access_token(),
                id_token.signing_alg()?,
                id_token.signing_key(&verifier)?,
            )?;
            ensure!(actual == *expected, "Access token hash mismatch");
        }
        if !claims
            .additional_claims()
            .roles
            .iter()
            .any(|role| role == "organizer" || role == "admin")
        {
            return Ok(None);
        }
        let age = (claims.expiration().timestamp() - (crate::protocol::now_ms() / 1000) as i64)
            .min(SESSION_SECONDS);
        ensure!(age > 0, "Expired ID token");
        let session = CsrfToken::new_random_len(32).secret().clone();
        let _: () = redis::cmd("SET")
            .arg(self.key("session", &session))
            .arg("authorized")
            .arg("EX")
            .arg(age)
            .query_async(connection)
            .await?;
        Ok(Some((session, age)))
    }

    pub async fn logout(
        &self,
        headers: &HeaderMap,
        connection: &mut ConnectionManager,
    ) -> Result<Response> {
        if let Some(session) = self.cookie(headers, false) {
            let _: usize = redis::cmd("DEL")
                .arg(self.key("session", &session))
                .query_async(connection)
                .await?;
        }
        let mut response = Redirect::to("/login").into_response();
        self.set_cookie(&mut response, false, "", 0);
        self.set_cookie(&mut response, true, "", 0);
        Ok(response)
    }
}
