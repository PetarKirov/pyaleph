from aleph.storage import get_json, pin_add
from aleph.model.messages import Message

import logging
LOGGER = logging.getLogger('chains.common')



async def get_verification_buffer(message):
    """ Returns a serialized string to verify the message integrity (this is was it signed)
    """
    return '{chain}\n{sender}\n{type}\n{item_hash}'.format(**message)

async def mark_confirmed(chain_name, object_hash, height):
    """ Mark a particular hash as confirmed in underlying chain.
    """
    pass

async def incoming(chain_name, message, tx_hash, height):
    """ New incoming message from underlying chain.
    Will be marked as confirmed if existing in database, created if not.
    """
    hash = message['item_hash']
    message['chain'] = message.get('chain', chain_name) # we set the incoming chain as default for signature
    try:
        content = await get_json(hash)
    except Exception as exc:
        LOGGER.exception("Can't get content of object %r" % hash)
        return

    if content.get('address', None) is None:
        content['address'] = message['sender']

    if content.get('time', None) is None:
        content['time'] = message['time']

    # for now, only support direct signature (no 3rd party or multiple address signing)
    if message['sender'] != content['address']:
        LOGGER.warn("Invalid sender for %s" % hash)
        return

    # since it's on-chain, we need to keep that content.
    # TODO: verify signature before (in chain-specific stage?)
    await pin_add(hash)

    # TODO: verify if search key is ok... do we need an unique key for messages?
    existing = Message.collection.find_one({
        'item_hash': hash,
        'chain': message['chain'],
        'sender': message['sender'],
        'type': message['type']
    })
    new_values = {
        'confirmed': True,
        'confirmations': [ # TODO: we should add the current one there
                           # and not replace it.
            {'chain': chain_name,
             'height': height,
             'hash': tx_hash}
    ]}
    if existing:
        Message.collection.update_one({
            'item_hash': hash,
            'chain': chain_name
        }, {
            '$set': new_values
        })
    else:
        LOGGER.info("New message to store.")
        message.update(new_values)
        await Message.collection.insert(message)



async def invalidate(chain_name, block_height):
    """ Invalidates a particular block height from an underlying chain (in case of forks)
    """
    pass
