import os
from fastmcp import FastMCP
import tempfile
#import aiosqlite
import random 
import json

#create a mcp server istance
mcp = FastMCP("Simple Server")





def main():
    print("Hello from expense-remote!")


if __name__ == "__main__":
    mcp.run(transport = "http",host = "0.0.0.0",port= 8000)
