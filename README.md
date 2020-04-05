# bplist-python
Apple binary Property List reader/writer for Python

## Simple parsing

    from bplist import BPlistReader
    
    with open('file.bplist', 'rb') as fp:
        reader = BPListReader(fp.read())
        parsed = reader.parse()
        
        # Now 'parsed' is a dictionary of values.
        
       
## even simpler run
python3 -m bplist [file_path]
(auto-outputs file_path+".json")