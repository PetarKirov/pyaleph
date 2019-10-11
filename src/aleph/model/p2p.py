"""
"""

from aleph.model.base import BaseClass
from pymongo import ASCENDING, DESCENDING, IndexModel
from datetime import datetime

class Peer(BaseClass):
    """Holds information about the chains state."""
    COLLECTION = "peers"

    INDEXES = [IndexModel([("type", ASCENDING)]),
               IndexModel([("address", ASCENDING)], unique=True),
               IndexModel([("last_seen", DESCENDING)])]
    
async def get_peers(peer_type=None):
    """ Returns current peers.
    TODO: handle the last seen, channel preferences, and better way of avoiding "bad contacts".
    NOTE: Currently used in jobs.
    """
    async for peer in Peer.collection.find({'type': peer_type}):
        yield peer['address']

async def add_peer(address, peer_type):
    Peer.collection.replace_one({
        'address': address,
        'type': peer_type
    }, {
        'address': address,
        'type': peer_type,
        'last_seen': datetime.now()
    }, upsert=True)