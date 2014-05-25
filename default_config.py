#!/usr/bin/python

#
# default config, hardcoded
#

client_config_path = "/etc/passwdb.client.conf"
server_config_path = "/etc/passwdb.client.conf"

server_config = { "storage_path" : "/tmp/111", }

from Crypto.PublicKey import RSA
key = RSA.generate(2048)
client_config = { "name" : "user@example.client",
                      "cipher" : "RSA",
                      "key" : key.exportKey() }
