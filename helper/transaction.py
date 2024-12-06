# from cryptography.exceptions import InvalidSignature
import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519
from enum import Enum
import json
import re

TransactionValidationError = Enum('TransactionValidationError', ['INVALID_JSON', 'INVALID_SENDER', 'INVALID_MESSAGE', 'INVALID_NONCE', 'INVALID_SIGNATURE'])

valid_sender_re = re.compile('^[a-fA-F0-9]{64}$')

def make_transaction(sender, message, nonce, signature) -> str:
    return json.dumps({'type': 'transaction', 'payload': {'sender': sender, 'nonce': nonce, 'message': message, 'signature': signature}})

def make_signature(private_key: ed25519.Ed25519PrivateKey, message: str, nonce: int) -> str:
    transaction = {'sender': private_key.public_key().public_bytes_raw().hex(), 'nonce': nonce, 'message': message}
    return private_key.sign(transaction_bytes(transaction)).hex()

def transaction_bytes(txn: dict) -> bytes:
    return json.dumps({k: txn[k] for k in ['sender', 'nonce', 'message']}, sort_keys=True).encode()

def validate_sender(sender):
    if sender and isinstance(sender, str) and valid_sender_re.search(sender):
        return sender
    return None

def validate_message(message):
    if message and isinstance(message, str):
        return message
    return None

def validate_nonce(nonce, sender, sender_nonce_map):
    if isinstance(nonce, int) and nonce > sender_nonce_map.get(sender, -1):
        return nonce
    return None

def validate_transaction(transaction: str, sender_map: dict) -> dict | TransactionValidationError:
    """ Main validation function for transaction """
    
    try:
        txn = json.loads(transaction)
    except json.JSONDecodeError:
        return TransactionValidationError.INVALID_JSON

    if not (sender := validate_sender(txn.get('sender'))):
        return TransactionValidationError.INVALID_SENDER

    if not validate_message(txn.get('message')):
        return TransactionValidationError.INVALID_MESSAGE
    
    if not isinstance(nonce := validate_nonce(txn.get('nonce'), sender, sender_map), int):
        return TransactionValidationError.INVALID_NONCE

    public_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(sender))
    try:
        public_key.verify(bytes.fromhex(txn.get('signature')), transaction_bytes(txn))
    except:
        return TransactionValidationError.INVALID_SIGNATURE

    sender_map[sender] = nonce
    return txn
