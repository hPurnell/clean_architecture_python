from datetime import datetime, timedelta

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
