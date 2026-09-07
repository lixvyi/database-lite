from dataclasses import dataclass,field
from .errors import PermissionDenied


@dataclass
class Policy:
    user:str;table:str;actions:set[str];columns:set[str]|None=None;row_filter:object=None


class Authorizer:
    """表/列/行/业务动作四层授权；row_filter 接收一行并返回 bool。"""
    def __init__(self):self.policies=[]
    def grant(self,user,table,actions,columns=None,row_filter=None):self.policies.append(Policy(user,table.lower(),set(actions),set(columns) if columns else None,row_filter))
    def policy(self,user,table,action):
        matches=[p for p in self.policies if p.user==user and p.table==table.lower() and action in p.actions]
        if not matches:raise PermissionDenied(f"user '{user}' cannot {action} table '{table}'")
        return matches[0]
    def check_columns(self,p,columns):
        if p.columns is not None and not set(columns)<=p.columns:raise PermissionDenied("one or more columns are not authorized")
    def allow_row(self,p,row):return p.row_filter is None or bool(p.row_filter(row))
