from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.auth.domain.errors import InvalidTokenError
from app.auth.service.jwt_token_service import JwtTokenService

# Constants
ALGORITHM = "HS256"
AUTH_DURATION = timedelta(hours=1)

# The signing key is injected, so this test needs no application configuration.
JWT_SECRET = "supersecretkey"


@pytest.fixture
def token_service() -> JwtTokenService:
    return JwtTokenService(secret=JWT_SECRET, algorithm=ALGORITHM)


@pytest.mark.unit
class TestJWT:
    def test_encode_jwt_token(self, token_service: JwtTokenService):
        """Test the JWT token encoding functionality."""
        username = "testuser"

        # Encode the token
        token = token_service.encode(username)

        # Decode the token to validate the encoding
        decoded_token = token_service.decode(token)

        # Ensure the decoded token contains the correct username
        assert decoded_token.sub == username

        # Ensure the token contains the necessary fields
        assert isinstance(decoded_token.exp, float)
        assert isinstance(decoded_token.iat, float)
        assert isinstance(decoded_token.sub, str)

    def test_decode_valid_jwt_token(self, token_service: JwtTokenService):
        """Test decoding a valid JWT token."""
        username = "testuser"

        # Encode a valid token
        token = token_service.encode(username)

        # Decode the token
        decoded_token = token_service.decode(token)

        # Ensure the decoded token contains the correct username
        assert decoded_token.sub == username
        assert isinstance(decoded_token.exp, float)
        assert isinstance(decoded_token.iat, float)

    def test_decode_invalid_jwt_token(self, token_service: JwtTokenService):
        """Test decoding an invalid JWT token."""
        invalid_token = "invalid.token.here"

        # Try decoding an invalid token and ensure it raises a domain error
        with pytest.raises(InvalidTokenError, match="Invalid token"):
            token_service.decode(invalid_token)

    def test_decode_expired_jwt_token(self, token_service: JwtTokenService):
        """Test decoding an expired JWT token."""
        username = "testuser"

        # Create a token with a past expiration date
        expired_token = jwt.encode(
            {
                "exp": (datetime.now() - timedelta(days=1)).timestamp(),
                "iat": datetime.now().timestamp(),
                "sub": username,
            },
            JWT_SECRET,
            algorithm=ALGORITHM,
        )

        # Try decoding the expired token and ensure it raises a domain error
        with pytest.raises(InvalidTokenError, match="Invalid token"):
            token_service.decode(expired_token)

    def test_decode_token_signed_with_another_secret(
        self, token_service: JwtTokenService
    ):
        """A token signed by a different key must be rejected."""
        foreign_token = JwtTokenService(secret="a-different-secret").encode("testuser")

        with pytest.raises(InvalidTokenError, match="Invalid token"):
            token_service.decode(foreign_token)

    def test_decode_rejects_an_unsigned_token(self, token_service: JwtTokenService):
        """A token with ``alg: none`` and no signature must not be trusted."""
        unsigned = jwt.encode(
            {"exp": 9_999_999_999.0, "iat": 0.0, "sub": "testuser"},
            key="",
            algorithm="none",
        )

        with pytest.raises(InvalidTokenError, match="Invalid token"):
            token_service.decode(unsigned)

    def test_decode_rejects_a_token_missing_claims(
        self, token_service: JwtTokenService
    ):
        """Correctly signed, but not the payload this service issues."""
        partial = jwt.encode({"sub": "testuser"}, JWT_SECRET, algorithm=ALGORITHM)

        with pytest.raises(InvalidTokenError, match="Invalid token"):
            token_service.decode(partial)

    def test_decode_rejects_a_token_with_unexpected_claims(
        self, token_service: JwtTokenService
    ):
        """Extra claims (e.g. a smuggled role) are not silently accepted."""
        padded = jwt.encode(
            {
                "exp": 9_999_999_999.0,
                "iat": 0.0,
                "sub": "testuser",
                "role": "admin",
            },
            JWT_SECRET,
            algorithm=ALGORITHM,
        )

        with pytest.raises(InvalidTokenError, match="Invalid token"):
            token_service.decode(padded)

    def test_encode_places_now_between_iat_and_exp(
        self, token_service: JwtTokenService
    ):
        """Regression guard: a freshly issued token is valid right now.

        Encoding with a naive local ``datetime`` object rather than a POSIX
        timestamp makes PyJWT read the wall clock as UTC, pushing ``iat`` into
        the future and making every just-minted token fail to decode.
        """
        before = datetime.now(timezone.utc).timestamp()
        # The decode itself would raise ImmatureSignatureError on a future iat.
        decoded = token_service.decode(token_service.encode("testuser"))
        after = datetime.now(timezone.utc).timestamp()

        assert decoded.iat <= after
        assert decoded.exp >= before

    def test_encode_honours_the_injected_auth_duration(self):
        """``exp - iat`` is the configured lifetime, not a hard-coded hour."""
        service = JwtTokenService(secret=JWT_SECRET, auth_duration=timedelta(minutes=5))

        decoded = service.decode(service.encode("testuser"))

        assert decoded.exp - decoded.iat == pytest.approx(5 * 60, abs=1)

    def test_decode_rejects_a_token_whose_iat_is_in_the_future(
        self, token_service: JwtTokenService
    ):
        not_yet_valid = jwt.encode(
            {
                "exp": (datetime.now() + timedelta(days=1)).timestamp(),
                "iat": (datetime.now() + timedelta(hours=1)).timestamp(),
                "sub": "testuser",
            },
            JWT_SECRET,
            algorithm=ALGORITHM,
        )

        with pytest.raises(InvalidTokenError, match="Invalid token"):
            token_service.decode(not_yet_valid)
