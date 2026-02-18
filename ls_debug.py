import os
print(f"CWD: {os.getcwd()}")
print("Listing CWD:")
print(os.listdir("."))
print("Walking tools/src/aden_tools/tools:")
for root, dirs, files in os.walk("tools/src/aden_tools/tools"):
    print(root, files)
