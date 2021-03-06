#!/usr/bin/python

# TODO : need to protect from overwriting password entries if creating new one
# TODO : spam protection needed!
# TODO : store history
# TODO : protection from evil admin

import sys, getopt, traceback
import yaml

def encrypt(key, string, cipher):
    if cipher == None:
        return string
    elif cipher == "RSA":
        from Crypto.PublicKey import RSA
        k = RSA.importKey(key)
        return k.encrypt(string, "K") # K is useless parameter
    else:
        print "ERROR : cipher unknown"

def decrypt(key, string, cipher):
    if cipher == None:
        return string
    elif cipher == "RSA":
        from Crypto.PublicKey import RSA
        k = RSA.importKey(key)
        return k.decrypt(string)
    else:
        print "ERROR : cipher unknown"

class storage:
    def __init__(self, path = ""):
        self.path = path

    def _get_data(self):
        open(self.path, "a")
        data = yaml.load(open(self.path))
        if data == None or len(data) == 0:
            data ={}
        return data

    def _save_data(self, data):
        f=open(self.path, "w")
        f.write(yaml.dump(data))
        f.close()

    def get_one(self, key):
        data = self._get_data()
        return data[key]

    def store_one(self, key, value):        
        
        data = self._get_data()
        data.update({key : value})
        self._save_data(data)

    def get_all_keys(self):
        data = self._get_data()
        return data.keys()

class server_side:
    """
    Data is curently stored in key-value style :
    (username, password_description, cipher, key) is key
    encrypted password is value
    """

    def __init__(self, storage=None, ):
        if storage == None:
            print "internal storage not implemented yet"
        self.storage = storage

    def _store_one(self, key, value):
        return self.storage.store_one(key, value)

    def get_one(self, key):
        return self.storage.get_one(key)

    def get_all_keys_by_request(self, request):
        all_keys = self.storage.get_all_keys()
        # (username, password_description, cipher, key)
        return filter(lambda x : x[1] == request, all_keys)

    def get_all_compound_keys(self):
        all_keys = self.storage.get_all_keys()
        return all_keys

class client_side(object):
    # (username, password_description, cipher, key)
    def __init__(self, name="example.client", cipher=None, key=None, server=None):
        self.name = name
        self.cipher = cipher
        if cipher in ["RSA", ]: # if we need to construct public key
            private_key = RSA.importKey(key)
            self._decryption_key = key
            self.encryption_key = private_key.publickey().exportKey()
        else: # for symmetryc and dummy keys. probably only for debug
            self.encryption_key = key
            self._decryption_key = key
        self.server = server

    def get_password(self, request):
        compound_key = (self.name, request, self.cipher, self.encryption_key)
        encrypted_password = self.server.get_one(compound_key)
        return decrypt(self._decryption_key, encrypted_password, self.cipher)

    def _set_password_simple(self, request, new_password):
        compound_key = (self.name, request, self.cipher, self.encryption_key)
        encrypted_password = encrypt(self.encryption_key, new_password, self.cipher)
        return server._store_one(compound_key, encrypted_password)

    # FIXME! Must protect from creating duplicate password names
    def update_password(self, request, new_password):
        all_keys_by_request = self.server.get_all_keys_by_request(request)
        if (self.name, request, self.cipher, self.encryption_key) not in all_keys_by_request:
            all_keys_by_request.append(tuple([self.name, request, self.cipher, self.encryption_key]))
        for compound_key in all_keys_by_request:
            encryption_key = compound_key[3]
            cipher = compound_key[2]
            encrypted_password = encrypt(encryption_key, new_password, cipher)
            self.server._store_one(compound_key, encrypted_password)

    def get_my_password_names(self):
        my_password_names = map(
                                lambda x : x[1],
                                filter(lambda x : x[0] == self.name, server.get_all_compound_keys())
                            )
        return my_password_names

    def get_all_users(self):
        all_compound_keys = server.get_all_compound_keys()
        all_users = []
        for compound_key in all_compound_keys:
            if compound_key[0] not in all_users:
                all_users.append(compound_key[0])
        return all_users

    def grant_password(self, newuser, password_id):
        compound_key = None
        try:
            candidate_compound_key =  filter(lambda x : x[0] == newuser, server.get_all_compound_keys())[0]
            candidate_compound_key[1] = password_id
            compound_key = tuple(candidate_compound_key)
        except:
            print "Can't get such user"

        # FIXME : need better encrypt/decrypt interface
        # e.g. class that takes a pair (cipher, key) and does all dirty work
        encrypted_password = ""
        if compound_key[2] == "RSA":
            encryption_key = RSA.importKey(compound_key[3])
            encrypted_password = encrypt(encryption_key, "RSA", self.get_password(password_id))
        elif compound_key[2] == "None":
            encrypted_password = self.get_password(password_id)
        else:
            print "Can't grant password : unsuported cipher"
            return None

        server._store_one(compound_key)

    def touch(self):
        pass

def print_help():
    print """
        Usage:
        pwdtool.py OPTIONS
        -h : print help and exit.
        -c, --cconf= : path to client config
        -s, --sconf= : path to server config
        -d : generate default configs and exit
        -a --action= : action to perform

        actions can be
          update_password (2 args : id and new value)
          get_password (1 arg : id of a pasword that we want to get)
          get_all_users
          get_my_password_names
          grant_password
    """

def parse_args(argv):
    try:
        opts, args = getopt.getopt(argv,"hdc:s:a:",["cconf=","sconf=","action="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    
    return [opts, args] 

if __name__ == "__main__":

    ### Test the storage engine!
    #
    s = storage("/tmp/111")
    s.store_one("test_key", "test_value")
    if s.get_one("test_key") != "test_value":
        print "ASSERT ERROR : problems in storage engine"
        sys.exit(10)

    ### FIXME : need refactoring!
    #
    (args, opt) = parse_args(sys.argv[1:])
    # print args, opt
    env = {}
    for arg in args:
        env.update({arg[0] : arg[1]})
    if "-h" in env.keys():
        print_help()
        exit(0)

    from default_config import *

    if "-c" in env.keys():
        client_config_path = env["-c"]
    if "-s" in env.keys():
        server_config_path = env["-s"]
    #
    # if we want just to print default configs, do it and exit!
    #
    if "-d" in env.keys():
        if "-c" in env.keys():
            open(client_config_path+".example", "w").write(yaml.dump(client_config))
        if "-s" in env.keys():
            open(server_config_path+".example", "w").write(yaml.dump(server_config))
        sys.exit(0)
    #
    # if client or server config defined, load it!
    #
    if "-c" in env.keys():
        client_config = yaml.load(open(client_config_path,"r"))
    if "-s" in env.keys():
        server_config = yaml.load(open(server_config_path,"r"))

    #
    # create server
    #
    server = server_side(storage(server_config["storage_path"]))
    # and client
    client_config.update({"server" : server})
    client = client_side(**client_config)

    if "-a" in env.keys():
        action = env["-a"]
        params = opt

        # FIXME!!! Must be a normal dispatching handler
        if action == "update_password" :
            try:
                client.update_password(*params)
            except:
                print "FIXME!!! Some error"
                traceback.print_exc(file=sys.stdout)
                sys.exit(100)            
            sys.exit(0)
        elif action == "get_password" :
            try:
                print client.get_password(*params)
            except:
                print "FIXME!!! Some error"
                traceback.print_exc(file=sys.stdout)
                sys.exit(100)
            sys.exit(0)
        elif action == "get_my_password_names" :
            try:
                print client.get_my_password_names(*params)
            except:
                print "FIXME!!! Some error"
                traceback.print_exc(file=sys.stdout)
                sys.exit(100)
            sys.exit(0)
        elif action == "get_all_users" :
            try:
                print client.get_all_users(*params)
            except:
                print "FIXME!!! Some error"
                sys.exit(100)
            sys.exit(0)
        elif action == "grant_password" :
            try:
                print client.grant_password(*params)
            except:
                print "FIXME!!! Some error"
                traceback.print_exc(file=sys.stdout)
                sys.exit(100)
            sys.exit(0)
        else :
            print "Not implemented"
