import os
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def create_test_token(affiliate_id: int = 1, expires_days: int = 7) -> str:
    payload = {
        "id": affiliate_id,
        "exp": datetime.utcnow() + timedelta(days=expires_days),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


if __name__ == "__main__":
    test_token = create_test_token()
    print(f"Test token (id=1):\nBearer {test_token}")