import struct

class BPlistReader(object):
    def __init__(self, s):
        self.data = s
    
    def __unpackIntStruct(self, sz, s):
        if   sz == 1:
            ot = '!B'
        elif sz == 2:
            ot = '!h'
        elif sz == 4:
            ot = '!I'
        else:
            raise Exception('int unpack size '+str(sz)+' unsupported')
        return struct.unpack(ot, s)[0]
    
    def __unpackInt(self, offset):
        return self.__unpackIntMeta(offset)[1]

    def __unpackIntMeta(self, offset):
        obj_header = struct.unpack('!B', self.data[offset])[0]
        obj_type, obj_info = (obj_header & 0xF0), (obj_header & 0x0F)
        int_sz = 2**obj_info
        return int_sz, self.__unpackIntStruct(int_sz, self.data[offset+1:offset+1+int_sz])

    def __resolveIntSize(self, obj_info, offset):
        if obj_info == 0x0F:
            ofs, obj_count = self.__unpackIntMeta(offset+1)
            objref = offset+2+ofs
        else:
            obj_count = obj_info
            objref = offset+1
        return obj_count, objref

    def __unpackItem(self, offset):
        obj_header = struct.unpack('!B', self.data[offset])[0]
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
            return self._unpackInt(offset)

        # ...

        elif obj_type == 0x50:
            obj_count, objref = self.__resolveIntSize(obj_info, offset)
            return self.data[objref:objref+obj_count]
        # unicode str
        elif obj_type == 0xA0:
            obj_count, objref = self.__resolveIntSize(obj_info, offset)
            arr = []
            for i in range(obj_count):
                arr.append(self.__unpackIntStruct(self.object_ref_size, self.data[objref+i:objref+i+self.object_ref_size]))
            return arr
        elif obj_type == 0xD0:
            obj_count, objref = self.__resolveIntSize(obj_info, offset)
            keys = []
            for i in range(obj_count):
                keys.append(self.__unpackIntStruct(self.object_ref_size, self.data[objref+i:objref+i+self.object_ref_size]))
            values = []
            objref += obj_count*self.object_ref_size
            for i in range(obj_count):
                values.append(self.__unpackIntStruct(self.object_ref_size, self.data[objref+i:objref+i+self.object_ref_size]))
            dic = {}
            for i in range(obj_count):
                dic[keys[i]] = values[i]
            return dic
        else:
            raise Exception('don\'t know how to unpack obj type '+str(obj_type))
    
    def parse(self):
        # read header
        if self.data[:8] != 'bplist00':
            raise Exception('Bad magic')
        
        # read trailer
        self.offset_size, self.object_ref_size, self.number_of_objects, self.top_object, self.table_offset = struct.unpack('!6xBB4xI4xI4xI', self.data[-32:])
        print "** plist offset_size:",self.offset_size,"objref_size:",self.object_ref_size,"num_objs:",self.number_of_objects,"top:",self.top_object,"table_ofs:",self.table_offset
        
        # read offset table
        self.offset_table = self.data[self.table_offset:-32]
        self.offsets = []
        ot = self.offset_table
        for i in range(self.number_of_objects):
            offset_entry = ot[:self.offset_size]
            ot = ot[self.offset_size:]
            self.offsets.append(self.__unpackIntStruct(self.offset_size, offset_entry))
        print "** plist offsets:",self.offsets
        
        # read object table
        self.objects = []
        for i in self.offsets:
            obj = self.__unpackItem(i)
            print "** plist unpacked",type(obj),obj,"at",i
            self.objects.append(obj)
        
        # rebuild object tree
        newTree = []
        for obj in self.objects:
            if type(obj) == list:
                newArr = []
                for i in obj:
                    newArr.append(self.objects[i])
                newTree.append(newArr)
            if type(obj) == dict:
                newDic = {}
                for k,v in obj.iteritems():
                    newDic[self.objects[k]] = self.objects[v]
                newTree.append(newDic)
            else:
                newTree.append(obj)
        
        # return root object
        return newTree[self.top_object]        
    
    @classmethod
    def plistWithString(cls, s):
        parser = cls(s)
        return parser.parse()

# helpers for testing
def plist(obj):
    from Foundation import NSPropertyListSerialization, NSPropertyListBinaryFormat_v1_0
    b = NSPropertyListSerialization.dataWithPropertyList_format_options_error_(obj,  NSPropertyListBinaryFormat_v1_0, 0, None)
    return str(b.bytes())

def unplist(s):
    from Foundation import NSData, NSPropertyListSerialization
    d = NSData.dataWithBytes_length_(s, len(s))
    return NSPropertyListSerialization.propertyListWithData_options_format_error_(d, 0, None, None)
