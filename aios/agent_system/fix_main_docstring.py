with open('low_success_regeneration.py', 'rb') as f:
    content = f.read()

old = b'def main():\r\n    """\xe6\xb6\x93\xe8\xaf\xb2\xe5\x9a\xb1\xe9\x8f\x81\xe5\xb8\xae\xe7\xb4\x99\xe9\x90\xa2\xe3\x84\xa4\xe7\xb0\xac\xe5\xa8\xb4\xe5\xac\xad\xe7\x98\xaf\xe9\x94\x9b?""\r\n'
new = b'def main():\r\n    """main function"""\r\n'

if old in content:
    content = content.replace(old, new)
    with open('low_success_regeneration.py', 'wb') as f:
        f.write(content)
    print('Fixed!')
else:
    print('Pattern not found')
    idx = content.find(b'def main():')
    print('Bytes at def main():', content[idx:idx+100])
