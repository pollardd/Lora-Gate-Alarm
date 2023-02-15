# Standard calls to encryption and decryption

import constants
import debug
import secrets      # file containing key and IV values
import mpyaes       # Encryption module found here https://github.com/iyassou/mpyaes

DEBUG = constants.DEBUG
LOGTOFILE =  constants.LOGTOFILE

def encryptMessage(unencryptedMessage):
    if(DEBUG >=1):
        debug.debug(DEBUG, "encryptMessage()", " ", LOGTOFILE)

    if(DEBUG >=2):
        debug.debug(DEBUG, "encryptMessage(unencryptedMessage)", "unencryptedMessage="+ str(unencryptedMessage), LOGTOFILE)
    if(DEBUG >=1):
        debug.debug(DEBUG, "encryptMessage(unencryptedMessage)", "unencryptedMessage Length ="+ str(len(str(unencryptedMessage))), LOGTOFILE)

    key = secrets.key
    IV = secrets.IV
    aes = mpyaes.new(key, mpyaes.MODE_CBC, IV)
    encryptedMessage = aes.encrypt(unencryptedMessage)

    if(DEBUG >=3):
        debug.debug(DEBUG, "encryptMessage(unencryptedMessage)", "encryptedMessage="+ str(encryptedMessage), LOGTOFILE)
    if(DEBUG >=2):
        debug.debug(DEBUG, "encryptMessage(unencryptedMessage)", "encryptedMessage Length="+ str(len(str(encryptedMessage))), LOGTOFILE)

    return encryptedMessage

def decryptMessage(encryptedMessage):
    if(DEBUG >=1):
        debug.debug(DEBUG, "decryptMessage()", " ", LOGTOFILE)
    if(DEBUG >=2):
        debug.debug(DEBUG, "decryptMessage(encryptedMessage)", "encryptedMessage="+ str(encryptedMessage), LOGTOFILE)
    if(DEBUG >=1):
        debug.debug(DEBUG, "decryptMessage(encryptedMessage)", "encryptedMessage Length="+ str(len(str(encryptedMessage))), LOGTOFILE)

    key = secrets.key
    IV = secrets.IV
    aes = mpyaes.new(key, mpyaes.MODE_CBC, IV)
    unencryptedMessage = aes.decrypt(bytearray(encryptedMessage))
    if(DEBUG >=1):
        debug.debug(DEBUG, "decryptMessage(encryptedMessage)", "decrypted message="+ str(unencryptedMessage), LOGTOFILE)

    return unencryptedMessage
