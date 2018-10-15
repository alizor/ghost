import os, sys, struct

tags = {
    b'\x0D\xFF': 'sound',  b'\x08\xFF': 'face',  b'\x19\xFF': 'change',
    b'\x1B\xFF': 'fchat',  b'\x24\xFF': 'NJ',
    }

tags2 = {
    b'\x2D\xFF': 'begin', b'\x02\xFF': 'press',  b'\x21\xFF': 'show',
    b'\xFF\xFF': 'end',   b'\x03\xFF': 'center', b'\x16\xFF': 'space',
    b'\x23\xFF': 'wait',  b'\x0F\xFF': 'blink', 
    b'\x16\x01': 'BACK',  b'\x17\x01': 'TRICK',  b'\x18\x01': 'GHOST',
    b'\x19\x01': 'TIME',  b'\x14\x01': 'DPAD',   b'\x1A\x01': 'MENU',
    b'\x1C\x01': 'MISSILE',  b'\x15\x01': 'JOWD', b'\x1D\x01': 'SISSEL',
    }

unknow = [
    '\x00\x01', '\x1D\xFF', '\x20\xFF', '\x15\xFF', '\x0C\xFF', '\x1C\xFF',
    '\x22\xFF', '\x1E\xFF', '\x2B\xFF',
    ]

def readTable(file):
    table_file = open(file, 'r')
    table = {}
    for line in table_file:
        line = line.strip('\n')
        if '=' in line:
            split = line.split('=')
            split[0] = struct.pack('>H', int(split[0], 16) )
            if len(split) == 3:
                table[split[0]] = '='
            else:
                table[split[0]] = split[1]
    return table

def invertTable(table):
    return dict([[i,j] for j,i in table.items()])

def extractMSG():
    dire = 'msg/'
    outdir = 'en/'
    
    try:
        table = readTable('ghost.tbl')
    except:
        print ('Table ghost.tbl not found!')
        sys.exit(1)
        
    table[b'\x01\xFF'] = '*\n'
    
    for name in os.listdir(dire):
        
        try: os.mkdir(outdir)
        except: pass
        
        file = open(dire + name, 'rb')
        output = open(outdir + name + '.txt', 'w')

        text_offset = []; pointer_offset = []; block_name = []
        
        file.read(8)
        text_block_size = struct.unpack('<L', file.read(4))[0]
        file.read(4)
        pointers_block_size = struct.unpack('<L', file.read(4))[0]
        file.read(32)
        file.seek(text_block_size, 1)
        file.read(4)
        file_num = struct.unpack('<L', file.read(4))[0]
        
        for i in range(file_num):
            pointer_offset.append(struct.unpack('<L', file.read(4))[0])
            text_offset.append(struct.unpack('<L', file.read(4))[0])
            
        file.read(2) # 2A 00
        x = file.tell()

        if file_num == 1:
            fname = file.read(pointers_block_size-12).decode("ASCII").strip('\x00')
            block_name.append(fname)
        else:
            for a in range(file_num - 1):
                file.seek(x + pointer_offset[a] - 2, 0)
                fname = file.read(pointer_offset[a+1]-pointer_offset[a]).decode("ASCII").strip('\x00')
                block_name.append(fname)
            fname = file.read(pointers_block_size-(file_num*8)-4-pointer_offset[a+1]).decode("ASCII").strip('\x00')
            block_name.append(fname)

        # text block
        file.seek(52, 0)

        for i in range(file_num):
            file.read(2)
            b1 = struct.unpack("<H", file.read(2))[0]
            b2 = struct.unpack("<H", file.read(2))[0]
            output.write('[%s][%02X%02X]\n\n' % (block_name[i], b1, b2 ))
            while True:
                byte = file.read(2)
                if byte in table:
                    output.write(table[byte])
                elif byte == b'\xFE\xFF':
                    output.write('\n\n-------------------------------\n\n')
                    break
                elif byte in tags:
                    output.write('<%s:%04X>' % (tags[byte], struct.unpack("<H", file.read(2))[0]) )
                    if tags[byte] != 'sound':
                        output.write('\n')
                elif byte in tags2:
                    output.write('<%s>' % tags2[byte])
                    if tags2[byte] in ['end', 'press', 'space']:
                        output.write('\n')
                elif byte in unknow:
                    output.write('<%04X_' % struct.unpack(">H", byte)[0] )
                    byte2 = file.read(2)
                    output.write('%04X>' % struct.unpack(">H", byte2)[0] )
                elif byte == b'\x05\xFF':
                    byte2 = file.read(2)
                    if   byte2 == b'\x06\x00': output.write('<red>')
                    elif byte2 == b'\x09\x00': output.write('<blue>')
                    elif byte2 == b'\x0C\x00': output.write('<green>')
                    elif byte2 == b'\x0F\x00': output.write('<black>')
                elif byte == b'\x10\xFF':
                    b1 = struct.unpack("<H", file.read(2))[0]
                    b2 = struct.unpack("<H", file.read(2))[0]
                    output.write('<shake:%02X%02X>' % (b1, b2) )
                else:
                    output.write('{%04X}' % struct.unpack(">H", byte)[0] )
        
        print (name)
        file.close()
        output.close()

def insertMSG():
    
    dire = 'txt/'
    outdir = 'br_msg/'
    table = readTable('ghost.tbl')
    table2 = invertTable(table)
    itags = invertTable(tags)
    itags2 = invertTable(tags2)
    
    table2['*'] = b'\x01\xFF'
    itags2['red'] = b'\x05\xFF\x06\x00'; itags2['blue'] = b'\x05\xFF\x09\x00'
    itags2['green'] = b'\x05\xFF\x0C\x00'; itags2['black'] = b'\x05\xFF\x0F\x00'
    
    for name in os.listdir(dire):
        
        try: os.mkdir(outdir)
        except: pass

        print (name)
        
        file = open(dire + name, 'r')
        output = open(outdir + name[:-4], 'wb')
        
        file_num = text_size = block_size = 0
        pointer1 = 2
        pointer2 = 52
        names = []; texts = []; ids = []
        txts = bytes()

        for line in file:
            line = line.strip()
            if line:
                if '-----------' in line:
                    file_num += 1
                    texts.append(txts)
                    txts = bytes()
                elif '[' and ']' in line:
                    split = line.split('][')
                    names.append(split[0][1:])
                    id1 = struct.pack('<H', int(split[1][:2], 16))
                    id2 = struct.pack('<H', int(split[1][2:4], 16))
                    ids.append((id1, id2))
                else:
                    x = 0
                    while x < len(line):
                        if line[x] == '<':
                            y = x
                            while True:
                                if line[y] != '>':
                                    y += 1
                                else:
                                    break
                            if line[x+1:y] in itags2:
                                txts += itags2[line[x+1:y]]
                            else:
                                if '_' in line[x+1:y]:
                                    tag = line[x+1:y].split('_')
                                    a1 = struct.pack('<H', int(tag[1], 16))
                                    a2 = struct.pack('<H', int(tag[2], 16))
                                    txts += a1 + a2
                                else:
                                    tag = line[x+1:y].split(':')
                                    if tag[0] in itags:
                                        a1 = struct.pack('<H', int(tag[1], 16))
                                        txts += itags[tag[0]] + a1
                                    else:
                                        a1 = struct.pack('<H', int(tag[1][:2], 16))
                                        a2 = struct.pack('<H', int(tag[1][2:], 16))
                                        txts += b'\x10\xFF' + a1 + a2
                            x = y + 1
                        elif line[x] == '{':
                            z = x
                            while True:
                                if line[z] != '}':
                                    z += 1
                                else:
                                    break
                            txts += struct.pack(">H", int(line[x+1:z], 16))
                            x = z + 1
                        else:
                            txts += table2[line[x]]
                            x += 1

        output.write(b'1LMG' + b'\x00' * 8 + b'\x04' + b'\x00' * 3 + b'\x00' * 4 + b'\x00' * 32)

        for i in range(file_num):
            output.write(b'\x2D\xFF' + ids[i][0] + ids[i][1] + texts[i] + b'\xFE\xFF')
            text_size += 8 + len(texts[i])

        if (4 - text_size%4) != 4:
            output.write(b'\x00' * (4 - text_size % 4))
            text_size += 4 - text_size%4

        output.write(b'\x2A\x00\x00\x00' + struct.pack('<L', file_num))

        for x in range(file_num):
            output.write(struct.pack('<L', pointer1))
            pointer1 += len(names[x]) + 1
            output.write(struct.pack('<L', pointer2))
            pointer2 += len(texts[x]) + 8

        pname = pointer1-len(names[x]) - 1
            
        block = 4 + file_num * 8 + pname + len(names[x])
        dx = 4 - block%4
        if dx == 0: dx = 4
        block_size = block + dx

        output.write(b'\x2A\x00')

        for a in range(len(names)):
            output.write(names[a].encode() + b'\x00')
            
        output.write(b'\x00' * (dx - 1))

        output.seek(8, 0)
        output.write(struct.pack('<L', text_size))
        output.seek(16, 0)
        output.write(struct.pack('<L', block_size))

        file.close()
        output.close()
        #os.system('dsdecmp -c lz11 %s' % outdir + name[:-4])

        
if __name__ == '__main__':
    print ("GHOST TRICK dumper/inserter \nby alizor\n")
    print ("\t1 = extract\n\t2 = insert\n\t3 = exit\n")
    choice = input(">>> ")
    if int(choice) == 1:
        extractMSG()
    elif int(choice) == 2:
        insertMSG()
    else:
        sys.exit(1)
    sys.exit(1)
