import json
from threading import Condition, Thread
import socket

from helper.blockchain import Blockchain
from helper.network import recv_prefixed, send_prefixed

import time

class ConsensusAlgorithm:
	def __init__(self, node_addresses: list, blockchain: Blockchain):
		self.node_addresses = node_addresses
		self.blockchain = blockchain

		self.counter_cond = Condition()
		self.node_count = len(node_addresses)  # 1 less than the number of nodes in network
		self.f = self.node_count // 2  # maximum number of failures
		self.responses_count = 0

		self.consensus_cond = Condition()
		self.consensus_set = dict()
		self.consensus_todo = 0
		self.current_idx = 0

		self.block_req_cond = Condition()
		self.client_flags = [True] * self.node_count


	def init(self):
		for idx, address in enumerate(self.node_addresses):
			Thread(target=self.client, args=(idx, address)).start()

		with self.counter_cond:
			while not self.all_responses_received():
				self.counter_cond.wait()
			print("[NET] All nodes have been connected to.")

	def reset_client_flags(self):
		for i in range(len(self.client_flags)):
			self.client_flags[i] = False

	def run(self):
		self.init()

		while True:
			with self.consensus_cond:
				while self.blockchain.txn_pool_size() == 0 and self.consensus_todo < self.blockchain.length():
					self.consensus_cond.wait()
				self.current_idx = self.blockchain.length()

				if not self.consensus_set and self.blockchain.txn_pool_size() != 0:
					block = self.blockchain.propose_block()
					self.consensus_set[block['current_hash']] = block
					print(f"[PROPOSAL] Created a block proposal: {json.dumps(block)}")

				self.consensus_todo = max(self.consensus_todo, self.blockchain.length())

			for _ in range(self.f + 1):
				# start client threads
				with self.block_req_cond:
					self.responses_count = 0
					self.reset_client_flags()
					self.block_req_cond.notify_all()

				# wait for client threads
				with self.counter_cond:					
					while not self.all_responses_received():
						self.counter_cond.wait()
			
			with self.consensus_cond:
				chosen = None
				for hash, block in self.consensus_set.items():
					if len(block['transactions']) > 0 and (not chosen or hash < chosen):
						chosen = block
				
				self.blockchain.add_block(chosen)
				self.consensus_set = dict()


	def all_responses_received(self):
		if self.responses_count == self.node_count:
			return True
		return False

	def increment_response_count(self):
		with self.counter_cond:
			self.responses_count += 1

			if self.all_responses_received():
				self.counter_cond.notify()

	def decrement_node_count(self):
		with self.counter_cond:
			self.node_count -= 1

			if self.all_responses_received:
				self.counter_cond.notify()


	def client(self, idx, address):

		first_connection = True
		consec_failures = 0

		while first_connection or consec_failures < 2:
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
				try:
					s.connect(address)
					if first_connection:
						self.increment_response_count()
						first_connection = False

				except Exception as e:
					if not first_connection:
						consec_failures += 1
					else:
						time.sleep(2)
					continue
					
				s.settimeout(5)
				while True:
					with self.block_req_cond:
						while self.client_flags[idx]:
							self.block_req_cond.wait()

					msg = json.dumps({"type": "values", "payload": self.current_idx}).encode()
					try:
						send_prefixed(s, msg)
						block_set_json = recv_prefixed(s).decode()
					except Exception as e:
						# print(e.with_traceback(None))
						consec_failures += 1
						break
					
					consensus_blocks = json.loads(block_set_json)
					with self.consensus_cond:
						for block in consensus_blocks:
							self.consensus_set[block['current_hash']] = block

					self.client_flags[idx] = True
					self.increment_response_count()
					consec_failures = 0

		# Removing node in the case of node failure		
		self.decrement_node_count()
