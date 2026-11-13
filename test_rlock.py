import eventlet
# Patch everything EXCEPT threads first to avoid RLock issues
eventlet.monkey_patch(thread=False, threading=False)

import _thread
import eventlet.green.thread as gt

# Apply Python 3.14+ compatibility patch
print("Applying Python 3.14 patches to eventlet.green.thread...")
for attr in ['start_joinable_thread', '_shutdown', '_make_thread_handle', '_ThreadHandle', '_get_main_thread_ident']:
    if hasattr(_thread, attr) and not hasattr(gt, attr):
        setattr(gt, attr, getattr(_thread, attr))

# Now patch threads
print("Finalizing monkey patch...")
eventlet.monkey_patch(thread=True, threading=True)

print("Monkey patch complete!")
import threading
print("RLock check: %s" % threading.RLock)
