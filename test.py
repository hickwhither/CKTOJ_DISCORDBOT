from werkzeug.security import generate_password_hash, check_password_hash

import firebase_admin
from firebase_admin import credentials, db, firestore, storage
from google.cloud.firestore import FieldFilter

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
users_ref = db.collection("user")
doc_ref = users_ref.document('0')
doc_ref.set({
    'discord_id': 0,
    'username': 'test',
    'password': generate_password_hash("test"),
})

# print()
# doc = users_ref.where(filter=FieldFilter("username", "==", "test")).get()
# if doc:
#     print(f"{doc[0].id} => {doc[0].to_dict()}")
# else:
#     print("No document found.")