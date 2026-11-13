import eventlet
import gc
import threading
eventlet.monkey_patch()

rlock_type = type(threading.RLock())
gc.collect()
locks = [o for o in gc.get_objects() if isinstance(o, rlock_type)]
print("Found %d RLocks" % len(locks))
for l in locks:
    print(l)
    import gc
    for ref in gc.get_referrers(l):
        try:
            print("  Referrer: %s" % str(ref)[:200])
        except:
            pass
