import pickle
import bcrypt
from pathlib import Path

names = ['admins']
username = ['admin']
passwords = ['Testsvr$#604']

hashed_passwords = [bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode() for p in passwords]

file_path = Path(__file__).parent / "hashpswds.pkl"
with file_path.open("wb") as file:
    pickle.dump(hashed_passwords, file)

print("Hashed passwords saved to hashpswds.pkl")
