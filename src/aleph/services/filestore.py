import rocksdb
import asyncio
import os
import multiprocessing
import threading

HASHES_STORAGE = 'hashes'
STORE_LOCK = threading.Lock()

hashes_db = None
import os
import logging

LOGGER = logging.getLogger('filestore')

def init_store(config):
    global hashes_db
    opts = rocksdb.Options()
    opts.create_if_missing = True
    opts.max_open_files = 300000
    opts.write_buffer_size = 67108864
    opts.max_write_buffer_number = 3
    opts.target_file_size_base = 67108864

    opts.table_factory = rocksdb.BlockBasedTableFactory(
        filter_policy=rocksdb.BloomFilterPolicy(10),
        block_cache=rocksdb.LRUCache(2 * (1024 ** 3)),
        block_cache_compressed=rocksdb.LRUCache(500 * (1024 ** 2)))

    hashes_db = rocksdb.DB(os.path.join(config.storage.folder.value, HASHES_STORAGE), opts)
    # print(os.getpid(), hashes_db)
    # hashes_db = rocksdb.DB(os.path.join(config.storage.folder.value, HASHES_STORAGE),
    #                        rocksdb.Options(create_if_missing=True))
    
def __get_value(key):
    try:
        with STORE_LOCK:
            return hashes_db.get(key)
    except Exception:
        LOGGER.exception("Can't get key %r" % key)
        return None
    
_get_value = __get_value

def __set_value(key, value):
    try:
        with STORE_LOCK:
            return hashes_db.put(key, value)
    except Exception:
        LOGGER.exception("Can't write key %r" % key)
        
_set_value = __set_value
    
async def get_value(key, in_executor=True):
    # print(os.getpid(), hashes_db)
    # if not isinstance(key, bytes):
    #     if isinstance(key, str):
    #         key = key.encode('utf-8')
    #     else:
    #         raise ValueError('Bad input key (bytes or string only)')    
    if in_executor:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_value, key.encode('utf-8'))
    else:
        return _get_value(key.encode('utf-8'))

async def set_value(key, value, in_executor=True):
    if not isinstance(key, bytes):
        if isinstance(key, str):
            key = key.encode('utf-8')
        else:
            raise ValueError('Bad input key (bytes or string only)')
        
    if not isinstance(value, bytes):
        if isinstance(value, str):
            value = value.encode('utf-8')
        else:
            raise ValueError('Bad input value (bytes or string only)')
    
    if in_executor:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _set_value, key, value)
    else:
        return _set_value(key, value)