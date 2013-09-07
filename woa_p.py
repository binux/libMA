"""
decompile from com/snda/woa/p
"""

getBytes = lambda s:map(lambda x:ord(x),s)

class P(object):

    key = ""
    c=[58,50,42,34,26,18,10,2,60,52,44,36,28,20,12,4,62,54,46,38,30,22,14,6,64,56,48,40,32,24,16,8,57,49,41,33,25,17,9,1,59,51,43,35,27,19,11,3,61,53,45,37,29,21,13,5,63,55,47,39,31,23,15,7]
    d=[40,8,48,16,56,24,64,32,39,7,47,15,55,23,63,31,38,6,46,14,54,22,62,30,37,5,45,13,53,21,61,29,36,4,44,12,52,20,60,28,35,3,43,11,51,19,59,27,34,2,42,10,50,18,58,26,33,1,41,9,49,17,57,25]
    e=[57,49,41,33,25,17,9,1,58,50,42,34,26,18,10,2,59,51,43,35,27,19,11,3,60,52,44,36,63,55,47,39,31,23,15,7,62,54,46,38,30,22,14,6,61,53,45,37,29,21,13,5,28,20,12,4]
    f=[14,17,11,24,1,5,3,28,15,6,21,10,23,19,12,4,26,8,16,7,27,20,13,2,41,52,31,37,47,55,30,40,51,45,33,48,44,49,39,56,34,53,46,42,50,36,29,32]
    g=[32,1,2,3,4,5,4,5,6,7,8,9,8,9,10,11,12,13,12,13,14,15,16,17,16,17,18,19,20,21,20,21,22,23,24,25,24,25,26,27,28,29,28,29,30,31,32,1]
    h=[16,7,20,21,29,12,28,17,1,15,23,26,5,18,31,10,2,8,24,14,32,27,3,9,19,13,30,6,22,11,4,25];
    j=[1,1,2,2,2,2,2,2,1,2,2,2,2,2,2,1]
    i = [[[14,4,13,1,2,15,11,8,3,10,6,12,5,9,0,7],[0,15,7,4,14,2,13,1,10,6,12,11,9,5,3,8],
        [4,1,14,8,13,6,2,11,15,12,9,7,3,10,5,0],[15,12,8,2,4,9,1,7,5,11,3,14,10,0,6,13]],

        [[15,1,8,14,6,11,3,4,9,7,2,13,12,0,5,10],[3,13,4,7,15,2,8,14,12,0,1,10,6,9,11,5],
        [0,14,7,11,10,4,13,1,5,8,12,6,9,3,2,15],[13,8,10,1,3,15,4,2,11,6,7,12,0,5,14,9]],

        [[10,0,9,14,6,3,15,5,1,13,12,7,11,4,2,8],[13,7,0,9,3,4,6,10,2,8,5,14,12,11,15,1],
        [13,6,4,9,8,15,3,0,11,1,2,12,5,10,14,7],[1,10,13,0,6,9,8,7,4,15,14,3,11,5,2,12]],

        [[7,13,14,3,0,6,9,10,1,2,8,5,11,12,4,15],[13,8,11,5,6,15,0,3,4,7,2,12,1,10,14,9],
        [10,6,9,0,12,11,7,13,15,1,3,14,5,2,8,4],[3,15,0,6,10,1,13,8,9,4,5,11,12,7,2,14]],

        [[2,12,4,1,7,10,11,6,8,5,3,15,13,0,14,9],[14,11,2,12,4,7,13,1,5,0,15,10,3,9,8,6],
        [4,2,1,11,10,13,7,8,15,9,12,5,6,3,0,14],[11,8,12,7,1,14,2,13,6,15,0,9,10,4,5,3]],

        [[12,1,10,15,9,2,6,8,0,13,3,4,14,7,5,11],[10,15,4,2,7,12,9,5,6,1,13,14,0,11,3,8],
        [9,14,15,5,2,8,12,3,7,0,4,10,1,13,11,6],[4,3,2,12,9,5,15,10,11,14,1,7,6,0,8,13]],

        [[4,11,2,14,15,0,8,13,3,12,9,7,5,10,6,1],[13,0,11,7,4,9,1,10,14,3,5,12,2,15,8,6],
        [1,4,11,13,12,3,7,14,10,15,6,8,0,5,9,2],[6,11,13,8,1,4,10,7,9,5,0,15,14,2,3,12]],

        [[13,2,8,4,6,15,11,1,10,9,3,14,5,0,12,7],[1,15,13,8,10,3,7,4,12,5,6,11,0,14,9,2],
        [7,11,4,1,9,12,14,2,0,6,10,13,15,3,5,8],[2,1,14,7,4,10,8,13,15,12,9,0,3,5,6,11]]]

    def __init__(self, key):
        self.key = key

    def b_BBi_B(self, paramArrayOfByte1, paramArrayOfByte2, paramInt):
        arrayOfByte1 = self.c_B_B(paramArrayOfByte1)
        arrayOfByte2 = self.c_B_B(paramArrayOfByte2)
        k = len(arrayOfByte2)
        m = k/8
        arrayOfByte3 = [0 for i in range(k)]
        arrayOfByte4 = [0 for i in range(8)]
        arrayOfByte5 = [0 for i in range(8)]
        for n in range(m):
            if paramInt <=1:
                self.a_BiBii_V(arrayOfByte1, 0,arrayOfByte4, 0, 8)
            else:
                self.a_BiBii_V(arrayOfByte1, n*8,arrayOfByte4, 0, 8)
            self.a_BiBii_V(arrayOfByte2, n*8, arrayOfByte5, 0, 8)
            tmp = self.a_BBi_B(arrayOfByte4, arrayOfByte5, paramInt)
            self.a_BiBii_V(tmp, 0, arrayOfByte3,n*8, 8)
        return arrayOfByte3

    def c_B_B(self, paramArrayOfByte):
        k = len(paramArrayOfByte)
        m = k + (8-k%8)
        arrayOfByte = [0 for i in range(m)]
        self.a_BiBii_V(paramArrayOfByte, 0, arrayOfByte, 0, k)
        return arrayOfByte

    def a_BiBii_V(self, paramArrayOfByte1, paramInt1, paramArrayOfByte2,
                  paramInt2,paramInt3):
        if paramArrayOfByte2 and paramArrayOfByte1:
            arrayOfByte = [0 for i in range(paramInt3)]
            for m in range(paramInt3):
                arrayOfByte[m] = paramArrayOfByte1[paramInt1 + m]
            for k in range(paramInt3):
                paramArrayOfByte2[paramInt2 + k] = arrayOfByte[k]

    def a_BBi_B(self, paramArrayOfByte1, paramArrayOfByte2, paramInt):
        if len(paramArrayOfByte1)!=8 or len(paramArrayOfByte2)!=8:
            raise
        if paramInt > 1:
            paramInt -= 2
        arrayOfInt = [[0 for j in range(48)] for i in range(16)]
        arrayOfInt2 = self.b_B_I(paramArrayOfByte1)
        arrayOfInt3 = self.b_B_I(paramArrayOfByte2)
        self.a_II_V(arrayOfInt2, arrayOfInt)
        rtn = self.a_IiI_B(arrayOfInt3, paramInt, arrayOfInt)
        return rtn

    def a_II_V(self, paramArrayOfInt, paramArrayOfInt1):
        arrayOfInt = [0 for i in range(56)]
        for k in range(56):
            arrayOfInt[k] = paramArrayOfInt[self.e[k] - 1]
        for m in range(16):
            self.a_Ii_V(arrayOfInt, self.j[m])
            for n in range(48):
                paramArrayOfInt1[m][n] = arrayOfInt[self.f[n] - 1]

    def a_IiiI_V(self,paramArrayOfInt, paramInt1, paramInt2, paramArrayOfInt1):
        arrayOfInt1 = [0 for i in range(32)]
        arrayOfInt2 = [0 for i in range(32)]
        arrayOfInt3 = [0 for i in range(32)]
        arrayOfInt4 = [0 for i in range(32)]
        arrayOfInt5 = [0 for i in range(48)]
        arrayOfInt = [[0 for j in range(6)] for i in range(9)]
        arrayOfInt7 = [0 for i in range(8)]
        arrayOfInt8 = [0 for i in range(32)]
        arrayOfInt9 = [0 for i in range(32)]
        for k in range(32):
            arrayOfInt1[k] = paramArrayOfInt[k]
            arrayOfInt2[k] = paramArrayOfInt[k + 32]
        for m in range(48):
            arrayOfInt5[m] = arrayOfInt2[self.g[m] -1]
            arrayOfInt5[m] += paramArrayOfInt1[paramInt1][m]
            if (arrayOfInt5[m] == 2):
                arrayOfInt5[m] = 0
        for n in range(8):
            for i2 in range(6):
                arrayOfInt[n][i2] = arrayOfInt5[i2 + n *6]
            arrayOfInt7[n] = self.i[n][((arrayOfInt[n][0] << 1) + arrayOfInt[n][5])][((arrayOfInt[n][1] << 3) + (arrayOfInt[n][2] << 2) + (arrayOfInt[n][3] << 1) + arrayOfInt[n][4])];
            for i3 in range(4):
                arrayOfInt8[3 + n * 4 - i3] = arrayOfInt7[n] % 2
                arrayOfInt7[n] /= 2
        for i1 in range(32):
            arrayOfInt9[i1] = arrayOfInt8[self.h[i1] - 1]
            arrayOfInt3[i1] = arrayOfInt2[i1]
            arrayOfInt4[i1] = arrayOfInt1[i1] + arrayOfInt9[i1]
            if arrayOfInt4[i1] == 2:
                arrayOfInt4[i1] = 0
            if (paramInt2 == 0 and paramInt1 == 0) or (paramInt2 == 1 and paramInt1 == 15):
                paramArrayOfInt[i1] = arrayOfInt4[i1]
                paramArrayOfInt[i1 + 32] = arrayOfInt3[i1]
            else:
                paramArrayOfInt[i1] = arrayOfInt3[i1]
                paramArrayOfInt[i1 + 32] = arrayOfInt4[i1]

    def a_IiI_B(self, paramArrayOfInt, paramInt, paramArrayOfInt1):
        arrayOfByte = [0 for i in range(8)]
        arrayOfInt1 = [0 for i in range(64)]
        arrayOfInt2 = [0 for i in range(64)]
        for m in range(64):
            arrayOfInt1[m] = paramArrayOfInt[self.c[m] -1]
        if (paramInt == 1):
            for i1 in range(16):
                self.a_IiiI_V(arrayOfInt1, i1, paramInt, paramArrayOfInt1)
        if paramInt == 0:
            for n in range(15,-1,-1):
                self.a_IiiI_V(arrayOfInt1, n, paramInt, paramArrayOfInt1)
        for k in range(64):
            arrayOfInt2[k] = arrayOfInt1[self.d[k] - 1]
        self.a_IB_V(arrayOfInt2, arrayOfByte)
        return arrayOfByte

    def a_Ii_V(self, paramArrayOfInt, paramInt):
        arrayOfInt1 = [0 for i in range(28)]
        arrayOfInt2 = [0 for i in range(28)]
        arrayOfInt3 = [0 for i in range(28)]
        arrayOfInt4 = [0 for i in range(28)]
        for m in range(28):
            arrayOfInt1[m] = paramArrayOfInt[m]
            arrayOfInt2[m] = paramArrayOfInt[m + 28]
        if paramInt == 1:
            for i1 in range(27):
                arrayOfInt3[i1] = arrayOfInt1[i1 + 1]
                arrayOfInt4[i1] = arrayOfInt2[i1 + 1]
            arrayOfInt3[27] = arrayOfInt1[0]
            arrayOfInt4[27] = arrayOfInt2[0]
        elif paramInt == 2:
            for n in range(26):
                arrayOfInt3[n] = arrayOfInt1[n + 2]
                arrayOfInt4[n] = arrayOfInt2[n + 2]
            arrayOfInt3[26] = arrayOfInt1[0]
            arrayOfInt4[26] = arrayOfInt2[0]
            arrayOfInt3[27] = arrayOfInt1[1]
            arrayOfInt4[27] = arrayOfInt2[1]
        for k in range(28):
            paramArrayOfInt[k] = arrayOfInt3[k]
            paramArrayOfInt[k + 28] = arrayOfInt4[k]

    def a_IB_V(self,paramArrayOfInt, paramArrayOfByte):
        for m in range(8):
            for n in range(8):
                paramArrayOfByte[m] += paramArrayOfInt[n + (m << 3)] << 7 - n
        for k in range(8):
            paramArrayOfByte[k] = paramArrayOfByte[k] % 256
            if paramArrayOfByte[k] > 128:
                paramArrayOfByte[k] = paramArrayOfByte[k] - 255

    def b_B_I(self, paramArrayOfByte):
        arrayOfInt1 = [0 for i in range(8)]
        for k in range(8):
            arrayOfInt1[k] = paramArrayOfByte[k]
            if arrayOfInt1[k] < 0:
                arrayOfInt1[k] = 256 + arrayOfInt1[k]
                arrayOfInt1[k] %= 256
        arrayOfInt2 = [0 for i in range(64)]
        for m in range(8):
            for n in range(8):
                arrayOfInt2[7 + m * 8 - n] = arrayOfInt1[m] % 2
                arrayOfInt1[m] /= 2
        return arrayOfInt2

    def byteToString(self, paramOfByte):
        return "".join(map(lambda x:"%02x"%(x if x>0 else 255 + x),paramOfByte))

    def encode(self, string, paramInt = 0):
        str1 = str(len(string))
        str1 = ["","000","00","0"][len(str1)] + str1
        str2 = str1 + string
        return self.byteToString(self.b_BBi_B(getBytes(self.key),getBytes(str2), paramInt + 1))
        
if __name__ == "__main__":
    key = "w!o2a#r4e%g6i&n8(0)^_-==991000282"
    p = P(key)
    s = p.encode("13800138000",0)#it should be "2736189fe85a1a4c4ee69d08e384fbb7"
    if s == "2736189fe85a1a4c4ee69d08e384fbb7":
        print "It Works!"
