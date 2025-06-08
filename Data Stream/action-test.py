print("this is hello from .py using github action")
import os
token = os.getenv("TOKEN")
print(type(token))
print(os.getenv("TOKEN"))