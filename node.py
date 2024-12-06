from argparse import ArgumentParser
from threading import Thread
import json
import socketserver

from helper.blockchain import Blockchain
from helper.consensus import ConsensusAlgorithm
from helper.network import recv_prefixed, send_prefixed

HOST = '0.0.0.0'

def process_msg(message: str):
    try:
        msg_dict = json.loads(message)
    except:
        return None
    
    type = msg_dict.get("type")
    if not (type and type in ["transaction", "values"] and "payload" in msg_dict):
        return None
    return msg_dict

class MyTCPServer(socketserver.ThreadingTCPServer):
	def __init__(self, node, server_address, RequestHandlerClass, bind_and_activate=True):
		self.node = node
		super().__init__(server_address, RequestHandlerClass, bind_and_activate)

class MyTCPHandler(socketserver.BaseRequestHandler):
	server: MyTCPServer

	def handle(self):
		node_ip = self.client_address[0]
		
		while True:
			try:
				data = recv_prefixed(self.request).decode()
			except Exception as e:
				# print(e.with_traceback(None))
				break
			
			if data_dict := process_msg(data):
				
				if data_dict['type'] == "transaction":
					txn = json.dumps(data_dict['payload'])
					print(f"[NET] Received a transaction from node {node_ip}: {txn}")

					txn_validity = self.server.node.process_transaction(txn)
					send_prefixed(self.request, json.dumps({"response": txn_validity}).encode())

				else:
					idx = data_dict['payload']
					print(f"[BLOCK] Received a block request from node {node_ip}: {idx}")

					block_list = self.server.node.process_block_request(idx)
					
					send_prefixed(self.request, json.dumps(block_list).encode())
			
			else:
				print(f"[NET] Received an invalid message from {node_ip}: {data}")

		
		#print("we exited the handler\n")


class Node:
	""" Class for BlockChain Node """

	def __init__(self, port, node_addresses):
		self.blockchain = Blockchain()
		self.server = MyTCPServer(self, (HOST, port), MyTCPHandler)
		self.consensus_algo = ConsensusAlgorithm(node_addresses, self.blockchain)

	def process_block_request(self, idx: int) -> list:
		with self.consensus_algo.consensus_cond:
			self.consensus_algo.consensus_todo = max(self.consensus_algo.consensus_todo, idx)

			if idx < self.blockchain.length():
				return [self.blockchain.get_block(idx)]
			
			elif idx == self.blockchain.length():
				if self.consensus_algo.current_idx < idx: # consensus pending
					new_block = self.blockchain.propose_block()
					self.consensus_algo.consensus_set[new_block['current_hash']] = new_block

					self.consensus_algo.consensus_cond.notify()
					return [new_block]
				
				else:
					return list(self.consensus_algo.consensus_set.values())

			else:
				return []
			
	def process_transaction(self, txn: str) -> bool:
		with self.consensus_algo.consensus_cond:
			if self.blockchain.add_transaction(txn):
				self.consensus_algo.consensus_cond.notify()
				return True
			return False

	def run(self):
		Thread(target=self.server.serve_forever).start()
		self.consensus_algo.run()


def parse_node_list(file_path: str):
	addresses = []
	with open(file_path) as f:
		for line in f:
			data = line.strip().split(':')
			ip, port = data[0], int(data[1])
			addresses.append((ip, port))
	return addresses

if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument('port', metavar='<Port-Server>', type=int)
	parser.add_argument('node_file', metavar='<Node-List>', type=str)
	args = parser.parse_args()

	node_addresses = parse_node_list(args.node_file)

	blockchain_node = Node(args.port, node_addresses)
	blockchain_node.run()