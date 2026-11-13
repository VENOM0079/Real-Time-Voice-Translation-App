import eventlet

# Phase 1: Initialize eventlet WITHOUT patching threads
# This loads eventlet internals but avoids premature RLock usage
eventlet.monkey_patch(os=False, select=False, socket=False, thread=False, time=False)

import _thread
import eventlet.green.thread as gt

# Phase 2: Apply the Python 3.14 compatibility patch
print("Applying Python 3.14 patches...")
for attr in ['start_joinable_thread', '_shutdown', '_make_thread_handle', '_ThreadHandle', '_get_main_thread_ident']:
    if hasattr(_thread, attr) and not hasattr(gt, attr):
        setattr(gt, attr, getattr(_thread, attr))

# Phase 3: Final monkey patch (all=True is default)
print("Finalizing monkey patch...")
eventlet.monkey_patch()

print("Monkey patch SUCCESSFUL!")
import threading
print("RLock check: %s" % threading.RLock)
