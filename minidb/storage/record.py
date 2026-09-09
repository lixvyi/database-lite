import struct
from ..errors import StorageError


class RecordCodec:
    """行编码：[字段数:u16][null bitmap][逐字段定长/长度前缀数据]。"""
    @staticmethod
    def encode(schema,row):
        cols=schema.columns;nulls=bytearray((len(cols)+7)//8);body=bytearray()
        for i,col in enumerate(cols):
            value=row.get(col.name)
            if value is None:nulls[i//8]|=1<<(i%8);continue
            if col.data_type=="INT":
                try:body+=struct.pack("<q",int(value))
                except (OverflowError,struct.error,ValueError) as exc:raise StorageError(f"value for column '{col.name}' is outside 64-bit INT range") from exc
            else:
                text=str(value)
                if col.length is not None and len(text)>col.length:raise StorageError(f"value for column '{col.name}' exceeds VARCHAR({col.length})")
                raw=text.encode("utf-8");body+=struct.pack("<I",len(raw))+raw
        return struct.pack("<H",len(cols))+nulls+body
    @staticmethod
    def decode(schema,data):
        count=struct.unpack_from("<H",data)[0];pos=2;nulls=data[pos:pos+(count+7)//8];pos+=(count+7)//8;row={}
        for i,col in enumerate(schema.columns):
            if nulls[i//8]&(1<<(i%8)):row[col.name]=None;continue
            if col.data_type=="INT":row[col.name]=struct.unpack_from("<q",data,pos)[0];pos+=8
            else:
                size=struct.unpack_from("<I",data,pos)[0];pos+=4;row[col.name]=data[pos:pos+size].decode("utf-8");pos+=size
        return row
