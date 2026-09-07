import argparse,json
from minidb import Database
from minidb.errors import MiniDBError


def main():
    ap=argparse.ArgumentParser(description="拾页 MiniDB 教学数据库")
    ap.add_argument("--data",default="minidb_data");ap.add_argument("--sql");ap.add_argument("--inspect",action="store_true")
    args=ap.parse_args();db=Database(args.data)
    def run(sql):
        try:
            result=db.inspect(sql) if args.inspect else db.execute(sql);print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
        except MiniDBError as e:print(e)
    if args.sql:return run(args.sql)
    print("拾页 MiniDB（输入 .quit 退出，语句以分号结束）");buf=""
    while True:
        line=input("minidb> " if not buf else "    ... ")
        if line.strip()==".quit":break
        buf+=line+"\n"
        if ";" in line:run(buf);buf=""

if __name__=="__main__":main()
