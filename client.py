import requests
import json

def parse_line(line):
    # Assuming the line is JSON formatted after 'data: ' prefix
    return json.loads(line.replace('data: ', ''))


def receive_stream():
    response = requests.get('http://localhost:5000/stream', stream=True)
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            data = parse_line(decoded_line)


if __name__ == '__main__':
    receive_stream()
