import hashlib
import json
from threading import Lock
from helper.transaction import validate_transaction, TransactionValidationError

def print_txn_error(error: TransactionValidationError, transaction: str):
    match error:
        case TransactionValidationError.INVALID_JSON:
            err_field = "format"
        case TransactionValidationError.INVALID_SENDER:
            err_field = "sender"
        case TransactionValidationError.INVALID_MESSAGE:
            err_field = "message"
        case TransactionValidationError.INVALID_NONCE:
            err_field = "nonce"
        case TransactionValidationError.INVALID_SIGNATURE:
            err_field = "signature"

    print(f"[TX] Received an invalid transaction, invalid {err_field} - {transaction}")

class Blockchain():
	def  __init__(self):
		self.lock = Lock()
		self.blockchain = []
		self.txn_pool = []
		self.nonce_map = dict()

		genesis_block = self.propose_block(previous_hash='0' * 64)
		self.blockchain.append(genesis_block)

	def propose_block(self, previous_hash=None) -> dict:
		with self.lock:
			block = {
				'index': len(self.blockchain),
				'transactions': self.txn_pool.copy(),
				'previous_hash': previous_hash or self.blockchain[-1]['current_hash'],
			}
		block['current_hash'] = self.calculate_hash(block)

		return block
	
	def add_block(self, block: dict):
		new_nonces = dict()
		for txn in block['transactions']:
			new_nonces[txn['sender']] = max(new_nonces.get(txn['sender'], 0), txn['nonce'])

		with self.lock:
			i = 0
			while i < len(self.txn_pool):
				if self.txn_pool[i]['nonce'] <= new_nonces.get(self.txn_pool[i]['sender'], -1):
					self.txn_pool.pop(i)
				else:
					i += 1

			for sender, nonce in new_nonces.items():
				self.nonce_map[sender] = max(self.nonce_map.get(sender, -1), nonce)

			self.blockchain.append(block)
		print(f"[CONSENSUS] Appended to the blockchain: {block['current_hash']}")

	def last_block(self):
		with self.lock:
			return self.blockchain[-1]

	def get_block(self, index):
		with self.lock:
			if index >= len(self.blockchain):
				raise RuntimeError("block index out-of-bounds")
			return self.blockchain[index]
	
	def length(self):
		with self.lock:
			return len(self.blockchain)
	
	def txn_pool_size(self):
		with self.lock:
			return len(self.txn_pool)

	def calculate_hash(self, block: dict) -> str:
		str_block = json.dumps({k: block.get(k) for k in ['index', 'transactions', 'previous_hash']}, sort_keys=True)
		byte_block = str_block.encode()
		hex_hash_block = hashlib.sha256(byte_block).hexdigest()

		return hex_hash_block

	def add_transaction(self, transaction: str) -> bool:
		with self.lock:
			valid = isinstance((txn := validate_transaction(transaction, self.nonce_map)), dict)
			if valid:
				self.txn_pool.append(txn)
		
		if valid:
			print(f"[MEM] Stored transaction in the transaction pool: {txn['signature']}")
			return True
		else:
			print_txn_error(txn, transaction)
		return False
