from typing import List
from schemas import Task


tasks_db: List[Task] = []

users_db = {
    "manav": {
        "username": "manav",
        "fullname": "Manav Sharma",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$MuzT/nDD7ms+XZWTlk/eaQ$OcvoASMa2SsyOybofi+j3a1K71ny5h4hNzux6BjAnoM",
    }
}
