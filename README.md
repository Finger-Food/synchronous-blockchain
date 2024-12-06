# Synchronous Crash Fault-Tolerant Blockchain

## Project Description

This project, started as part of a university assignment, implements a **peer-to-peer (P2P) blockchain system** in Python. It creates a distributed blockchain network where nodes communicate directly with each other to process transactions, propose blocks, and reach consensus. Each node operates as both a client and a server.

### Key Features

- **Multi-threaded TCP Server**: Nodes can handle multiple connections simultaneously.
- **Transaction Validation**: Ensures cryptographic security and proper sequencing.
- **Block Creation**: SHA-256 hashing and lexicographical sorting for integrity.
- **Consensus Protocol**: Synchronous, crash-fault tolerant algorithm that decides on the lexicographically 'lowest hash block' amongst proposals
- **Fault Tolerance**: Handles node failures during communication and consensus.

---

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd <project_directory>
   ```

2. Install dependencies if necessary:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a node discovery file for each node (e.g., `node-list.txt`) with each line containing an IP address and port of *other* nodes in the network in the format:
   ```
   <ip_address>:<port>
   ```
   Example:
   ```
   192.168.1.43:8888
   192.168.1.56:8888
   ```

---

## Running the Blockchain Node

1. Start each node in a different terminal or machine with:
   ```bash
   python node.py <server_port> <node_list_file>
   ```
   Example:
   ```bash
   python node.py 8888 node-list.txt
   ```

2. The node will:
   - Listen for incoming connections on the specified port.
   - Connect to other nodes specified in the `node-list.txt` file.
   - Handle transaction requests and block proposals.
   - Participate in the consensus process to append blocks to the blockchain.

---

## Testing the Blockchain

1. Open a node in 3 different terminals with node lists in the `ips/` folder in the format:
`python node.py 900X ips/ipX.txt` for `X = 1...3` each on separate terminals.
2. Insert transactions into the system via the tester file `node_tester` in another terminal:
    ```
   python node_tester.py --port 9000 9001 9002 --test Y
   ```
with `Y` in the range `[1..5]`

---

## How It Works

### Transaction Handling
- Nodes accept transactions in JSON format:
  ```json
  {
    "type": "transaction",
    "payload": {
      "sender": "<public_key>",
      "message": "<text_message>",
      "nonce": <integer>,
      "signature": "<digital_signature>"
    }
  }
  ```
- Transactions are validated based on:
  - Cryptographic signature verification.
  - Nonce sequencing.
  - Transaction uniqueness.

### Block Creation
- Blocks are created once valid transactions are collected.
- Block structure:
  ```json
  {
    "index": <block_number>,
    "transactions": [...],
    "previous_hash": "<hash_of_previous_block>",
    "current_hash": "<hash_of_this_block>"
  }
  ```

### Consensus Protocol
- Nodes exchange block proposals and decide on a block to append based on:
  - Lexicographical hash ordering.
  - Inclusion of transactions.
- The protocol is fault-tolerant to crash failures but it is not Byzantine fault-tolerant.

---

## Sample Outputs

- **Receiving Transactions**:
  ```
  [NET] Received a transaction: {"type": "transaction", "payload": {...}}
  [MEM] Stored transaction in the pool: <transaction_signature>
  ```

- **Creating a Block Proposal**:
  ```
  [PROPOSAL] Created a block proposal: {"index": 2, "transactions": [...], "current_hash": "...", "previous_hash": "..."}
  ```

- **Consensus Decision**:
  ```
  [CONSENSUS] Appended block to the blockchain: <current_hash>
  ```

---

## Notes

- **Genesis Block**: The blockchain starts with a predefined genesis block:
  ```json
  {
    "index": 1,
    "transactions": [],
    "previous_hash": "0000000000000000000000000000000000000000000000000000000000000000",
    "current_hash": "<genesis_block_hash>"
  }
  ```
- Ensure each transaction uses a unique and sequential nonce for proper validation.

---

## Future Improvements

- Implement advanced consensus protocols (e.g., Proof of Stake, Proof of Work).
- Add encryption for secure message exchanges.
- Extend the system to support more complex smart contracts.

---

### Aside

This README was created with extensive assistance from chatGPT. Really cool!