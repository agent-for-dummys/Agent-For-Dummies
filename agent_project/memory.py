import json
import sqlite3


class Memory:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        self.connection.execute("CREATE TABLE IF NOT EXISTS memories(namespace TEXT, key TEXT, value TEXT, PRIMARY KEY(namespace,key))")

    def put(self, namespace, key, value):
        with self.connection:
            self.connection.execute("INSERT INTO memories VALUES(?,?,?) ON CONFLICT(namespace,key) DO UPDATE SET value=excluded.value",
                                    (namespace, key, json.dumps(value, ensure_ascii=False)))

    def get(self, namespace, key):
        row = self.connection.execute("SELECT value FROM memories WHERE namespace=? AND key=?", (namespace, key)).fetchone()
        return json.loads(row[0]) if row else None

    def close(self):
        self.connection.close()
