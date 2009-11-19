import struct

def unpack_int_struct(sz, s):
    if   sz == 1:
        ot = '!B'
    elif sz == 2:
        ot = '!h'
    elif sz == 4:
        ot = '!I'
    else:
        raise Exception('int unpack size '+str(sz)+' unsupported')
    return struct.unpack(ot, s)[0]

def unpack_int(data, offset):
    return unpack_int_meta(data, offset)[1]

def unpack_int_meta(data, offset):
    obj_header = struct.unpack('!B', data[offset])[0]
    obj_type, obj_info = (obj_header & 0xF0), (obj_header & 0x0F)
    int_sz = 2**obj_info
    return int_sz, unpack_int_struct(int_sz, data[offset+1:offset+1+int_sz])

def resolve_int_size(obj_info, data, offset):
    if obj_info == 0x0F:
        ofs, obj_count = unpack_int_meta(data, offset+1)
        objref = offset+2+ofs
    else:
        obj_count = obj_info
        objref = offset+1
    return obj_count, objref

def unpack_item(data, offset, objref_size):
    obj_header = struct.unpack('!B', data[offset])[0]
    obj_type, obj_info = (obj_header & 0xF0), (obj_header & 0x0F)
    if   obj_type == 0x00:
        if   obj_info == 0x00:
            return None
        elif obj_info == 0x08:
            return False
        elif obj_info == 0x09:
            return True
        elif obj_info == 0x0F:
            return None # this is really pad byte, FIXME
        else:
            raise Exception('unpack item type '+str(obj_header)+' at '+str(offset)+ 'failed')
    elif obj_type == 0x10:
        return unpack_int(data, offset)
    
    # ...
    
    elif obj_type == 0x50:
        obj_count, objref = resolve_int_size(obj_info, data, offset)
        return data[objref:objref+obj_count]
    # unicode str
    elif obj_type == 0xA0:
        obj_count, objref = resolve_int_size(obj_info, data, offset)
        arr = []
        for i in range(obj_count):
            arr.append(unpack_int_struct(objref_size, data[objref+i:objref+i+objref_size]))
        return arr
    elif obj_type == 0xD0:
        obj_count, objref = resolve_int_size(obj_info, data, offset)
        keys = []
        for i in range(obj_count):
            keys.append(unpack_int_struct(objref_size, data[objref+i:objref+i+objref_size]))
        values = []
        objref += obj_count*objref_size
        for i in range(obj_count):
            values.append(unpack_int_struct(objref_size, data[objref+i:objref+i+objref_size]))
        dic = {}
        for i in range(obj_count):
            dic[keys[i]] = values[i]
        return dic
    else:
        raise Exception('don\'t know how to unpack obj type '+str(obj_type))
    
def unpack(data):
    # read header
    if data[:8] != 'bplist00':
        raise Exception('Bad magic')
    
    # read trailer
    offset_size, object_ref_size, number_of_objects, top_object, table_offset = struct.unpack('!6xBB4xI4xI4xI', data[-32:])
    print "** plist offset_size:",offset_size,"objref_size:",object_ref_size,"num_objs:",number_of_objects,"top:",top_object,"table_ofs:",table_offset
    
    # read offset table
    offset_table = data[table_offset:-32]
    offsets = []
    for i in range(number_of_objects):
        offset_entry = offset_table[:offset_size]
        offset_table = offset_table[offset_size:]
        offsets.append(unpack_int_struct(offset_size, offset_entry))
    print "** plist offsets:",offsets
    
    # read object table
    objects = []
    for i in offsets:
        obj = unpack_item(data, i, object_ref_size)
        print "** plist unpacked",type(obj),obj,"at",i
        objects.append(obj)
    
    # rebuild object tree
    newTree = []
    for obj in objects:
        if type(obj) == list:
            newarr = []
            for i in obj:
                newarr.append(objects[i])
            newTree.append(newarr)
        if type(obj) == dict:
            newdic = {}
            for k,v in obj.iteritems():
                newdic[objects[k]] = objects[v]
            newTree.append(newdic)
        else:
            newTree.append(obj)
    
    # return root object
    return newTree[top_object]