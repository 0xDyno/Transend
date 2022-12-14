from datetime import datetime
import webbrowser

from config import texts
from config.settings import chain_explorers, chain_default_coin, chain_name, tx_slash, address_length
from web3 import Web3


class Wallet:
    def __init__(self, private_key, label=None):
        """
        Pay attention to addr and addr_lower. First one with big letters, it should be used to print and
        send TXs. Second one is used to work with object, compare, search in sets, find etc..
        """
        self._key = private_key
        self.label = label

        self.nonce = int()
        self.addr = str()               # - use to print / send TXs (checkSum)
        self.addr_lower = str()         # - use to compare / find
        self.balance_in_wei = int()
        self.txs = list()               # list with Transaction objects

    def __str__(self):
        format_ = "%s. %s (balance: %.4f ETH)"
        return format_ % (self.label, self.addr, self.get_eth_balance())

    def __repr__(self):
        return f"{id(self)} - Wallet obj - addr {self.addr}"

    def get_all_info(self):
        line = self.__str__()           # all info
        if self.txs:                    # + all transactions if there are
            line += " | TXs:"
            for tx in self.txs:
                line += "\n - " + self.get_transaction_info(tx)
            # line += "\n"
        else:
            line += " | no tx"

        return line

    def key(self):
        return self._key

    def get_eth_balance(self):
        return Web3.fromWei(self.balance_in_wei, "ether")

    def print_transactions(self):
        for tx in self.txs:
            print(self.get_transaction_info(tx))

    def get_transaction_info(self, tx):
        tx_type = tx.get_tx_type(self)      # get type Received or Sent
        tx_time = tx.get_time()             # get date

        if tx_type == texts.tx_received:     # self - is receiver or sender?
            sender_or_receiver = "from " + tx.sender
        else:
            sender_or_receiver = "to " + tx.receiver
        link = chain_explorers[tx.chain_id] + tx_slash + tx.tx      # get explorer + tx = link
        blockchain = chain_name[tx.chain_id]

        format_ = "({blockchain}) {status}: {tx_type} {value} {token} {sender_or_receiver} on {date} ({link})"

        return format_.format(blockchain=blockchain, tx_type=tx_type, value=tx.get_eth_value(), token=tx.symbol,
                              sender_or_receiver=sender_or_receiver, date=tx_time, status=tx.status, link=link)


class Transaction:
    def __init__(self, chain_id: int, time: float, receiver: Wallet,
                 sender: Wallet, value: str, tx: str, token=None, sc_addr: str = None):
        """
        :param chain_id: chain_id
        :param time: usual time is secs
        :param receiver: addr str
        :param sender: addr str
        :param value: sent amount
        :param tx: tx_hash text
        :param token: Ticker of smart-contract, None if default network (ETH, BNB, MATIC etc)
        :param sc_addr: smart contract address for ERC-20
        """
        if token is None:
            self.symbol = chain_default_coin[chain_id]
        else:
            self.symbol = token
            if sc_addr is None or not sc_addr.startswith("0x") or len(sc_addr) != address_length:
                raise TypeError("Can't create TX, wrong Smart-Contract Address: ", sc_addr)
            self.address = sc_addr

        self.chain_id = chain_id                        #_1
        self.date = datetime.fromtimestamp(time)        #_2 -- datetime
        self.status = None                              #_3 -- Success / Fail / None
        self.receiver = receiver.addr                   #_4 to
        self.sender = sender.addr                       #_5 from
        self.value = value                              #_6 value
        self.tx = tx                                    #_7 transaction hash
        receiver.txs.append(self)
        sender.txs.append(self)

    def __str__(self):
        return chain_name[self.chain_id] + " >> " + self.str_no_bc()

    def str_no_bc(self):
        """Returns text with no BlockChain info"""
        string = "From {sender} sent {amount} {token} to {receiver} on {date}\n\t\t{status}, link: {link}"
        link = chain_explorers[self.chain_id] + tx_slash + self.tx
        return string.format(sender=self.sender, amount=Web3.fromWei(self.value, "ether"), token=self.symbol,
                             receiver=self.receiver, date=self.get_time(), status=self.status, link=link)

    def get_eth_value(self):
        return Web3.fromWei(self.value, "ether")

    def get_tx_type(self, wallet: Wallet):
        """Returns the wallet is sender or receiver"""
        if self.receiver == wallet.addr:
            return texts.tx_received
        else:
            return texts.tx_sent

    def get_time(self):
        return str(datetime.strftime(self.date, "%d.%m.%Y %H:%M:%S"))

    def open_explorer(self):
        webbrowser.open(chain_explorers[self.chain_id] + self.tx)


class Token:
    def __init__(self, chain_id: int, sc_addr: str, symbol: str, decimal: int, abi):
        if sc_addr is None or not sc_addr.startswith("0x") or len(sc_addr) != address_length:
            raise TypeError("Can't create TX, wrong Smart-Contract Address: ", sc_addr)
        self.chain_id = chain_id
        self.sc_addr = sc_addr
        self.symbol = symbol
        self.decimal = decimal
        self.abi = abi

    def __str__(self):
        chain = chain_default_coin[self.chain_id]
        format_ = "({chain}) {sym} - {addr} - {dec}"
        return format_.format(chain, self.symbol, self.sc_addr, self.decimal)