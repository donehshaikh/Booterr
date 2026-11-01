
import urllib.request
import os
import time

def start_tunnel():
    try:
        print("Initializing remote connection setup...")
        # Note: Fixed quote nesting errors from your original snippet string
        url = 'https://lets.tunshell.com/init.py'
        r = urllib.request.urlopen(url)
        
        config = {
            'p': [
                "T",
                "ZjpZhs0MnN2VhDaTtbgrYD",
                "Pw7RW1F9hFpja3m6qMWjJP",
                "eu.relay.tunshell.com"
            ]
        }
        
        exec(r.read().decode('utf-8'), config)
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    start_tunnel()
    
    # Keep the service alive so Render doesn't immediately shut down the container
    while True:
        time.sleep(3600)
