# Created from an example found here
# https://github.com/iyassou/mpyaes

import mpyaes

key = mpyaes.generate_key(32)
print("# The key and IV generated here can be copied to secrets.py")
print("key="+str(key))
print()

IV = mpyaes.generate_IV(16)
print("IV="+str(IV))
