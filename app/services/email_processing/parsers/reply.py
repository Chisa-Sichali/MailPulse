def is_reply(msg) -> bool:
    if msg.get("In-Reply-To"):
        return True

    if msg.get("References"):
        return True

    return False
