from smartcard.CardRequest import CardRequest
from smartcard.util import toHexString


GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]  # PC/SC: GET DATA (UID/IDm)


def read_one_uid(timeout: int = 3) -> str | None:
    """Read a single NFC tag UID via PC/SC.

    Returns uppercase hex string with no spaces or None on timeout.
    """
    try:
        cs = CardRequest(timeout=timeout, newcardonly=True).waitforcard()
        if cs is None:
            return None
        cs.connection.connect()
        data, sw1, sw2 = cs.connection.transmit(GET_UID)
        cs.connection.disconnect()
        if ((sw1 << 8) | sw2) == 0x9000 and data:
            return toHexString(data).replace(" ", "")
    except Exception as e:
        # Expected timeouts shouldn't spam logs
        if "Time-out" not in str(e) and "Command timeout" not in str(e):
            print(f"スキャンエラー: {e}")
    return None

