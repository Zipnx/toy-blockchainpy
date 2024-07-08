#!./venv/bin/python3

import bson, json, sys

if __name__ == '__main__':
    data = sys.stdin.buffer.read()

    sys.stdout.write(json.dumps(bson.loads(data), indent = 4))


