from itsdangerous import URLSafeTimedSerializer
from keys import secret_key,salt
def token(email):
    serializer=URLSafeTimedSerializer(secret_key)
    return serializer.dumps(email,salt=salt)