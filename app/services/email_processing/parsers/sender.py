def parse_sender(raw_sender: str) -> list[str]:
    if "<" in raw_sender and ">" in raw_sender:
        name = raw_sender.split("<")[0].strip().strip('"')
        address = raw_sender.split("<")[1].replace(">", "").strip()
        return [name, address]

    address = raw_sender.strip()
    return ["", address]
