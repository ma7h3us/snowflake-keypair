import argparse
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from snowflake.core import Root
from snowflake.core.user import User
from snowflake.snowpark import Session
from pathlib import Path


# functions
def save_file(filename, content):  
   f = open(filename, "wb")  
   f.write(content) 
   f.close() 

# initialize argparser
parser = argparse.ArgumentParser()
parser.add_argument('user', help="user name")
args = parser.parse_args()

# connect to Snowflake
session = Session.builder.config("connection_name", "default").create()
root = Root(session)

# check if user exists
try: 
    user = root.users[args.user].fetch()
except:
    user = None

# create private-keys directory
Path("./private-keys").mkdir(parents=True, exist_ok=True)
    
# generate private key
private_key = rsa.generate_private_key(  
    public_exponent=65537,  
    key_size=2048,  
    backend=default_backend()  
)  

private_pem = private_key.private_bytes(  
    encoding=serialization.Encoding.PEM,  
    format=serialization.PrivateFormat.PKCS8,  
    encryption_algorithm=serialization.NoEncryption()  
)  

# generate public key
public_key = private_key.public_key()  
public_pem = public_key.public_bytes(  
    encoding=serialization.Encoding.PEM,  
    format=serialization.PublicFormat.SubjectPublicKeyInfo  
)
public_pem = public_pem.decode()
public_pem = public_pem[public_pem.find('\n')+1:public_pem[:-1].rfind('\n')]

# if user exists, assign public key and save private key file to disk
if user:
    user.rsa_public_key = public_pem
    root.users[args.user].create_or_alter(user)

# if user doesn't exist, create user with some details, assign public key and save private key file to disk
else:
    print(f"Creating user {args.user}")
    new_user = User(name=args.user)
    new_user.first_name = input("First Name: ")
    new_user.last_name = input("Last Name: ")
    new_user.display_name = f'{new_user.first_name} {new_user.last_name}'
    new_user.rsa_public_key = public_pem
    root.users.create(new_user)

# save private key to file
save_file(f'./private-keys/{args.user}.p8',private_pem)

# close session
session.close()